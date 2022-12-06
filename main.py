import asyncio
import os
import discord
from discord.ext import commands
from dotenv.main import load_dotenv

intents = discord.Intents.all()
intents.members = True

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot = commands.Bot(command_prefix=",", intents=intents)

async def is_allowed(ctx):
    return (ctx.author.id == 827799188950876201
        or ctx.author.id == 223117142290202625)

async def main():

    for f in os.listdir("./cogs"):
        if f.endswith(".py"):
            await bot.load_extension("cogs." + f[:-3])

    @bot.command()
    @commands.check(is_allowed)
    async def load(ctx, extension: str):
        await bot.load_extension(f"cogs.{extension.lower()}")
        print(f"{extension.title()} Cog Succesfully Loaded")
    
    @bot.command()
    @commands.check(is_allowed)
    async def unload(ctx, extension: str):
        await bot.unload_extension(f"cogs.{extension.lower()}")
        print(f"{extension.title()} Cog Succesfully Unloaded")
    
    @bot.command()
    @commands.check(is_allowed)
    async def reload(ctx, extension: str):
        await bot.reload_extension(f"cogs.{extension.lower()}")
        print(f"{extension.title()} Cog Succesfully Reloaded")
    
    await bot.start(BOT_TOKEN)

asyncio.run(main())
