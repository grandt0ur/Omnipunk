import discord
from discord import Option
from discord.ext import commands
import os
import datetime
from datetime import datetime
import random
import pprint
import requests

my_secret = os.environ['DISCORD_BOT_SECRET']

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("."),
                   intents=intents)


async def timeout_user(*, user_id: int, guild_id: int, until):
  headers = {"Authorization": f"Bot {bot.http.token}"}
  url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
  timeout = (datetime.datetime.utcnow() +
             datetime.timedelta(minutes=until)).isoformat()
  json = {'communication_disabled_until': timeout}
  async with bot.session.patch(url, json=json, headers=headers) as session:
    if session.status in range(200, 299):
      return True
    return False


bot.remove_command('help')


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user} (ID: {bot.user.id})')
  print('------')
  await bot.change_presence(activity=discord.Activity(
    type=discord.ActivityType.watching,
    name=
    f'{len(bot.guilds)} servers | {len(bot.users)} users | Type ?help or tag me with help for commands'
  ))


@bot.command()
async def gotcha(ctx):
  """Destinys Qoute"""
  await ctx.send('Anything Else?')


@bot.command()
async def test1(ctx):
  """My Jokes"""
  await ctx.send(
    'I cant wait to see what cosmic horrors i will face in NeoPunkFMs Discord')


@bot.command()
async def help(ctx):
  await ctx.send('Currently Working on this')


@bot.command()
async def clr(ctx, num: int = 10):
  if num > 500 or num < 0:
    await ctx.send(f"**❌ Invalid Amount Maximum 500**")
  else:
    await ctx.channel.purge(limit=num)
    await ctx.send(f"**Sucsses Delete `{num}` message**")


@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, until: int):
  handshake = await timeout_user(user_id=member.id,
                                 guild_id=ctx.guild.id,
                                 until=until)
  if handshake:
    return await ctx.send(f"Successfully timed out user for {until} minutes.")
  await ctx.send("Something went wrong")


bot.run(MTA5MTc3NTM4NzI0OTQyMjU0OA.Gls_CG.cFFV4WwXP8v1t1pjSM8CY_P9Gez0_7eYP59-Vg)
