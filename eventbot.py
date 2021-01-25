import discord
from discord import Attachment
from discord import Embed
from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime
import os

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(os.getenv('TOKEN'))