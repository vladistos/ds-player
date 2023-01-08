from discord.ext import commands
import discord
import wavelink
from cogs.youtube_player import YoutubePlayer
from cogs.vk import VkPlayer
from cogs.music_control import MusicControl
import cogs.music_base

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(intents=intents)

bot.add_cog(MusicControl())


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


# bot.add_cog(cogs.vk_cog.VkCog())

bot.run('')
