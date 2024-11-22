import os
try:
    import subprocess
    import json
    import discord
    from discord.ext import commands
    from discord import app_commands
    from flask import Flask, request, jsonify, render_template
    import asyncio
    import threading
    from werkzeug.security import generate_password_hash, check_password_hash
    from getpass import getpass
    from flask_httpauth import HTTPBasicAuth
    import json
    from lang_handler import LangHandler
    import config_handler as config
except ImportError:
    os.system("pip3 install -r requirements.txt")

if not os.path.exists("./sounds"):
    os.makedirs("sounds")

# if you want to change this don't forget to change it in the config_handler.py
CONFIG_FILE = os.path.join("config", "config.json")

if not os.path.exists(CONFIG_FILE):
    guildid = int(input('Enter Audio Guild ID: '))
    channelid = int(input('Enter Audio Channel ID: '))
    autojoin = bool(
        input('Should the bot join automatically on startup? (Default: True): ')) or True
    token = input('Enter Bot Token: ')
    sounds_dir = input(
        'How should the folder with the sounds in it be called? ')
    ipv4 = input('Bind IPv4? (Default: 0.0.0.0): ') or '0.0.0.0'
    port = int(input('Enter Port (Default: 5000): ') or 5000)
    user = input('Enter Username (Default: admin): ') or 'admin'
    pw = getpass('Enter Password: ')
    lang = input(
        'Which language should the Bot speak? (check folder called >lang<; Default: en): ') or "en"
    CUSTOM_CONFIG = {
        "soundboard": {
            "sound_files": {},
            "sounds_dir": f"{sounds_dir}",
            "guild_id": f"{guildid}",
            "channel_id": f"{channelid}",
            "auto_join": autojoin,
            "volume": 1
        },
        "customization": {
            "avatar": "./config//avatar.png",
            "name": "Change me in the config.json"
        },
        "discord_token": f"{token}",
        "flask": {
            "host": f"{ipv4}",
            "port": port,
            "username": f"{user}",
            "password": pw
        },
        "lang": lang,
        "lang_dir": "lang",
        "interface_lang_dir": "./interface/lang/"
    }
    pw = None
    with open(CONFIG_FILE, 'w') as f:
        f.write(json.dumps(CUSTOM_CONFIG))
    exit(0)


async def change_user(pfp_location, name):
    for guild in bot.guilds:
        try:
            await guild.me.edit(nick=name)
            print(f"Nickname geändert auf {guild.name} in guild: {guild.name}")
        except Exception as e:
            print(f"Fehler beim Ändern des Nicknames in {guild.name}: {e}")
    with open(pfp_location, 'rb') as avatar_file:
        avatar_data = avatar_file.read()
        await bot.user.edit(avatar=avatar_data, username=name)
    print("User profile changed!")


def add_sounds_from_directory():
    tmp = config.get()
    sounds_directory = str(tmp["soundboard"]["sounds_dir"])

    for filename in os.listdir(sounds_directory):
        if filename.endswith('.mp3'):
            sound_name = os.path.splitext(filename)[0]
            sound_path = os.path.join(sounds_directory, filename)

            if filename not in str(tmp["soundboard"]["sound_files"]):
                config.set(f"soundboard/sound_files/{sound_name}", sound_path)

    sounds = tmp["soundboard"]["sound_files"].items()

    keys_to_delete = [sound_name for sound_name,
                      sound_path in sounds if not os.path.exists(sound_path)]

    for key in keys_to_delete:
        del tmp["soundboard"]["sound_files"][key]

    config.save(config)


lang_manager = LangHandler(config.get()["lang"])

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if username == config.get()["flask"]["username"] and config.get()["flask"]["password"] == password:
        return username
    return None


# Discord-Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Flask App Setup
app = Flask(__name__, static_folder='interface/public')


@app.route('/')
@auth.login_required
def index():
    return app.send_static_file('index.html')


@app.route('/api/sounds', methods=['GET'])
@auth.login_required
def get_sounds():
    return config.get()["soundboard"]["sound_files"]


@app.route('/api/sounds/add', methods=['POST'])
@auth.login_required
def add_sound():
    data = request.json
    name = data.get('name')
    path = data.get('path')
    if name and path:
        config.set(f"soundboard/sound_files/{name}", path)
        return jsonify({"message": "Sound added."})
    return jsonify({"message": "Invalid input."}), 400


@app.route('/api/sounds/remove', methods=['POST'])
@auth.login_required
def remove_sound():
    data = request.json
    name = data.get('name')
    if name in config.get()["soundboard"]["sound_files"]:
        config.remove(f"soundboard/sound_files/{name}")
        return jsonify({"message": "Sound removed."})
    return jsonify({"message": "Sound not found."}), 404


@app.route('/api/sounds/rename', methods=['POST'])
@auth.login_required
def rename_sound():
    data = request.json
    old_name = data.get('oldName')
    new_name = data.get('newName')
    if old_name in config.get()["soundboard"]["sound_files"] and new_name not in config.get()["soundboard"]["sound_files"]:
        config.set(f"soundboard/sound_files/{new_name}",
                   config.get()["soundboard"]["sound_files"][old_name])
        config.remove(f"soundboard/sound_files/{old_name}")
        return jsonify({"message": "Sound renamed."})
    return jsonify({"message": "Invalid input or name already exists."}), 400


@app.route('/api/sounds/play', methods=['POST'])
@auth.login_required
def play_sound():
    data = request.json
    name = data.get('name')
    if name in config.get()["soundboard"]["sound_files"]:
        guild_id = config.get()["soundboard"]["guild_id"]
        asyncio.run_coroutine_threadsafe(
            play_sound_coroutine(guild_id, name), bot.loop)
        return jsonify({"message": "Playing sound."})
    return jsonify({"message": "Sound not found."}), 404


async def play_sound_coroutine(guild_id, sound_name):
    guild = bot.get_guild(int(guild_id))
    if guild and guild.voice_client:
        source = discord.FFmpegPCMAudio(
            config.get()["soundboard"]["sound_files"][sound_name],
            options=f'-filter:a "volume={config.get()["soundboard"]["volume"]}"'
        )
        guild.voice_client.play(source)


@app.route('/api/channel/join', methods=['POST'])
@auth.login_required
def join_channel_api():
    data = request.json
    guild_id = data.get('guild_id', config.get()["soundboard"]["guild_id"])
    channel_id = data.get('channel_id', config.get()[
                          "soundboard"]["channel_id"])
    asyncio.run_coroutine_threadsafe(
        join_channel_coroutine(guild_id, channel_id), bot.loop)
    return jsonify({"message": "Joining channel."})


async def join_channel_coroutine(guild_id, channel_id):
    guild = bot.get_guild(int(guild_id))
    if guild:
        channel = guild.get_channel(int(channel_id))
        if channel:
            if not guild.voice_client:
                try:
                    await channel.connect()
                    print(f"Successfully joined channel {channel_id}")
                except Exception as e:
                    print(f"Failed to join channel: {e}")
            else:
                print("Bot is already connected to a voice channel.")
        else:
            print(f"Channel with ID {channel_id} not found.")
    else:
        print(f"Guild with ID {guild_id} not found.")


@app.route('/api/channel/leave', methods=['POST'])
@auth.login_required
def leave_channel_api():
    data = request.json
    guild_id = data.get('guild_id', config.get()["soundboard"]["guild_id"])
    asyncio.run_coroutine_threadsafe(
        leave_channel_coroutine(guild_id), bot.loop)
    return jsonify({"message": "Leaving channel."})


@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    guild = bot.get_guild(int(config.get()["soundboard"]["guild_id"]))
    if guild and guild.voice_client and guild.voice_client.is_connected():
        return jsonify({"status": True})
    else:
        return jsonify({"status": False})


async def leave_channel_coroutine(guild_id):
    guild = bot.get_guild(int(guild_id))
    if guild and guild.voice_client:
        await guild.voice_client.disconnect()
        print(f"Disconnected from channel in guild {guild_id}")
    else:
        print(f"No active voice client in guild {guild_id}")


@app.route('/api/settings', methods=['POST'])
@auth.login_required
def update_settings():
    data = request.json
    guild_id = data.get('guild_id')
    channel_id = data.get('channel_id')
    if guild_id and channel_id:
        config.set("soundboard/guild_id", guild_id)
        config.set("soundboard/channel_id", channel_id)
        return jsonify({"message": "Settings updated."})
    return jsonify({"message": "Invalid input."}), 400


@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({
        "guild_id": config.get()["soundboard"]["guild_id"],
        "channel_id": config.get()["soundboard"]["channel_id"]
    })


@app.route('/api/sounds/stop', methods=['POST'])
@auth.login_required
def stop_sound():
    guild_id = config.get()["soundboard"]["guild_id"]
    asyncio.run_coroutine_threadsafe(stop_sound_coroutine(guild_id), bot.loop)
    return jsonify({"message": "Stopping sound."})


async def stop_sound_coroutine(guild_id):
    guild = bot.get_guild(int(guild_id))
    if guild and guild.voice_client:
        guild.voice_client.stop()
        print(f"Stopped sound in channel for guild {guild_id}")


@app.route('/api/sounds/upload', methods=['POST'])
@auth.login_required
def upload_sound():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.mp3'):
        filename = file.filename
        filepath = os.path.join(
            config.get()["soundboard"]["sounds_dir"], filename)
        file.save(filepath)

        sound_name = os.path.splitext(filename)[0]
        config.set(f"soundboard/sound_files/{sound_name}", filepath)

        return jsonify({'message': 'File uploaded successfully'}), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/sounds/volume', methods=['POST'])
@auth.login_required
def set_volume():
    data = request.json
    volume = int(data.get('volume', 100))

    volume_level = volume / 100

    config.set("soundboard/volume", volume_level)

    return jsonify({"message": f"Volume set to {volume}%"})


@app.route('/api/lang', methods=['GET'])
@auth.login_required
def get_language():
    lang = config.get()["lang"]
    lang_file = os.path.join(
        config.get()["interface_lang_dir"], f'{lang}.json')

    if os.path.exists(lang_file):
        with open(lang_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Language file not found"}), 404


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await change_user(config.get()["customization"]["avatar"], config.get()["customization"]["name"])
    add_sounds_from_directory()

    if (config.get()["soundboard"]["auto_join"]):
        print(f"Joining: " + config.get()["soundboard"]["channel_id"])
        await join_channel_coroutine(guild_id=config.get()["soundboard"]["guild_id"], channel_id=config.get()["soundboard"]["channel_id"])

    # Register all commands globally on all servers
    try:
        await bot.tree.sync()
        print("Slash commands synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Define slash commands:
@bot.tree.command(name='play', description="Plays a provided sound.")
async def play(interaction: discord.Interaction, sound_name: str):
    guild_id = interaction.guild.id
    try:
        await play_sound_coroutine(guild_id, sound_name)
    except Exception as e:
        await interaction.response.send_message(lang_manager("commands.play.404", sound_name), ephemeral=True)
        return
    await interaction.response.send_message(f"Playing sound: {sound_name}")

@play.autocomplete('sound_name')
async def play_cmd_autocomplete(interaction: discord.Interaction, current: str):
    sounds = []
    for sound in config.get()["soundboard"]["sound_files"]:
        sounds.append(sound)
        
    filtered = [sound for sound in sounds if current.lower() in sound.lower()]
    return [discord.app_commands.Choice(name=sound, value=sound) for sound in filtered]
    


@bot.tree.command(name="add_sound", description="Upload an MP3 file to save it to the sounds directory.")
async def add_sound_cmd(interaction: discord.Interaction, file: discord.Attachment):
    # Check if the file is an MP3
    if not file.filename.lower().endswith('.mp3'):
        await interaction.response.send_message(lang_manager("commands.add.fileformat"), ephemeral=True)
        return

        # Save the file
    try:
        file_path = f"./sounds/{file.filename}"
        await file.save(file_path)
        await interaction.response.send_message(lang_manager("commands.add.success", file.filename))
    except Exception as e:
        await interaction.response.send_message(lang_manager("commands.add.error", e), ephemeral=True)


@bot.tree.command(name='stop', description="Stops the current sound.")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    await stop_sound_coroutine(guild_id)
    await interaction.response.send_message("Sound stopped.")


@bot.tree.command(name='volume', description="Sets the volume in %")
async def set_volume_cmd(interaction: discord.Interaction, new_volume_level: int = 100):
    config.set("soundboard/volume", new_volume_level / 100)
    await interaction.response.send_message(f"Volume set to {config.get()["soundboard"]["volume"] * 100}%")


@bot.tree.command(name='join', description="Joins the provided channelid/Your channel")
async def join(interaction: discord.Interaction, channel_id: str = None):
    if channel_id:
        channel_id = channel_id.strip('<>#')
        try:
            guild_id = interaction.guild.id
            await join_channel_coroutine(guild_id, channel_id)
            await interaction.response.send_message(lang_manager("commands.join.success", channel_id))
        except Exception as e:
            print(f"An error occurred: {e}")

    else:
        if interaction.user.voice and interaction.user.voice.channel:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message(lang_manager("commands.join.success", channel.id))
        else:
            await interaction.response.send_message("You are not connected to a voice channel and no channel ID was provided.", ephemeral=True)


@bot.tree.command(name='leave', description="Disconnects the bot from the current voice channel.")
async def leave(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    await leave_channel_coroutine(guild_id)
    await interaction.response.send_message("Left the voice channel.")


@bot.tree.command(name='list', description="Lists all sounds.")
async def list(interaction: discord.Interaction):
    sound_names = config.get()["soundboard"]["sound_files"].keys()
    embed = discord.Embed(title="Available Sounds", color=discord.Color.blue())

    embed.description = "\n".join(sound_names)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="language")
async def language(interaction: discord.Interaction, lang: str = None):
    if (lang):
        available_langs = os.listdir(config.get()["lang_dir"])
        if (lang + ".json" in available_langs):
            config.set("lang", lang)
            global lang_manager
            lang_manager = LangHandler(lang)
            await interaction.response.send_message(content=lang_manager("commands.language.success"))
        else:
            print(f"{lang} is not in {available_langs}")
    else:
        await interaction.response.send_message(content=lang_manager("commands.language.lang_empty", str(os.listdir(config.get()["lang_dir"]))), ephemeral=True)


def run_flask_app():
    from waitress import serve
    serve(app, host=config.get()["flask"]["host"],
          port=config.get()["flask"]["port"])
    


if __name__ == '__main__':
    watchdog_process = subprocess.Popen(['python3', 'watchdog_script.py'])

    try:
        threading.Thread(target=run_flask_app).start()
        bot.run(config.get()["discord_token"])
    finally:
        watchdog_process.terminate()
