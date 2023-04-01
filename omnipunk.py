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
async def clr(ctx , num : int = 10):
  if num > 500 or num < 0:
    await ctx.send(f"**❌ Invalid Amount Maximum 500**")
  else:
    await ctx.channel.purge(limit = num)
    await ctx.send(f"**Sucsses Delete `{num}` message**")


bot.run(my_secret)
