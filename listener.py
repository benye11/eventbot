import discord
from discord import Attachment
from discord import Embed
from discord.ext import commands
from datetime import datetime
from eventbot import getenv_variables
import psycopg2
import os
import time
import sched
import asyncio

class listener(commands.Cog):
    def __init__(self, bot, env_variables):
        self.bot = bot
        self.DATABASE_URL = env_variables[0]
        self.DATABASE_POLL_TABLE = env_variables[1]
        self.DATABASE_POLL_MESSAGE_ID_TABLE = env_variables[2]
        self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')
        self.cur = self.conn.cursor()
        self.args = ["FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE"]

    @commands.command
    async def on_ready():
        print('Logged in as {0.user}'.format(self.bot))

    @commands.command(aliases=['eventbot'])
    async def help(self, ctx):
        embed = discord.Embed(color=0x32A852, title='Commands', description='This is a list of all the commands and how to use them')
        embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
        embed.set_thumbnail(url='https://i.imgur.com/qn182DB.jpg')
        embed.add_field(name=".poll", value="create a poll for availability", inline=False)
        embed.add_field(name=".notify message", value="notify this channel with message", inline=False)
        embed.add_field(name=".schedule event_name event_day", value="schedules event notification at event_day\nevent_day format (year is assumed to be current year): Month/Day\nexample: 01/23", inline=False) #in the future, should be able to enter this into database. for now, just internal schedule
        #embed.add_field(name=".availability event_id", value="output people available for this event", inline=False) #implement later
        embed.add_field(name=".availability event_day", value="output people available for this time\nweekday format: Monday or 1, Tuesday or 2, etc.", inline=False)
        embed.add_field(name=".repo", value="output link to github repo. helpful links and resources are displayed in the README.md")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y %I:%M %p'))
        await ctx.send(embed=embed)
    
    @commands.command()
    async def poll(self, ctx):
        #check if a poll exists. we should have only one
        SQL = self.computesql(self.DATABASE_POLL_MESSAGE_ID_TABLE, "check_poll_message", "", payload.channel_id, "", "", "")
        self.cur.execute(SQL)
        fetch = cur.fetchone()
        if fetch is not None:
            await ctx.send("poll already exists! please edit that one and don't delete it")
        else:
            embed = discord.Embed(color=0x32A852, title='Poll Weekly Availability anytime between 6-10PM', description="If you are available at least 30 mins between 6-10PM, please react")
            embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
            embed.set_thumbnail(url='https://image.flaticon.com/icons/png/512/1458/1458512.png')
            embed.add_field(name="React with number emojis", value="1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣ corresponds to Monday, Tuesday, etc. and ❌ if not available for anything")
            current_time = datetime.now().strftime('%m/%d/%Y %I:%M %p')
            embed.set_footer(text=current_time)
            message = await ctx.send(embed=embed)
            SQL = self.compute(self.DATABASE_POLL_MESSAGE_ID_TABLE, "set_poll_message", str(message.id), str(message.channel.id), 0, 0, args)
            self.cur.execute(SQL)
            embed.add_field(name= "Message ID", value=str(message.id), inline=False)
            await message.edit(embed=embed) #add message ID for reference
            await message.pin() #pins message
    
    @commands.command()
    async def notify(self, ctx, *args):
        if len(args) == 0:
            await ctx.send("[Usage]: .notify <event_name>\n[Error message]: please provide event name")
        else:
            await ctx.send("Notifying " + "@everyone" + " that \"" + ' '.join(args) + "\" is happening now!")

    @commands.command()
    async def schedule(self, ctx, *args):
        if len(args) == 0:
            await ctx.send("[Usage]: .schedule <event_name> <event_day>\n[Error message]: please provide event name")
        else:
            time_input = ' '.join(args[-3:]) + ' ' + str(datetime.now().year)
            await ctx.send('time:' + time_input +"mm")
            event_input = ' '.join(args[:-3])
            try:
                parsed_time = datetime.strptime(time_input, '%m/%d %I:%M %p %Y') #definitely needs to handle more edge cases
                difference = parsed_time - datetime.now()
                await asyncio.sleep(difference.total_seconds())
                await ctx.send("[Scheduler] Notifying " + "@everyone" + " that \"" + event_input + "\" is happening now!")
            except Exception as e:
                await ctx.send("[Usage]: .schedule <event_name> <event_day>\n[Error message]: invalid <event_day>\n[Format]: Month/Day Hour:Minute AM/PM\n[Example]: 01/23 4:30 PM\ndebug message: " + str(e))

    @commands.command()
    async def availability(self, ctx, arg):
        if '/' in arg[0]:
            #query sql
            day = datetime.strptime(arg[0], "%m/%d").strftime("%A").lower()
            #computesql(self, table, action, user_id, username, column, column_index, args):
            SQL = self.computesql(self.DATABASE_POLL_TABLE, "fetch_users", "", "", day, 0, args)
            self.cur.execute(SQL)
            fetch = self.cur.fetchall()
            users = [x[0] for x in fetch]
            mentions = []
            for i in range(len(users)):
                user = await self.bot.fetch_user(users[i])
                mentions.append(user.mention)
            output = ', '.join(output)
            await ctx.send(output + " are available on " + arg[0] + "(" + day + ")")
            #now we have many tuples
            pass
        elif arg[0].isnumeric():
            #query sql
            await ctx.send("id parsing not implemented")
            pass
        else:
            await ctx.send("[Usage]: .availability <event_id or event_day> [Error message]: invalid date or ID")
        
    
    #NOTE: cache is cleared after every restart, so use raw_on_reaction_add
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        
        #sql implementation
        column_index = -1
        column = ""
        SQL = self.computesql(self.DATABASE_POLL_MESSAGE_ID_TABLE, "fetch_poll_message", payload.message_id, payload.channel_id, 0, 0, args)
        self.cur.execute(SQL)
        fetch = self.cur.fetchone()
        if int(fetch[0]) == int(payload.message_id) and int(fetch[1]) == int(payload.channel_id):
            if str(payload.emoji) == "1️⃣":
                column_index = 0
                column = "monday"
            elif str(payload.emoji) == "2️⃣":
                print('2')
                column_index = 1
                column = "tuesday"
            elif str(payload.emoji) == "3️⃣":
                column_index = 2
                column = "wednesday"
            elif str(payload.emoji) == "4️⃣":
                column_index = 3
                column = "thursday"
            elif str(payload.emoji) == "5️⃣":
                column_index = 4
                column = "friday"
            elif str(payload.emoji) == "6️⃣":
                column_index = 5
                column = "saturday"
            elif str(payload.emoji) == "7️⃣":
                column_index = 6
                column = "sunday"
            elif str(payload.emoji) == "❌":
                column_index = 7
            if column_index != -1:
                if column_index == 7:
                    SQL = self.computesql(self.DATABASE_POLL_TABLE, "delete", payload.user_id, user.name, 0, 0, args)
                    self.cur.execute(SQL)
                    await channel.send("executed delete SQL: " + SQL)
                else:
                    SQL = self.computesql(self.DATABASE_POLL_TABLE, "update", payload.user_id, user.name, column, column_index, args)
                    self.cur.execute(SQL)
                    await channel.send("executed update/insert SQL: " + SQL)

    def computesql(self, table, action, user_id, username, column, column_index, args):
        SQL = ''
        if action == "update":
            dup = args.clone()
            dup[column_index] = "TRUE"
            SQL = "INSERT INTO {table} (user_id, username, monday, tuesday, wednesday, thursday, friday, saturday, sunday) VALUES ({user_id}, {username}, {args[0]}, {args[1]}, {args[2]}, {args[3]}, {args[4]}, {args[5]}, {args[6]}) ON CONFLICT (user_id) DO UPDATE SET {column} = TRUE;".format(table=table, user_id=user_id, username=username, column=column, args=dup)
        elif action == "delete":
            SQL = "DELETE FROM {table} WHERE user_id = {user_id};".format(table=table, user_id=user_id)
        elif action == "check_user":
            SQL = "SELECT CASE WHEN monday | tuesday | wednesday | thursday | friday | saturday | sunday = 0 THEN FALSE ELSE TRUE END as \"deletable\" FROM {table} WHERE user_id = {user_id};".format(table=table, user_id=user_id)
        elif action == "fetch_users":
            SQL = "SELECT user_id, username FROM {table} WHERE {column} = {value};"
        elif action == "delete_poll_message":
            SQL = "DELETE FROM {table} WHERE poll_message_id = {user_id} AND channel_id = {username};".format(table=table, user_id=user_id, username=username)
        elif action == "check_poll_message":
            SQL = "SELECT poll_message_id FROM {table} WHERE channel_id = {username};".format(table=table, username=username)
        elif action == "fetch_poll_message":
            SQL = "SELECT poll_message_id, channel_id FROM {table} WHERE poll_message_id = {user_id} AND channel_id = {username};".format(table=table, user_id=user_id, username=username)
        elif action == "set_poll_message":
            SQL = "INSERT INTO {table} (poll_message_id, channel_id) VALUES ({user_id}, {username});".format(user_id=user_id, username=username)
        return SQL

def setup(bot):
    env_variables = getenv_variables()
    bot.add_cog(listener(bot, env_variables))