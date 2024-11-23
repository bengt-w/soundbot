import discord
from discord.ext import commands

# Bot-Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot ist bereit! Eingeloggt als {bot.user}")

@bot.command()
async def embed(ctx):
    # Erstelle einen Embed
    embed = discord.Embed(
        title="Mittelgroße Überschrift",
        description="Hier ist ein Embed mit drei Zeilen darunter:",
        color=discord.Color.blue()  # Farbe des Embeds
    )
    
    # Drei Zeilen als Felder hinzufügen
    embed.add_field(name="Zeile 1", value="Das ist die erste Zeile.", inline=False)
    embed.add_field(name="Zeile 2", value="Das ist die zweite Zeile.", inline=False)
    embed.add_field(name="Zeile 3", value="Das ist die dritte Zeile.", inline=False)
    
    # Sende den Embed
    await ctx.send(embed=embed)

import config_handler
bot.run(config_handler.get()["discord_token"])