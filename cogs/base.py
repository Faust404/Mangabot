from tinydb import TinyDB, Query
from bs4 import BeautifulSoup
from discord.ext import tasks, commands
from discord import app_commands

import re
import requests
import discord


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 0

        self.db = TinyDB("mangadata.json", indent=4, separators=(",", ": "))
        self.query = Query()
        self.mangadb = self.db.table("Manga", cache_size=30)

        self.elements = {
            "Asura" : {"class": "eplister", "tag": "div"},
            "Luminous" : {"class": "eplister", "tag": "div"},
            "Manganelo" : {"class": "panel-story-chapter-list", "tag": "div"}
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot Online")
        await self.bot.tree.sync()
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(error, ephemeral=True)
        else:
            raise error
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def start(self, ctx):
        self.channel_id = ctx.channel.id
        self.check_new_chapters.start()
        await ctx.send("The Bot is Online Now")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stop(self, ctx):
        self.check_new_chapters.cancel()
        await ctx.send("The Bot is Offline Now")

    @app_commands.command()
    async def search(self, interaction: discord.Interaction, name: str):
        data = requests.get('https://manganelo.com/search/story/'+self.format_for_url(name)).text
        search_results = BeautifulSoup(data, features='html.parser').find('div', class_="panel-search-story")
        mangas = []
        result_embed = discord.Embed(title="Search Results")
        if not (search_results == None):
            search_results = search_results.find_all('div', class_='search-story-item')
            for manga in search_results:
                title = manga.find('a', class_="a-h text-nowrap item-title")['title'].strip()
                link = manga.find('a', class_="a-h text-nowrap item-title")['href'].strip()
                # icon_url = manga.find("img", class_="img-loading").get("src")
                updated = manga.find_all('span', class_="text-nowrap item-time")[0].text.replace('Updated :', '').strip()

                # mangas.append({'title': title, 'link': link, 'last-updated': updated, 'thumbnail': icon_url})
                mangas.append({'title': title, 'link': link, 'last-updated': updated})

            if len(mangas) > 1:
                for manga in mangas:
                    # result_embed.set_image(url=manga['thumbnail'])
                    result_embed.add_field(name=manga['title'],
                                             value=manga['link'], inline=False)
                await interaction.response.send_message(embed=result_embed, ephemeral=True)
            else:
                await interaction.response.send_message(mangas[0]['link'], ephemeral=True)

    @tasks.loop(minutes=30)
    async def check_new_chapters(self):
        for entry in self.mangadb.all():
            manga = entry['name'] 
            await self.fetch(manga)

    def format_for_url(self, s):
        return '_'.join(''.join(map(lambda x: x if x.isalnum() else ' ', s)).split())

    def extract_chapter_num(self, string):
        match = re.search(r'\d+(\.\d+)?', string)
        if match:
            return float(match.group())
        else:
            return None

    def get_ping_role(self, channel, manga):
        roles = channel.guild.roles
        role_names = []
        for role in roles:
            role_names.append(role.name)
        
        gen = (role for role in role_names if (manga.lower() in role.lower()))
        return next(gen)

    async def role_ping(self, channel, manga):
        try: 
            role_to_ping = self.get_ping_role(channel, manga)
        except:
            pass
        else:
            role = discord.utils.get(channel.guild.roles, name=role_to_ping)
            await channel.send(role.mention)

    async def fetch(self, manga):
        channel = self.bot.get_channel(self.channel_id)
        try:
            result = self.mangadb.search(self.query.name == manga)[0]
        except:
            pass
        else:
            source = result["source"]
            cl = self.elements[source]["class"]
            tag = self.elements[source]["tag"]
            chapcount = result["chapcount"]
            url = result["url"]

            data = requests.get(url).text
            soup = BeautifulSoup(data, "html.parser")

            # Getting all the chapters from the webpage
            chap_list = soup.findAll(tag, attrs={"class": cl})

            try:
                chap_list = chap_list[0].findAll("li")
            except IndexError:
                print("Index Error")
            else:
                # Getting information of the latest available chapter
                href_data = chap_list[0].find_all("a", href=True)

                # Getting the number of the latest available chapter
                latest_chapter = re.findall(">Chapter.*<", str(href_data))[0]
                latest_chapter = latest_chapter.lstrip(">").rstrip("<")
                latest_chapter_num = self.extract_chapter_num(latest_chapter)

                # Send message to channel if latest chapter is newer than existing chapter in database
                if latest_chapter_num > chapcount:
                    await self.role_ping(channel, manga)
                    self.mangadb.update({'chapcount': latest_chapter_num}, self.query.name == manga)
                    for item in href_data:
                        await channel.send(item["href"])


async def setup(bot):
    await bot.add_cog(Base(bot))
