import discord
from discord.ext import commands
import asyncio
import config_handler as config
import os

# Bot-Setup
TOKEN = "DEIN_DISCORD_BOT_TOKEN"
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def join(ctx):
    """Der Bot tritt dem Sprachkanal bei."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        await ctx.send(f"Bin dem Kanal {channel} beigetreten!")
    else:
        await ctx.send("Du bist in keinem Sprachkanal!")

@bot.command()
async def leave(ctx):
    """Der Bot verlässt den Sprachkanal."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Verlassen!")
    else:
        await ctx.send("Ich bin in keinem Sprachkanal!")

@bot.command()
async def record(ctx):
    """Startet die Audioaufnahme."""
    if not ctx.voice_client:
        await ctx.send("Ich bin nicht in einem Sprachkanal!")
        return

    voice_client = ctx.voice_client

    if not voice_client.is_connected():
        await ctx.send("Ich bin nicht verbunden!")
        return

    # Datei vorbereiten
    audio_filename = f"recording_{ctx.channel.id}.mp3"
    if os.path.exists(audio_filename):
        os.remove(audio_filename)

    # Sprachaufnahmen beginnen
    def audio_callback(raw_audio):
        with open(audio_filename, "ab") as f:
            f.write(raw_audio)

    voice_client.listen(discord.AudioSink(callback=audio_callback))
    await ctx.send("Aufnahme gestartet!")

@bot.command()
async def stop(ctx):
    """Stoppt die Aufnahme."""
    if ctx.voice_client and ctx.voice_client.is_connected():
        ctx.voice_client.stop_listening()
        await ctx.send("Aufnahme gestoppt und gespeichert!")
    else:
        await ctx.send("Ich nehme gerade nicht auf!")

bot.run(config.get()["discord_token"])
