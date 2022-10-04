from bs4 import BeautifulSoup
from selenium import webdriver

import os
import json
import discord
import re

from discord.ext import commands

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True

bot_token = 'ODM1NTc3NTA1MTc5MjM4NDIw.GoDutk.89Lr5UEhBW_4g_czSscy6dQKTl-G2BWxpNC260'
channel_id = 820716614869712947
user_id = '223117142290202625'
bot = commands.Bot(command_prefix="!", intents=intents)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

with open('mangadata.json') as json_file:
    json_data = json.load(json_file)

@bot.event
async def on_ready():

    for entry in json_data:
        await fetch_link(entry)

    with open('mangadata.json', 'w') as outfile:
        json.dump(json_data, outfile, sort_keys=True, indent=4)

    driver.quit()


async def fetch_link(name):
    channel = await bot.fetch_user(int(user_id))
    # channel = await bot.fetch_channel(channel_id)

    details = json_data[name]
    url = details['url']
    tag = details['tag']
    cl = details['class']
    chapcount = details['chapcount']

    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")

    # Getting all the chapters from the webpage
    chap_list = soup.findAll(tag, attrs={'class' : cl})
    chap_list = chap_list[0].findAll('li')

    # Getting information of the latest available chapter
    href_data = chap_list[0].find_all('a', href=True)

    # Getting the number of the latest available chapter
    latest_chapter = re.findall('>Chapter.*<', str(href_data))[0]
    latest_chapter = latest_chapter.lstrip('>').rstrip('<')
    latest_chapter_num = int(latest_chapter.split()[-1])

    # DM user if latest chapter is newer than existing chapter in database
    if latest_chapter_num > chapcount:
        json_data[name]['chapcount'] = latest_chapter_num
        for item in href_data:
            await channel.send(item['href'])
    else:
        await channel.send('No new chaps for ' + name)

bot.run(bot_token)