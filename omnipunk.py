import discord
import os
import datetime
import aiofiles
from datetime import datetime as dt
from asyncio import sleep as s
import aiohttp
import discord
import warnings
from discord.ext import commands
warnings.filterwarnings("ignore", category=DeprecationWarning)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(command_prefix=commands.when_mentioned_or("."),
                   intents=intents)
bot.remove_command('help')
bot.session = aiohttp.ClientSession()
bot.warnings = {} # guild_id : {member_id: [count, [(admin_id, reason)]]}
bot.sniped_messages = {}
day = dt.now()

@bot.event
async def on_ready():
    for guild in bot.guilds:
        bot.warnings[guild.id] = {}

        async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    bot.warnings[guild.id][member_id][0] += 1
                    bot.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    bot.warnings[guild.id][member_id] = [1, [(admin_id, reason)]]
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name= f'{len(bot.guilds)} servers | {len(bot.users)} users | Type ?help or tag me with help for commands'))


@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}


@bot.command(pass_context=True, aliases=['w'])
@commands.has_any_role("Jannies", "moderator")
async def warn(ctx, member: discord.Member = None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    if reason is None:
        return await ctx.send("Please provide a reason for warning this user.")

    try:
        first_warning = False
        bot.warnings[ctx.guild.id][member.id][0] += 1
        bot.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

    except KeyError:
        first_warning = True
        bot.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = bot.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")
    await member.send(f"You have been warned by {ctx.message.author}")


@bot.command(pass_context=True, aliases=['ws'])
async def warns(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.red())
    try:
        i = 1
        for admin_id, reason in bot.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await member.send(embed=embed)

    except KeyError:  # no warnings
        await ctx.send("This user has no warnings...yet")


@bot.event
async def on_message_delete(message):
    bot.sniped_messages[message.guild.id] = (message.content, message.author, message.channel.name, message.created_at)


@bot.command(pass_context=True, aliases=['s'])
@commands.has_any_role("Jannies", "moderator")
async def snipe(ctx):
    try:
        contents, author, channel_name, time = bot.sniped_messages[ctx.guild.id]

    except:
        await ctx.channel.send("Couldn't find a message to snipe!")
        return

    embed = discord.Embed(description=contents, color=discord.Color.purple(), timestamp=time)
    embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar_url)
    embed.set_footer(text=f"Deleted in : #{channel_name}")

    await ctx.channel.send(embed=embed)

@bot.command()
async def gotcha(ctx):
  """Destinys Qoute"""
  await ctx.send('Anything Else?')


@bot.command()
async def test1(ctx):
  """My Jokes"""
  await ctx.send(
    'I cant wait to see what cosmic horrors i will face in NeoPunkFMs Discord')


@bot.command(pass_context=True, aliases=['h'])
async def help(ctx, member: discord.Member,):
    hlpembed=discord.Embed(title="Help Menu", colour=discord.Colour.blue())
    hlpembed.add_field(name="mute / m", value="Mutes users for specified amount of time (a Reason is Required)", inline=False)
    hlpembed.add_field(name="ex:", value=" .mute @you 10 lame-ass user", inline=False)
    hlpembed.add_field(name="unmute / um", value="Unmutes users",
                       inline=False)
    hlpembed.add_field(name="ex:", value=" .unmute @you", inline=False)
    hlpembed.add_field(name="clr / clear", value="This clears the chat the command is run in. limit is 10,000",
                       inline=False)
    hlpembed.add_field(name="ex:", value=" .clr 100", inline=False)
    hlpembed.add_field(name="warn / w", value="This gives the user a warning",
                       inline=False)
    hlpembed.add_field(name="ex:", value=" .warn 100", inline=False)
    hlpembed.add_field(name="warns / ws", value="This gives the number, reasons, and mod who issued a specific warn",
                       inline=False)
    hlpembed.add_field(name="ex:", value=" .ws @jupiter", inline=False)
    hlpembed.add_field(name="snipe / s", value="This snipes the users last message",
                       inline=False)
    hlpembed.add_field(name="ex:", value=" .snipe", inline=False)
    await member.send(hlpembed)
    await ctx.send(f"Successfully sent help to {member}.")


@bot.command(pass_context=True, aliases=['cls', 'clear'])
@commands.has_any_role("Jannies", "moderator")
async def clr(ctx, num: int = 10):
  if num > 10000 or num < 0:
    await ctx.send(f"**❌ Invalid Amount Maximum 500**")
  else:
    await ctx.channel.purge(limit=num)
    await ctx.send(f"**Sucsses Delete `{num}` message**")

@bot.command()
async def userinfo(ctx: commands.Context, user: discord.User):
    # In the command signature above, you can see that the `user`
    # parameter is typehinted to `discord.User`. This means that
    # during command invocation we will attempt to convert
    # the value passed as `user` to a `discord.User` instance.
    # The documentation notes what can be converted, in the case of `discord.User`
    # you pass an ID, mention or username (discrim optional)
    # E.g. 80088516616269824, @Danny or Danny#0007

    # NOTE: typehinting acts as a converter within the `commands` framework only.
    # In standard Python, it is use for documentation and IDE assistance purposes.

    # If the conversion is successful, we will have a `discord.User` instance
    # and can do the following:
    user_id = user.id
    username = user.name
    avatar = user.display_avatar.url
    await ctx.send(f'User found: {user_id} -- {username}\n{avatar}')

@bot.command(pass_context=True, aliases=['m'])
@commands.has_any_role("Jannies", "moderator")
async def mute(ctx, member: discord.Member, time : int, *, reason=None):
    guild = ctx.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")
    if not mutedRole:
        mutedRole = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    embed = discord.Embed(title="Mute Report", description=f"{member.mention} was muted for {time} Hours ",
                          colour=discord.Colour.blue())
    embed.set_thumbnail(url=member.avatar)
    embed.add_field(name="Report Generated by :", value=f"{ctx.message.author.mention}", inline=False)
    embed.add_field(name="Actual Mute Duration :", value=f"{time*60} Minutes", inline=False)
    embed.add_field(name="reason:", value=reason, inline=False)
    embed.set_footer(text="Bot Coded by fate")
    await bot.get_channel(1086126239619751986).send(embed=embed)
    await member.add_roles(mutedRole, reason=reason)
    await member.send(f" you have been muted from: {guild.name} {ctx.message. author} for {time} hour(s)\n reason: {reason}. If this mute goes over 1day contact kismet#0005")
    await ctx.message.delete()
    await s(time*60)
    await member.remove_roles(mutedRole)


@bot.command(pass_context=True, aliases=['u', 'um'])
@commands.has_any_role("Jannies", "moderator")
async def unmute(ctx, member: discord.Member):
    guild = ctx.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")
    if mutedRole in member.roles:
        await member.remove_roles(mutedRole)
        await ctx.send(f"You have unmuted {member.mention} from: {guild.name}")
        await member.send(f"You have been unmuted from: {guild.name}. Remember to follow the rules my creator made them and im sure he was specific for a reason")
    else:
        await ctx.send("This user was never even muted, goofy!!!1")

@bot.command(pass_context=True, aliases=['a', 'announce'])
@commands.has_any_role("Jannies", "moderator")
async def ann(ctx, *, message = None):
    channel = discord.utils.get(ctx.guild.text_channels, name="announcements")
    if message == None and channel == NotImplemented:
        await ctx.send(f"{ctx.message.author} you need to provide a message. Or else you are wasting my time")
        return
    else :
        embed2=discord.Embed(title='Announcements')
        embed2.add_field(name="", value=f"{message}")
        embed2.set_footer(text=f"Announced by {ctx.message.author}")
        await bot.get_channel(1073393397609529466).send('@everyone', embed=embed2)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Hey you know that a: '{str(error)}'")

  bot.run("TOKEN HERE")
