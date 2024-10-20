import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import mysql.connector
from mysql.connector import Error
import random
import re
from collections import defaultdict

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', 0))
ADULT_ONLY_CHANNEL_ID = int(os.getenv('ADULT_ONLY_CHANNEL_ID', 0))
REPORT_CHANNEL_ID = int(os.getenv('REPORT_CHANNEL_ID', 0))


if not BOT_TOKEN:
    raise ValueError("No bot token found. Make sure to set it in your .env file.")

if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID:
    raise ValueError("YouTube API key or Channel ID not found. Make sure to set them in your .env file.")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("./"), intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Command tree synced!")

bot = MyBot()

# Logging configuration
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='bot.log')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

ALLOWED_ROLE_IDS = [1191071898218549270, 1278866719384932374, 1191072430781894716]

# Input Validation
def validate_age(age):
    try:
        age = int(age)
        if age < 0 or age > 120:  # Reasonable age range
            raise ValueError("Age cannot be negative or unreasonably high")
        if age < 18:
            return age, "underage"
        return age, "of_age"
    except ValueError:
        raise ValueError("Invalid age input")

def sanitize_input(input_string):
    return re.sub(r'[^\w\s-]', '', input_string).strip()

# Error Handling
def handle_error(error, context=""):
    error_message = f"An error occurred {context}: {str(error)}"
    logging.error(error_message)
    return "An unexpected error occurred. Please try again later or contact an administrator."

# Database connection details
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Validate that we have all necessary database information
if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing database connection information. Please check your .env file.")

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
        logging.error(f"Error connecting to MySQL database: {e}")
        return None

def execute_db_query(query, params=None):
    connection = create_db_connection()
    if connection is None:
        logging.error("Failed to create database connection")
        return None

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                logging.info(f"Query executed successfully. Rows returned: {len(result)}")
                return result
            else:
                connection.commit()
                logging.info(f"Query executed successfully. Rows affected: {cursor.rowcount}")
                return cursor.rowcount
    except Error as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def create_underage_users_table():
    query = """
    CREATE TABLE IF NOT EXISTS underage_users (
        id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        age INT,
        account_creation DATETIME,
        join_date DATETIME
    )
    """
    result = execute_db_query(query)
    if result is not None:
        logging.info("underage_users table created or already exists")
    else:
        logging.error("Failed to create underage_users table")

# Call this function when your bot starts up
create_underage_users_table()


def add_underage_user(user_id, name, age, account_creation, join_date):
    # Convert ISO format strings to datetime objects
    account_creation_dt = datetime.fromisoformat(account_creation.replace('+00:00', ''))
    join_date_dt = datetime.fromisoformat(join_date.replace('+00:00', ''))
    
    # Format datetime objects to MySQL-compatible format
    account_creation_formatted = account_creation_dt.strftime('%Y-%m-%d %H:%M:%S')
    join_date_formatted = join_date_dt.strftime('%Y-%m-%d %H:%M:%S')

    query = """INSERT INTO underage_users 
               (id, name, age, account_creation, join_date) 
               VALUES (%s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE 
               name=%s, age=%s, account_creation=%s, join_date=%s"""
    params = (str(user_id), name, age, account_creation_formatted, join_date_formatted,
              name, age, account_creation_formatted, join_date_formatted)
    result = execute_db_query(query, params)
    if result is None or result == 0:
        logging.error(f"Failed to add underage user: {user_id}")
    else:
        logging.info(f"Successfully added/updated underage user: {user_id}")

def remove_underage_user(user_id):
    query = "DELETE FROM underage_users WHERE id = %s"
    execute_db_query(query, (str(user_id),))

def is_underage(user_id):
    query = "SELECT * FROM underage_users WHERE id = %s"
    result = execute_db_query(query, (str(user_id),))
    return result is not None and len(result) > 0

# Call this function when your bot starts up
create_underage_users_table()

@bot.tree.command(name="help")
@app_commands.describe(command_name="The command to get help for")
async def help_command(interaction: discord.Interaction, command_name: str = None):
    """Display help information for commands"""
    if command_name is None:
        embed = discord.Embed(title="Bot Commands", description="Here are the available commands:", color=discord.Color.blue())
        
        user_commands = """
        `/help`: Display this help message
        `/poll`: Create a poll in the specified channel (ADMIN ONLY)
        `/pollresults`: Display the results of a poll (ADMIN ONLY)
        `/punch`: Punch another user
        `/kill`: Virtually kill another user
        `/repeat`: Repeat a message
        `/manualverify`: Manually verify a user's age (ADMIN ONLY)
        `/underage_list`: List underage users (ADMIN ONLY)
        `/announce`: Send an announcement (ADMIN ONLY)
        `/snipe`: Show the last deleted message in the channel
        """
        embed.add_field(name="User Commands", value=user_commands, inline=False)
    else:
        command = bot.tree.get_command(command_name)
        if command is None:
            await interaction.response.send_message(f"No command called '{command_name}' found.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Help: {command.name}", color=discord.Color.green())
        embed.add_field(name="Description", value=command.description or "No description available.", inline=False)
        
        if command.checks:
            embed.add_field(name="Note", value="This is an admin command and requires specific roles to use.", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="poll")
@app_commands.describe(
    channel="The channel to create the poll in",
    question="The poll question",
    options="The poll options (separate with spaces)"
)
@app_commands.checks.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')
async def poll(interaction: discord.Interaction, channel: discord.TextChannel, question: str, options: str):
    """Create a poll in the specified channel"""
    option_list = options.split()
    if len(option_list) < 2:
        await interaction.response.send_message("You need at least two options for a poll!", ephemeral=True)
        return
    if len(option_list) > 10:
        await interaction.response.send_message("You can only have up to 10 options in a poll!", ephemeral=True)
        return

    embed = discord.Embed(title="📊 " + question, color=discord.Color.blue())
    description = "\n".join(f"{POLL_EMOJIS[i]} {option}" for i, option in enumerate(option_list))
    embed.description = description

    poll_message = await channel.send("@everyone A new poll has been created!", embed=embed)

    for i in range(len(option_list)):
        await poll_message.add_reaction(POLL_EMOJIS[i])

    await interaction.response.send_message(f"Poll created in {channel.mention}!", ephemeral=True)

@bot.tree.command(name="pollresults")
@app_commands.describe(
    message_id="The ID of the poll message",
    channel="The channel where the poll is located"
)
@app_commands.checks.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')
async def poll_results(interaction: discord.Interaction, message_id: str, channel: discord.TextChannel = None):
    """Display the results of a poll"""
    channel = channel or interaction.channel
    try:
        poll_message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        await interaction.response.send_message("Couldn't find a message with that ID in the specified channel.", ephemeral=True)
        return

    if not poll_message.embeds:
        await interaction.response.send_message("That message doesn't seem to be a poll.", ephemeral=True)
        return

    embed = poll_message.embeds[0]
    if not embed.description:
        await interaction.response.send_message("This poll doesn't have any options.", ephemeral=True)
        return

    options = embed.description.split('\n')
    results = []

    for i, option in enumerate(options):
        reaction = discord.utils.get(poll_message.reactions, emoji=POLL_EMOJIS[i])
        if reaction:
            results.append((option, reaction.count - 1))

    results.sort(key=lambda x: x[1], reverse=True)
    
    result_embed = discord.Embed(title=f"Results for: {embed.title}", color=discord.Color.green())
    for option, count in results:
        result_embed.add_field(name=option, value=f"{count} votes", inline=False)

    await interaction.response.send_message(embed=result_embed)

@bot.tree.command(name="punch")
@app_commands.describe(user="The user to punch")
async def punch(interaction: discord.Interaction, user: discord.Member):
    """Punch another user"""
    if user == interaction.user:
        punch_image = random.choice(PUNCH_IMAGES)
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.set_image(url=punch_image)
        await interaction.response.send_message(f"{interaction.user.mention} punched themselves!", embed=embed)
    else:
        await interaction.response.send_message(f"{user.mention} got knocked out by {interaction.user.mention}!")

@bot.tree.command(name="kill")
@app_commands.describe(user="The user to kill")
async def kill(interaction: discord.Interaction, user: discord.Member):
    """Virtually kill another user"""
    if user == interaction.user:
        await interaction.response.send_message(f"{interaction.user.mention} committed seppuku!")
    else:
        await interaction.response.send_message(f"{user.mention} was killed by {interaction.user.mention}!")

@bot.tree.command(name="repeat")
@app_commands.describe(message="The message to repeat")
async def repeat(interaction: discord.Interaction, message: str):
    """Repeats the user's message"""
    await interaction.response.send_message(message)

@bot.tree.command(name="manualverify")
@app_commands.describe(member="The member to verify")
@app_commands.checks.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')
async def manualverify(interaction: discord.Interaction, member: discord.Member):
    """Sends the age verification to users who may not have had to do it"""
    if is_underage(member.id):
        await interaction.response.send_message(f"{member.mention} is already verified as underage.", ephemeral=True)
        return

    await interaction.response.send_message(f"Sending age verification to {member.mention}.", ephemeral=True)

    try:
        await member.send("Please enter your age to verify.")

        def check(m):
            return m.author == member and isinstance(m.channel, discord.DMChannel)

        response = await bot.wait_for('message', timeout=60.0, check=check)
        age, age_status = validate_age(response.content)

        account_creation = member.created_at.isoformat()
        join_date = member.joined_at.isoformat()

        adult_channel = interaction.guild.get_channel(ADULT_ONLY_CHANNEL_ID)

        if age_status == "underage":
            add_underage_user(member.id, member.name, age, account_creation, join_date)
            logging.info(f"Attempting to add underage user: {member.id}, {member.name}, {age}")
            await member.send(f"Your age ({age}) has been recorded. As you are under 18, your access to certain channels will be restricted.")
            await interaction.followup.send(f"{member.mention} is now marked as underage.", ephemeral=True)
            
            if adult_channel:
                await adult_channel.set_permissions(member, read_messages=False, send_messages=False)
                logging.info(f"Restricted access to adult-only channel for underage user: {member.id}")
            
            logging.info(f"User {member.id} manually verified as underage by {interaction.user.id}")
        else:
            remove_underage_user(member.id)
            await member.send(f"Your age ({age}) has been recorded. You have full access to the server.")
            await interaction.followup.send(f"{member.mention} is verified as not underage.", ephemeral=True)
            
            if adult_channel:
                await adult_channel.set_permissions(member, overwrite=None)
                logging.info(f"Removed restrictions from adult-only channel for user: {member.id}")
            
            logging.info(f"User {member.id} manually verified as of age by {interaction.user.id}")

    except asyncio.TimeoutError:
        await member.send("You took too long to respond. Please try again later.")
    except Exception as e:
        error_message = handle_error(e, "in manualverify command")
        await member.send(error_message)
        await interaction.followup.send("An error occurred during verification. Please try again later.", ephemeral=True)

@bot.tree.command()
@app_commands.checks.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')
async def underage_list(interaction: discord.Interaction):
    """Retrieve and display a list of underage users from the database."""
    query = "SELECT id, name, age FROM underage_users ORDER BY name"
    results = execute_db_query(query)

    if results is None:
        await interaction.response.send_message("Failed to retrieve underage users. Please try again later.", ephemeral=True)
        return

    if not results:
        await interaction.response.send_message("No underage users found in the database.", ephemeral=True)
        return

    embed = discord.Embed(title="Underage Users List", color=discord.Color.blue())
    embed.set_footer(text=f"Total underage users: {len(results)}")

    chunks = [results[i:i + 25] for i in range(0, len(results), 25)]

    for i, chunk in enumerate(chunks):
        field_value = "\n".join([f"**{user['name']}** (ID: {user['id']}, Age: {user['age']})" for user in chunk])
        embed.add_field(name=f"Users {i*25+1}-{i*25+len(chunk)}", value=field_value, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

last_deleted_messages = defaultdict(lambda: None)

@bot.event
async def on_message_delete(message):
    last_deleted_messages[message.channel.id] = message
    print(f"Message deleted in channel {message.channel.id}: {message.content}")

@bot.tree.command(name="snipe", description="Show the last deleted message in the channel")
async def snipe(interaction: discord.Interaction):
    """Show the last deleted message in the channel."""
    deleted_message = last_deleted_messages.get(interaction.channel.id)
    if deleted_message:
        embed = discord.Embed(description=deleted_message.content, color=discord.Color.red())
        embed.set_author(name=deleted_message.author.name, icon_url=deleted_message.author.display_avatar.url)
        embed.timestamp = deleted_message.created_at
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("No recently deleted messages found in this channel.")

# Sync command
@bot.command()
@commands.is_owner()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"Synced {len(synced)} commands.")

@bot.tree.command()
@app_commands.checks.has_any_role('NeoPunkFM', 'NPFM Affiliate', 'Neo-Engineer')
@app_commands.describe(
    channel="The channel to send the announcement to",
    message="The announcement message"
)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    """Sends an announcement to the specified channel"""
    try:
        await channel.send(message)
        await interaction.response.send_message(f"Announcement sent to {channel.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to send messages in that channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

PUNCH_IMAGES = [
    "https://gifdb.com/images/high/kasumi-nakasu-love-live-punching-aemy2k35e12ripji.webp",
    "https://gifdb.com/images/high/man-entering-room-and-punching-bo8w5138igevlh2l.webp",
    "https://c.tenor.com/VrWzG0RWmRQAAAAC/tenor.gif",
]

POLL_EMOJIS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

# Get Guild ID from .env file
GUILD_ID = int(os.getenv('GUILD_ID'))

@bot.command()
async def report(ctx, message_or_user: str = None, *, reason: str = None):
    """
    Report a user or message. Can be used in server channels or DMs.
    Usage: 
    - !report [user] [reason]
    - !report [message_id] [reason]
    - Reply to a message with: !report [reason]
    """
    reported_msg = None
    user = None
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        await ctx.send("Error: Couldn't find the specified server. Please contact an administrator.")
        return

    if ctx.message.reference:
        # If the command is used as a reply to a message
        try:
            reported_msg = await ctx.fetch_message(ctx.message.reference.message_id)
            user = reported_msg.author
        except discord.NotFound:
            await ctx.send("Couldn't fetch the message you're replying to. It may have been deleted.")
            return
    elif message_or_user:
        try:
            # Check if the input is a valid message ID
            message_id = int(message_or_user)
            reported_msg = await find_message_by_id(guild, message_id)
            if reported_msg:
                user = reported_msg.author
            else:
                await ctx.send("Couldn't find a message with that ID. Make sure the ID is correct and the message is from the specified server.")
                return
        except ValueError:
            # If not a message ID, treat it as a user mention or ID
            try:
                user = await bot.fetch_user(int(message_or_user))
            except (ValueError, discord.NotFound):
                try:
                    user = await commands.UserConverter().convert(ctx, message_or_user)
                except commands.UserNotFound:
                    await ctx.send("Please provide a valid user mention, user ID, or message ID.")
                    return

    if not user:
        await ctx.send("Please specify a user to report, provide a message ID, or use this command as a reply to a message.")
        return

    if not reason:
        await ctx.send("Please provide a reason for the report.")
        return

    # Here you would typically send this information to a designated channel or store it in a database
    report_channel = bot.get_channel(REPORT_CHANNEL_ID)
    
    embed = discord.Embed(title="New Report", color=discord.Color.red())
    embed.add_field(name="Reported User", value=f"{user.name}#{user.discriminator} (ID: {user.id})", inline=False)
    embed.add_field(name="Reported By", value=f"{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})", inline=False)
    
    if reported_msg:
        embed.add_field(name="Reported Message", value=reported_msg.content[:1024], inline=False)
        if len(reported_msg.content) > 1024:
            embed.add_field(name="Reported Message (continued)", value=reported_msg.content[1024:], inline=False)
        embed.add_field(name="Message ID", value=reported_msg.id, inline=False)
        embed.add_field(name="Message Link", value=reported_msg.jump_url, inline=False)
        embed.add_field(name="Channel", value=reported_msg.channel.name, inline=False)
    
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Report Source", value="DM" if isinstance(ctx.channel, discord.DMChannel) else "Server Channel", inline=False)
    embed.add_field(name="Server", value=guild.name, inline=False)

    await report_channel.send(embed=embed)
    await ctx.send("Thank you for your report. It has been submitted for review.")

async def find_message_by_id(guild, message_id):
    """
    Search for a message by its ID in all channels of the given server.
    """
    for channel in guild.text_channels:
        try:
            message = await channel.fetch_message(message_id)
            return message
        except discord.NotFound:
            continue
    return None

@bot.tree.command(name="report_info", description="Get information on how to report anonymously")
async def report_info(interaction: discord.Interaction):
    """Provides information on how to report anonymously and get message IDs."""
    
    instructions = (
        "To report anonymously:\n\n"
        "1. Send a DM to the bot with the following format:\n"
        "   `!report [user_id or message_id] [reason]`\n\n"
        "2. To get a user's ID, right-click their name and select 'Copy ID'. "
        "You need to have Developer Mode enabled in Discord settings.\n\n"
        "3. To get a message ID:\n"
        "   - Enable Developer Mode in Discord settings (User Settings > App Settings > Advanced)\n"
        "   - Right-click on the message and select 'Copy Message ID'\n\n"
        "4. When reporting a message, use the message ID instead of the user ID.\n\n"
        "Example:\n"
        "`!report 123456789 Inappropriate behavior`\n\n"
        "Remember, all reports are confidential and anonymous when sent via DM."
    )

    try:
        await interaction.user.send(instructions)
        await interaction.response.send_message("Instructions have been sent to your DMs.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I couldn't send you a DM. Please check your privacy settings and try again.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.run(BOT_TOKEN)
