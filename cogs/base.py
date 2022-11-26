from tinydb import TinyDB, Query
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from discord.ext import tasks, commands
from discord import app_commands

import re
import requests
import discord

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 0

        self.db = TinyDB("mangadata.json", indent=4, separators=(",", ": "))
        self.query = Query()
        self.mangadb = self.db.table("Manga", cache_size=30)

        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), chrome_options=chrome_options
        )

        self.elements = {
            "Asura" : {"class": "eplister", "tag": "div"},
            "Luminous" : {"class": "eplister", "tag": "div"},
            "Manganelo" : {"class": "panel-story-chapter-list", "tag": "div"}
        }

    async def is_allowed(ctx):
        return (ctx.author.id == 827799188950876201
            or ctx.author.id == 223117142290202625)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot Online")
        await self.bot.tree.sync()
    
    @app_commands.command()
    @commands.check(is_allowed)
    async def start(self, ctx):
        self.channel_id = ctx.channel.id
        self.check_new_chapters.start()
    
    @app_commands.command()
    @commands.check(is_allowed)
    async def stop(self, ctx):
        self.check_new_chapters.cancel()

    @app_commands.command()
    async def search(self, interaction: discord.Interaction, name: str):
        role = discord.utils.get(interaction.guild.roles, name = 'test')
        data = requests.get('https://manganelo.com/search/story/'+self.format_for_url(name)).text
        search_results = BeautifulSoup(data, features='lxml').find('div', class_="panel-search-story")
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

            self.driver.get(url)
            soup = BeautifulSoup(self.driver.page_source, "lxml")

            # Getting all the chapters from the webpage
            chap_list = soup.findAll(tag, attrs={"class": cl})
            chap_list = chap_list[0].findAll("li")

            # Getting information of the latest available chapter
            href_data = chap_list[0].find_all("a", href=True)

            # Getting the number of the latest available chapter
            latest_chapter = re.findall(">Chapter.*<", str(href_data))[0]
            latest_chapter = latest_chapter.lstrip(">").rstrip("<")
            latest_chapter_num = float(latest_chapter.split()[1])

            # Send message to channel if latest chapter is newer than existing chapter in database
            if latest_chapter_num > chapcount:
                self.mangadb.update({'chapcount': latest_chapter_num}, self.query.name == manga)
                for item in href_data:
                    await channel.send(item["href"])


async def setup(bot):
    await bot.add_cog(Base(bot))
