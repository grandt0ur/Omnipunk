import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from contextlib import closing
import re
import mysql.connector
from mysql.connector import Error
import random

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID'))

if not BOT_TOKEN:
    raise ValueError("No bot token found. Make sure to set it in your .env file.")

if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID:
    raise ValueError("YouTube API key or Channel ID not found. Make sure to set them in your .env file.")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("./"), intents=intents)

# Remove the default help command
bot.remove_command('help')

@bot.command(name='help', aliases=['h'])
async def custom_help(ctx, command_name: str = None):
    """Display help information for commands"""
    if command_name is None:
        # General help message
        embed = discord.Embed(title="Bot Commands", description="Here are the available commands:", color=discord.Color.blue())
        
        # Regular User Commands
        user_commands = """
        `./help` or `./h`: Display this help message
        `./poll #channel "Question" "Option1" "Option2" ...`: Create a poll in the specified channel (ADMIN ONLY)
        `./pollresults <message_id> [#channel]`: Display the results of a poll (ADMIN ONLY)
        `./vote <poll_id> <option_number>`: Vote on a poll
        `./punch <@user>`: Punch another user
        `./kill <@user>`: Virtually kill another user
        """
        embed.add_field(name="User Commands", value=user_commands, inline=False)
    else:
        # Command-specific help
        command = bot.get_command(command_name)
        if command is None:
            await ctx.send(f"No command called '{command_name}' found.")
            return

        embed = discord.Embed(title=f"Help: {command.name}", color=discord.Color.green())
        embed.add_field(name="Description", value=command.help or "No description available.", inline=False)
        
        usage = f"{ctx.prefix}{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
        
        # Check if it's an admin command
        if any(isinstance(check, commands.has_any_role) for check in command.checks):
            embed.add_field(name="Note", value="This is an admin command and requires specific roles to use.", inline=False)

    await ctx.send(embed=embed)

@custom_help.error
async def custom_help_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Invalid command name. Please use `./help` to see all available commands.")
    else:
        await ctx.send("An error occurred while trying to display the help message. Please try again later.")
        print(f"Error in help command: {error}")

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

# Database connection details
DB_HOST = "us.mysql.db.bot-hosting.net"
DB_PORT = 3306
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = "s148168_users"

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_underage_users_table():
    connection = create_db_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS underage_users (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            age INT,
            account_creation DATETIME,
            join_date DATETIME
        )
        """)
        connection.commit()
        print("Underage users table created successfully")
    except Error as e:
        print(f"Error creating underage users table: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_underage_user(user_id, name, age, account_creation, join_date):
    connection = create_db_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        
        # Convert datetime strings to MySQL compatible format
        account_creation = datetime.fromisoformat(account_creation).strftime('%Y-%m-%d %H:%M:%S')
        join_date = datetime.fromisoformat(join_date).strftime('%Y-%m-%d %H:%M:%S')
        
        query = """INSERT INTO underage_users 
                   (id, name, age, account_creation, join_date) 
                   VALUES (%s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE 
                   name=%s, age=%s, account_creation=%s, join_date=%s"""
        values = (str(user_id), name, age, account_creation, join_date,
                  name, age, account_creation, join_date)
        cursor.execute(query, values)
        connection.commit()
        print(f"Added underage user: {user_id}")
    except Error as e:
        print(f"Error adding underage user: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def remove_underage_user(user_id):
    connection = create_db_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        query = "DELETE FROM underage_users WHERE id = %s"
        cursor.execute(query, (str(user_id),))
        connection.commit()
        print(f"Removed underage user: {user_id}")
    except Error as e:
        print(f"Error removing underage user: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def is_underage(user_id):
    connection = create_db_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM underage_users WHERE id = %s"
        cursor.execute(query, (str(user_id),))
        result = cursor.fetchone()
        return result is not None
    except Error as e:
        print(f"Error checking underage status: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Call this function when your bot starts up
create_underage_users_table()

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
@commands.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')
async def manualverify(ctx, member: discord.Member):
    """Sends the age verification to users who may not have had to do it"""
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

@bot.command(name='gotcha')
async def gotcha(ctx):
    """Destiny's Quote"""
    await ctx.send('Anything Else?')

@bot.command(name='test1')
async def test1(ctx):
    """My Jokes"""
    await ctx.send('I cant wait to see what cosmic horrors I will face in NeoPunkFMs Discord')

@bot.command(name='underage_list')
@commands.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')  # Adjust roles as needed
async def underage_list(ctx):
    """Retrieve and display a list of underage users from the database."""
    connection = create_db_connection()
    if connection is None:
        await ctx.send("Failed to connect to the database. Please try again later.")
        return

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, name, age FROM underage_users ORDER BY name"
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            await ctx.send("No underage users found in the database.")
            return

        # Create an embed to display the results
        embed = discord.Embed(title="Underage Users List", color=discord.Color.blue())
        embed.set_footer(text=f"Total underage users: {len(results)}")

        # Split the results into chunks of 25 (Discord's field limit per embed)
        chunks = [results[i:i + 25] for i in range(0, len(results), 25)]

        for i, chunk in enumerate(chunks):
            field_value = "\n".join([f"**{user['name']}** (ID: {user['id']}, Age: {user['age']})" for user in chunk])
            embed.add_field(name=f"Users {i*25+1}-{i*25+len(chunk)}", value=field_value, inline=False)

        await ctx.send(embed=embed)

    except Error as e:
        print(f"Error retrieving underage users: {e}")
        await ctx.send("An error occurred while retrieving the underage users list.")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@underage_list.error
async def underage_list_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("You don't have permission to use this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# You might want to replace this with actual image URLs
PUNCH_IMAGES = [
    "https://example.com/punch1.gif",
    "https://example.com/punch2.gif",
    # Add more punch image URLs here
]

@bot.command()
async def punch(ctx, member: discord.Member):
    """Punch another user"""
    if member == ctx.author:
        punch_image = random.choice(PUNCH_IMAGES)
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.set_image(url=punch_image)
        await ctx.send(f"{ctx.author.mention} punched themselves!", embed=embed)
    else:
        await ctx.send(f"{member.mention} got knocked out by {ctx.author.mention}!")
    await ctx.message.delete()

@bot.command()
async def kill(ctx, member: discord.Member):
    """Virtually kill another user"""
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention} committed seppuku!")
    else:
        await ctx.send(f"{member.mention} was killed by {ctx.author.mention}!")
    await ctx.message.delete()

# Error handling for these commands
@punch.error
@kill.error
async def interaction_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to mention a user to use this command!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Couldn't find that user. Make sure you're mentioning a valid user.")

bot.run(BOT_TOKEN)
