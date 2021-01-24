import discord
from discord import Attachment
from discord import Embed
from discord.ext import commands
from datetime import datetime
import os

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')
@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))

@bot.command(aliases=['help', 'eventbot'])
async def commands(ctx):
    #attachment = Attachment('./help.jpg', 'help.jpg')
    embed = discord.Embed(color=0x32A852, title='Commands', description='This is a list of all the commands and how to use them')
    #embed.set_author(name='Event Bot', icon_url='https://image.flaticon.com/icons/png/512/1458/1458512.png')
    embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
    embed.set_thumbnail(url='https://i.imgur.com/qn182DB.jpg')
    embed.add_field(name=".poll", value="create a poll for availability", inline=False) \
    .add_field(name=".notify message", value="notify this channel with message", inline=False) \
    .add_field(name=".schedule event_name event_day", value="schedules event notification at event_day\nevent_day format (year is assumed to be current year): Month/Day\nexample: 1/23", inline=False) \
    .add_field(name=".availability event_id", value="output people available for this event", inline=False) \
    .add_field(name=".availability weekday", value="output people available for this time\nweekday format: Monday or 1, Tuesday or 2, etc.", inline=False) \
    .add_field(name=".repo", value="output link to github repo. helpful links and resources are displayed in the README.md") \
    .set_footer(text=datetime.now().strftime('%-m/%-d/%Y %-I:%-M %p'))
    #.add_field(name=".schedule event_name event_start event_end", value="schedules event notification at event_time and outputs event id\ntime format: MM-DD HH:MM AM/PM to schedule current year\nexample: 01-23 11:00 PM", inline=False) \
    #.add_field(name=".availability time_start time_end", value="output people available for this time\nformat: MM-DD HH:MM AM/PM to MM-DD HH:MM AM/PM\nexample: 01-23 04:30 PM to 01-23 05:00 PM\nyear format: YYYY-MM-DD HH:MM AM/PM to YYYY-MM-DD Hour:MM AM/PM to schedule specific year", inline=False) \
    #embed = Embed().setColor('#0099ff').setTitle('Some title').setURL('https://discord.js.org/').setAuthor('Some name', 'https://i.imgur.com/wSTFkRM.png', 'https://discord.js.org').setDescription('Some description here').setThumbnail('https://i.imgur.com/wSTFkRM.png')
    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx):
    embed = discord.Embed(color=0x32A852, title='Poll Weekly Availability anytime between 6-10PM', description="If you are available at least 30 mins between 6-10PM, please react")
    embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
    embed.set_thumbnail(url='https://image.flaticon.com/icons/png/512/1458/1458512.png')
  #embed.add_field(name="React to this if available anytime between 6-10PM", value="If you are available at least 30 mins between 6-10PM, please react", inline=False)
    embed.add_field(name="React with number emojis", value="1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣ corresponds to Monday, Tuesday, etc.")
    embed.set_footer(text=datetime.now().strftime('%-m/%-d/%Y %-I:%-M %p'))
    await ctx.send(embed=embed)
    #NOTE: cache is cleared after every restart, so usee raw_on_reaction_add

#with open('token.json', 'r') as f:
    #bot.run(json.load(f)['TOKEN'])
bot.run(os.getenv('TOKEN'))
    #token can be utilized to ban people, do malicious things, etc.
    #the python file controls what you do

"""
    output = " \
    Here are the menu options:\n \
    .poll                                           # create a poll for availability (Please run only once)\n \
    .notify event_name                              # create notification for event in this channel and tag @channel\n \
    .schedule event_name event_time    # schedules notification for an event at event_time\n \
                                                    # time format: MM-DD HH:MM AM/PM to schedule current year\n \
                                                    # example:     01-23 11:00 PM\n \
    .availability  time_start time_end              # check availability for this channel\n \
                                                    # format:       MM-DD HH:MM AM/PM to MM-DD HH:MM AM/PM\n \
                                                    # example:      01-23 04:30 PM to 01-23 05:00 PM\n \
                                                    # year format:  YYYY-MM-DD HH:MM AM/PM to YYYY-MM-DD Hour:MM AM/PM to schedule specific year\n \
                                                    # example: 2021-01-23\n \
    "
"""