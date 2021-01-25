import discord
from discord import Attachment
from discord import Embed
from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime
import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

table = os.environ['DATABASE_POLL_TABLE']

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
    #check if poll exists. we should have only one
    if os.environ.get('POLLOBJECTID') is not None:
        await ctx.send("poll already exists! please edit that one and don't delete it")
    else:
        embed = discord.Embed(color=0x32A852, title='Poll Weekly Availability anytime between 6-10PM', description="If you are available at least 30 mins between 6-10PM, please react")
        embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
        embed.set_thumbnail(url='https://image.flaticon.com/icons/png/512/1458/1458512.png')
        #embed.add_field(name="React to this if available anytime between 6-10PM", value="If you are available at least 30 mins between 6-10PM, please react", inline=False)
        embed.add_field(name="React with number emojis", value="1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣ corresponds to Monday, Tuesday, etc. and ❌ if not available for anything")
        current_time = datetime.now().strftime('%-m/%-d/%Y %-I:%-M %p')
        embed.set_footer(text=current_time)
        message = await ctx.send(embed=embed)
        os.environ['POLLOBJECTID'] = str(message.id)
        os.environ['POLLCHANNELID'] = str(message.channel.id)
        embed.add_field(name= "Message ID", value=str(message.id), inline=False)
        await message.edit(embed=embed) #add message ID for reference
        await message.pin() #pins message
        #NOTE: cache is cleared after every restart, so use raw_on_reaction_add

@Cog.listener()
async def on_raw_reaction_add(payload):
    #sql implementation
    args = ["FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE"]
    column_index = -1
    column = ""
    if str(payload.message_id) == os.environ['POLLOBJECTID'] and str(payload.channel_id) == os.environ['POLLCHANNELID']: #message_id but may also need channel_id
        if payload.emoji == "1️⃣":
            column_index = 0
            column = "monday"
        elif payload.emoji == "2️⃣":
            column_index = 1
            column = "tuesday"
        elif payload.emoji == "3️⃣":
            column_index = 2
            column = "wednesday"
        elif payload.emoji == "4️⃣":
            column_index = 3
            column = "thursday"
        elif payload.emoji == "5️⃣":
            column_index = 4
            column = "friday"
        elif payload.emoji == "6️⃣":
            column_index = 5
            column = "saturday"
        elif payload.emoji == "7️⃣":
            column_index = 6
            column = "sunday"
        elif payload.emoji == "❌":
            column_index = 7
        if column_index != -1:
            if column_index == 7: #delete
                curs.execute(computesql(table, "delete", payload.user_id, bot.fetch_user(payload.user_id).name, "", "", ""))
            else:
                curs.execute(computesql(table, "update", payload.user_id, bot.fetch_user(payload.user_id).name, column, column_index, args))
                print('executed')

def computesql(table, action, user_id, username, column, column_index, args):
    SQL = ''
    args[column_index] = "TRUE"
    if action == "update":
        SQL = "INSERT INTO {table} (user_id, username, monday, tuesday, wednesday, thursday, friday, saturday, sunday) VALUES ({user_id}, {username}, {args[0]}, {args[1]}, {args[2]}, {args[3]}, {args[4]}, {args[5]}, {args[6]} \
            ON CONFLICT (user_id) DO UPDATE SET {column} = TRUE;".format(table=table, user_id=user_id, username=username, column=column, args=args)
        #SQL = "UPDATE {table} SET {column} = TRUE WHERE user_id = {user_id}".format(table=table, user_id=user_id, column=column)
    elif action == "delete":
        SQL = "DELETE FROM {table} WHERE user_id = {user.id};".format(table=table, user_id=user_id)
    elif action == "check_user": #
        SQL = "SELECT CASE WHEN monday | tuesday | wednesday | thursday | friday | saturday | sunday = 0 THEN FALSE ELSE TRUE END deletable FROM {table} WHERE user_id = {user_id};".format(table=table, user_id=user_id)
    elif action == "check_poll":
        SQL = "SELECT FROM {table}"
    elif action == "delete_poll":
        SQL = ""
    return SQL
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