import discord
from discord.ext import commands
import sqlite3
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from contextlib import closing
import re

# 1. Token Security
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No bot token found. Make sure to set it in your .env file.")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("./"), intents=intents)
bot.remove_command('help')

# Logging configuration
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='bot.log')

# Console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

ALLOWED_ROLE_IDS = [1191071898218549270, 1278866719384932374, 1191072430781894716]

# 2. Input Validation
def validate_age(age):
    try:
        age = int(age)
        if age < 0:
            raise ValueError("Age cannot be negative")
        if age < 18:
            return age, "underage"
        return age, "of_age"
    except ValueError:
        raise ValueError("Invalid age input")

def sanitize_input(input_string):
    # Remove any potentially dangerous characters
    return re.sub(r'[^\w\s-]', '', input_string).strip()

# 3. Error Handling
def handle_error(error, context=""):
    error_message = f"An error occurred {context}: {str(error)}"
    logging.error(error_message)
    return "An unexpected error occurred. Please try again later or contact an administrator."

# 4. Database Security
def init_db():
    try:
        with closing(sqlite3.connect('users.db')) as conn:
            with closing(conn.cursor()) as c:
                c.execute('''CREATE TABLE IF NOT EXISTS underage_users
                             (id TEXT PRIMARY KEY, 
                              name TEXT, 
                              age INTEGER, 
                              account_creation TEXT, 
                              join_date TEXT)''')
                conn.commit()
        logging.info("Database initialized successfully")
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during database initialization: {e}")

def add_underage_user(user_id, name, age, account_creation, join_date):
    try:
        with closing(sqlite3.connect('users.db')) as conn:
            with closing(conn.cursor()) as c:
                c.execute("""INSERT OR REPLACE INTO underage_users 
                             (id, name, age, account_creation, join_date) 
                             VALUES (?, ?, ?, ?, ?)""",
                          (str(user_id), sanitize_input(name), age, account_creation, join_date))
                conn.commit()
        logging.info(f"Added underage user: {user_id}")
    except sqlite3.Error as e:
        logging.error(f"Database error in add_underage_user: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in add_underage_user: {e}")

def remove_underage_user(user_id):
    try:
        with closing(sqlite3.connect('users.db')) as conn:
            with closing(conn.cursor()) as c:
                c.execute("DELETE FROM underage_users WHERE id=?", (str(user_id),))
                conn.commit()
        logging.info(f"Removed underage user: {user_id}")
    except sqlite3.Error as e:
        logging.error(f"Database error in remove_underage_user: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in remove_underage_user: {e}")

def is_underage(user_id):
    try:
        with closing(sqlite3.connect('users.db')) as conn:
            with closing(conn.cursor()) as c:
                c.execute("SELECT * FROM underage_users WHERE id=?", (str(user_id),))
                result = c.fetchone()
        return result is not None
    except sqlite3.Error as e:
        logging.error(f"Database error in is_underage: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in is_underage: {e}")
    return False

# 5. Permission Management
def has_allowed_role():
    async def predicate(ctx):
        return any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles)
    return commands.check(predicate)

ADULT_ONLY_CHANNEL_ID = 1191075004285202503

@bot.event
async def on_member_join(member):
    try:
        await member.send("Welcome to the server! Please enter your age to get access to the appropriate channels.")
        
        def check(m):
            return m.author == member and isinstance(m.channel, discord.DMChannel)
        
        response = await bot.wait_for('message', timeout=60.0, check=check)
        age, age_status = validate_age(response.content)
        logging.info(f"Age validation result: age={age}, status={age_status}")

        account_creation = member.created_at.isoformat()
        join_date = member.joined_at.isoformat()

        if age_status == "underage":
            logging.info(f"Adding underage user: id={member.id}, name={member.name}, age={age}")
            add_underage_user(member.id, member.name, age, account_creation, join_date)
            
            # Restrict access to adult-only channel
            adult_channel = member.guild.get_channel(ADULT_ONLY_CHANNEL_ID)
            if adult_channel:
                await adult_channel.set_permissions(member, read_messages=False, send_messages=False)
                logging.info(f"Restricted access to adult-only channel for underage user: {member.id}")
            
            await member.send(f"Your age ({age}) has been recorded. As you are under 18, your access to certain channels will be restricted.")
        else:
            remove_underage_user(member.id)
            await member.send(f"Your age ({age}) has been recorded. You have full access to the server.")

        logging.info(f"User {member.id} joined and was verified as {age_status}")
    except ValueError as e:
        logging.error(f"ValueError in age verification: {str(e)}")
        await member.send(f"Age verification failed: {str(e)}")
    except asyncio.TimeoutError:
        logging.error("Timeout in age verification")
        await member.send("You took too long to respond. Please try again later.")
    except Exception as e:
        error_message = handle_error(e, "in on_member_join")
        logging.error(f"Unexpected error in on_member_join: {str(e)}")
        await member.send(error_message)

@bot.command(name='manualverify', aliases=['mv'])
async def manualverify(ctx, member: discord.Member):
    if is_underage(member.id):
        await ctx.send(f"{member.mention} is already verified as underage.")
        return

    await ctx.send(f"Sending age verification to {member.mention}.")

    try:
        await member.send("Please enter your age to verify.")

        def check(m):
            return m.author == member and isinstance(m.channel, discord.DMChannel)

        response = await bot.wait_for('message', timeout=60.0, check=check)
        age, age_status = validate_age(response.content)

        account_creation = member.created_at.isoformat()
        join_date = member.joined_at.isoformat()

        adult_channel = ctx.guild.get_channel(ADULT_ONLY_CHANNEL_ID)

        if age_status == "underage":
            add_underage_user(member.id, member.name, age, account_creation, join_date)
            await member.send(f"Your age ({age}) has been recorded. As you are under 18, your access to certain channels will be restricted.")
            await ctx.send(f"{member.mention} is now marked as underage.")
            
            if adult_channel:
                await adult_channel.set_permissions(member, read_messages=False, send_messages=False)
                logging.info(f"Restricted access to adult-only channel for underage user: {member.id}")
            
            logging.info(f"User {member.id} manually verified as underage by {ctx.author.id}")
        else:
            remove_underage_user(member.id)
            await member.send(f"Your age ({age}) has been recorded. You have full access to the server.")
            await ctx.send(f"{member.mention} is verified as not underage.")
            
            if adult_channel:
                await adult_channel.set_permissions(member, overwrite=None)
                logging.info(f"Removed restrictions from adult-only channel for user: {member.id}")
            
            logging.info(f"User {member.id} manually verified as of age by {ctx.author.id}")

    except asyncio.TimeoutError:
        await member.send("You took too long to respond. Please try again later.")
    except Exception as e:
        error_message = handle_error(e, "in manualverify command")
        await member.send(error_message)
        await ctx.send("An error occurred during verification. Please try again later.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    else:
        error_message = handle_error(error, "in command execution")
        await ctx.send(error_message)

@bot.command()
async def gotcha(ctx):
    """Destinys Qoute"""
    await ctx.send('Anything Else?')

@bot.command()
async def test1(ctx):
    """My Jokes"""
    await ctx.send('I cant wait to see what cosmic horrors I will face in NeoPunkFMs Discord')

@bot.command(aliases=['h'])
async def help(ctx):
    hlpembed = discord.Embed(title="Help Menu", colour=discord.Colour.blue())
    hlpembed.add_field(name="snipe / s", value="This snipes the user's last message", inline=False)
    hlpembed.add_field(name="ex:", value=" .snipe", inline=False)
    
    await ctx.send(embed=hlpembed)

init_db()
bot.run(BOT_TOKEN)
