import discord
from discord import Attachment
from discord import Embed
from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime
import os
import importlib

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')

"""
def load_extension(name, bot, sharedobj):
    lib = importlib.import_module(name)
    lib.setup(bot, sharedobj)
    bot.extensions[name] = lib
"""

env_variables = (os.environ['DATABASE_URL'], os.environ['DATABASE_POLL_TABLE'], os.environ['DATABASE_POLL_MESSAGE_ID_TABLE'])

#load_extension('listener', bot, env_variables)

"""
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
"""
@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(self.bot))

@bot.command()
async def notify(self, ctx, *args):
    if len(args) == 0:
        await ctx.send("[Usage]: .notify <event_name>\n[Error message]: please provide event name")
    else:
        await ctx.send("Notifying " + "@everyone" + " that \"" + ' '.join(args) + "\" is happening now!")

def getenv_variables():
    return env_variables

bot.run(os.getenv('TOKEN'))