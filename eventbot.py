import discord
from discord import Attachment
from discord import Embed
from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime
import psycopg2
import os
import time
import sched
import asyncio

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')

env_variables = (os.environ['DATABASE_URL'], os.environ['DATABASE_POLL_TABLE'], os.environ['DATABASE_POLL_MESSAGE_ID_TABLE'])

class listener(commands.Cog):
    def __init__(self, bot, env_variables):
        self.bot = bot
        self.DATABASE_URL = env_variables[0]
        self.DATABASE_POLL_TABLE = env_variables[1]
        self.DATABASE_POLL_MESSAGE_ID_TABLE = env_variables[2]
        self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')
        self.cur = self.conn.cursor()
        self.args = ["FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE"]

    @commands.command(aliases=['eventbot'])
    async def help(self, ctx):
        embed = discord.Embed(color=0x32A852, title='Commands', description='This is a list of all the commands and how to use them')
        embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
        embed.set_thumbnail(url='https://i.imgur.com/qn182DB.jpg')
        embed.add_field(name=".poll", value="create a poll for availability", inline=False)
        embed.add_field(name=".notify message", value="notify this channel with message", inline=False)
        embed.add_field(name=".schedule event_name event_day", value="schedules event notification at event_day\nevent_day format (year is assumed to be current year): [Format]: Month/Day Hour:Minute AM/PM\nexample: 01/23 4:30 PM", inline=False) #in the future, should be able to enter this into database. for now, just internal schedule
        #embed.add_field(name=".availability event_id", value="output people available for this event", inline=False) #implement later
        embed.add_field(name=".availability event_day", value="output people available for this time\nday format: Month/Day Example: 01/23", inline=False)
        embed.add_field(name=".rr", value="output people haven't reacted to the poll. Alternate names: .requestresponse or .request_response", inline=False)
        embed.add_field(name=".repo", value="output link to github repo. helpful links and resources are displayed in the README.md")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y %I:%M %p'))
        await ctx.send(embed=embed)

    @commands.command() 
    async def poll(self, ctx):
        #check if a poll exists. we should have only one
        SQL = self.computesql(table=self.DATABASE_POLL_MESSAGE_ID_TABLE, action="check_poll_message_exists", channel_id="'" + str(ctx.channel.id) + "'")
        self.cur.execute(SQL)
        fetch = self.cur.fetchone()
        if fetch is None:
            embed = discord.Embed(color=0x32A852, title='Poll Weekly Availability anytime between 6-10PM', description="If you are available at least 30 mins between 6-10PM, please react")
            embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
            embed.set_thumbnail(url='https://image.flaticon.com/icons/png/512/1458/1458512.png')
            embed.add_field(name="React with number emojis", value="1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣ corresponds to Monday, Tuesday, etc. and ❌ if not available for anything")
            current_time = datetime.now().strftime('%m/%d/%Y %I:%M %p')
            embed.set_footer(text=current_time)
            message = await ctx.send(embed=embed)
            SQL = self.computesql(table=self.DATABASE_POLL_MESSAGE_ID_TABLE, action="set_poll_message", message_id="'" + str(message.id) + "'", channel_id="'" + str(message.channel.id) + "'")
            self.cur.execute(SQL)
            self.conn.commit() #commit changes to database
            embed.add_field(name= "Message ID", value=str(message.id), inline=False)
            await message.edit(embed=embed) #add message ID for reference
            await message.pin() #pins message
        elif fetch is not None and fetch[1] == str(ctx.channel.id):
            try:
                msg = await ctx.channel.fetch_message(int(fetch[0]))
                await ctx.send("poll already exists! please edit that one and don't delete it. It should be a pinned message")
            except Exception as e: #message doesn't exist, then delete from db. this is an error check
                SQL = self.computesql(table=self.DATABASE_POLL_MESSAGE_ID_TABLE, action="delete_poll_message", message_id="'" + str(fetch[0]) + "'", channel_id="'" + str(fetch[1]) + "'")
                self.cur.execute(SQL)
                embed = discord.Embed(color=0x32A852, title='Poll Weekly Availability anytime between 6-10PM', description="If you are available at least 30 mins between 6-10PM, please react")
                embed.set_author(name='Event Bot', icon_url='https://i.imgur.com/qn182DB.jpg')
                embed.set_thumbnail(url='https://image.flaticon.com/icons/png/512/1458/1458512.png')
                embed.add_field(name="React with number emojis", value="1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣ corresponds to Monday, Tuesday, etc. and ❌ if not available for anything")
                current_time = datetime.now().strftime('%m/%d/%Y %I:%M %p')
                embed.set_footer(text=current_time)
                message = await ctx.send(embed=embed)
                SQL = self.computesql(table=self.DATABASE_POLL_MESSAGE_ID_TABLE, action="set_poll_message", message_id="'" + str(message.id) + "'", channel_id="'" + str(message.channel.id) + "'")
                self.cur.execute(SQL)
                self.conn.commit() #commit changes to database
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
            #await ctx.send('time:' + time_input +"mm")
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
        if '/' in arg:
            #query sql
            day = datetime.strptime(arg + " " + str(datetime.now().year), "%m/%d %Y").strftime("%A").lower()
            #computesql(self, table, action, user_id, username, column, column_index, args):
            SQL = self.computesql(table=self.DATABASE_POLL_TABLE, action="fetch_available_users", channel_id="'" + str(ctx.channel.id) + "'", column=day)
            self.cur.execute(SQL)
            fetch = self.cur.fetchall()
            users = [x[0] for x in fetch]
            mentions = []
            for i in range(len(users)):
                user = await self.bot.fetch_user(users[i])
                mentions.append(user.mention)
            if len(mentions) == 0:
                await ctx.send("no one is available on " + arg + " (" + day + ")")
            elif len(mentions) == 1:
                await ctx.send(mentions[0] + " is available on " + arg + " (" + day + ")")
            else:
                output = ', '.join(mentions)
                index = output.rfind(',')
                output = output[:index] + ' and' + output[index+1:]
                await ctx.send(output + " are available on " + arg + " (" + day + ")")
            #now we have many tuples
            pass
        elif arg.isnumeric():
            #query sql
            await ctx.send("id parsing not implemented")
            pass
        else:
            await ctx.send("[Usage]: .availability <event_id or event_day> [Error message]: invalid date or ID")

    @commands.command(aliases=['requestresponse', 'request_response'])
    async def rr(self, ctx):
        SQL = self.computesql(table=self.DATABASE_POLL_TABLE, action="fetch_all_users", channel_id= "'" + str(ctx.channel.id) + "'")
        self.cur.execute(SQL)
        fetch = self.cur.fetchall()
        user_ids = [x[0] for x in fetch]
        mentions = []
        for user_id in user_ids:
            user = await self.bot.fetch_user(user_id)
            mentions.append(user.mention)
        if len(mentions) == 0:
            await ctx.send("everyone has responded to the poll")
        elif len(mentions) == 1:
            await ctx.send(mentions[0] + " hasn't responded")
        else:
            output = ', '.join(mentions)
            index = output.rfind(',')
            output = output[:index] + ' and' + output[index+1:]
            await ctx.send(output + " haven't responded")

    @commands.command()
    async def repo(self, ctx):
        embed= discord.Embed(title="Repo Link", url="https://github.com/benye11/eventbot", description="Developed in Python", color=0x000000)
        await ctx.send(embed=embed)
        
    #NOTE: cache is cleared after every restart, so use raw_on_reaction_add
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        
        #sql implementation
        column_index = -1
        column = ""
        SQL = self.computesql(table=self.DATABASE_POLL_MESSAGE_ID_TABLE, action="fetch_poll_message", message_id="'" + str(payload.message_id) + "'", channel_id="'" + str(payload.channel_id) + "'")
        self.cur.execute(SQL)
        fetch = self.cur.fetchone()
        if fetch is None:
            pass
        elif int(fetch[0]) == int(payload.message_id) and int(fetch[1]) == int(payload.channel_id):
            if str(payload.emoji) == "1️⃣":
                column_index = 0
                column = "monday"
            elif str(payload.emoji) == "2️⃣":
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
                value = "TRUE"
                SQL = self.computesql(table=self.DATABASE_POLL_TABLE, action="add_user_selection", value=value, channel_id="'" + str(payload.channel_id) + "'", user_id="'" + str(payload.user_id) + "'", username="'" + str(user.name) + "'", column=column, column_index=column_index, args=self.args)
                self.cur.execute(SQL)
                self.conn.commit() #must commit to database
                #await channel.send("executed update/insert SQL: " + SQL)

    #NOTE: cache is cleared after every restart, so use raw_on_reaction_add
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        
        #sql implementation
        column_index = -1
        column = ""
        value = ""
        SQL = self.computesql(table=self.DATABASE_POLL_MESSAGE_ID_TABLE, action="fetch_poll_message", message_id="'" + str(payload.message_id) + "'", channel_id="'" + str(payload.channel_id) + "'")
        self.cur.execute(SQL)
        fetch = self.cur.fetchone()
        if fetch is None:
            pass
        elif int(fetch[0]) == int(payload.message_id) and int(fetch[1]) == int(payload.channel_id):
            if str(payload.emoji) == "1️⃣":
                value = "FALSE"
                column = "monday"
            elif str(payload.emoji) == "2️⃣":
                value = "FALSE"
                column = "tuesday"
            elif str(payload.emoji) == "3️⃣":
                value = "FALSE"
                column = "wednesday"
            elif str(payload.emoji) == "4️⃣":
                value = "FALSE"
                column = "thursday"
            elif str(payload.emoji) == "5️⃣":
                value = "FALSE"
                column = "friday"
            elif str(payload.emoji) == "6️⃣":
                value = "FALSE"
                column = "saturday"
            elif str(payload.emoji) == "7️⃣":
                value = "FALSE"
                column = "sunday"
            elif str(payload.emoji) == "❌":
                value = "FALSE"
                column = "unavailable"
            if column_index != -1:
                user_id = "'" + str(payload.user_id) + "'"
                channel_id = "'" + str(payload.channel_id) + "'"
                username = "'" + str(user.name) + "'"
                #SQL = self.computesql(table=self.DATABASE_POLL_TABLE, action="add_user_selection", channel_id="'" + str(payload.channel_id) + "'", user_id="'" + str(payload.user_id) + "'", username="'" + str(user.name) + "'", column, column_index, self.args)
                SQL = self.computesql(table=self.DATABASE_POLL_TABLE, action="remove_user_selection", value=value, user_id=user_id, channel_id=channel_id, username=username, column=column, args=self.args)
                self.cur.execute(SQL)
                self.conn.commit()
                SQL = self.computesql(table=self.DATABASE_POLL_TABLE, action="delete_user_if_no_reactions", user_id=user_id, channel_id=channel_id)
                self.cur.execute(SQL)
                self.conn.commit()

    def computesql(self, table="", action="", value="", user_id="", username="", channel_id="", column=-1, column_index=-1, args=[], message_id="", unavailable="FALSE"):
        SQL = ''
        if action == "add_user_selection":
            dup = args.copy()
            if column_index != 7:
                dup[column_index] = "TRUE"
                #you need to add channel_id in here later for multi-channel use
                SQL = "INSERT INTO {table} (user_id, username, channel_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, unavailable) VALUES ({user_id}, {username}, {channel_id}, {args[0]}, {args[1]}, {args[2]}, {args[3]}, {args[4]}, {args[5]}, {args[6]}, {unavailable}) ON CONFLICT (user_id, channel_id) DO UPDATE SET {column} = {value};".format(table=table, value=value, user_id=user_id, username=username, channel_id=channel_id, column=column, args=dup, unavailable=unavailable)
        elif action == "remove_user_selection":
            SQL = "UPDATE {table} SET {column} = {value} WHERE user_id = {user_id} AND channel_id = {channel_id};".format(table=table, value=value, user_id=user_id, column=column, channel_id=channel_id)
        elif action == "delete_user_if_no_reactions":
            SQL = "IF ((SELECT COUNT(user_id) FROM {table} WHERE (monday OR tuesday OR wednesday OR thursday OR friday OR saturday OR sunday OR unavailable) = FALSE AND user_id = {user_id} AND channel_id = {channel_id}) > 0) THEN DELETE FROM {table} WHERE user_id = {user_id} AND channel_id = {channel_id} END IF;".format(table=table, user_id=user_id, channel_id=channel_id)
        elif action == "fetch_all_users":
            SQL = "SELECT user_id, username FROM {table} WHERE channel_id = {channel_id};".format(table=table, channel_id=channel_id)
        elif action == "fetch_available_users":
            SQL = "SELECT user_id, username FROM {table} WHERE {column} = TRUE AND channel_id = {channel_id} AND unavailable = FALSE;".format(table=table, channel_id=channel_id, column=column)
        elif action == "delete_poll_message":
            SQL = "DELETE FROM {table} WHERE poll_message_id = {message_id} AND channel_id = {channel_id};".format(table=table, message_id=message_id, channel_id=channel_id)
        elif action == "check_poll_message_exists":
            SQL = "SELECT poll_message_id, channel_id FROM {table} WHERE channel_id = {channel_id};".format(table=table, channel_id=channel_id)
        elif action == "fetch_poll_message":
            SQL = "SELECT poll_message_id, channel_id FROM {table} WHERE poll_message_id = {message_id} AND channel_id = {channel_id};".format(table=table, message_id=message_id, channel_id=channel_id)
        elif action == "set_poll_message":
            SQL = "INSERT INTO {table} (poll_message_id, channel_id) VALUES ({message_id}, {channel_id});".format(table=table, message_id=message_id, channel_id=channel_id)
        return SQL

class BotClass():
    def __init__(self, bot, env_variables):
        self.bot = bot
        self.bot.add_cog(listener(bot, env_variables))
        bot.run(os.getenv('TOKEN'))

    @bot.event
    async def on_ready():
        print('Logged in as {0.user}'.format(bot))


botobj = BotClass(bot, env_variables)