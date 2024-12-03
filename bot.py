import os
try:
    import subprocess
    from datetime import datetime
    import json
    import discord
    from discord.ext import commands
    from discord import app_commands
    from flask import Flask, request, jsonify, render_template, request
    import asyncio
    import threading
    from werkzeug.security import generate_password_hash, check_password_hash
    from getpass import getpass
    from flask_httpauth import HTTPBasicAuth
    import json
    import random
    from lang_handler import LangHandler
    import config_handler as config
    from user_handler import validate_authcode, gen_authcode
    from log_handler import log as logger
except ImportError:
    print("Please install the dependencies with:")
    print("")
    print("pip install -r requirements.txt")
    print("")
    print("And then restart the bot.")

sounds_dir = config.get()["soundboard"]["sounds_dir"]

if not os.path.exists(sounds_dir):
    os.makedirs(sounds_dir)

# if you want to change this don't forget to change it in the config_handler.py
CONFIG_FILE = os.path.join("config", "config.json")


async def change_user(pfp_location, name):
    for guild in bot.guilds:
        try:
            await guild.me.edit(nick=name)
            print(f"Nickname geändert auf {guild.name} in guild: {guild.name}")
        except Exception as e:
            print(f"Fehler beim Ändern des Nicknames in {guild.name}: {e}")
    if os.path.exists(pfp_location):
        with open(pfp_location, 'rb') as avatar_file:
            avatar_data = avatar_file.read()
            await bot.user.edit(avatar=avatar_data, username=name)
    else:
        print("Avatar file not found.")
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
    if validate_authcode(username, password):
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
    logger("/index.html", user=request.authorization.username, method="GET")
    return app.send_static_file('index.html')


@app.route('/api/sounds', methods=['GET'])
@auth.login_required
def get_sounds():
    logger("/api/sounds", user=request.authorization.username, method="GET")
    sounds = {
                "Sound 1": None,
                "Sound 2": None,
                "Sound 3": None,
                "Sound 4": None,
                "Sound 5": None,
            }
    if config.get()["demo_mode"]:
        return sounds
    return config.get()["soundboard"]["sound_files"]


@app.route('/api/sounds/add', methods=['POST'])
@auth.login_required
def add_sound():
    data = request.json
    name = data.get('name')
    path = data.get('path')
    logger(f"/api/sounds/add {name}@{path}",
           user=request.authorization.username, method="POST")
    if name and path:
        config.set(f"soundboard/sound_files/{name}", path)
        return jsonify({"message": "Sound added."})
    return jsonify({"message": "Invalid input."}), 400


@app.route('/api/sounds/remove', methods=['POST'])
@auth.login_required
def remove_sound():
    data = request.json
    name = data.get('name')
    logger(f"/api/sounds/remove {name}",
           user=request.authorization.username, method="POST")
    if name in config.get()["soundboard"]["sound_files"]:
        config.remove(f"soundboard/sound_files/{name}")
        try:
            os.remove(config.get()["soundboard"]["sound_files"][name])
        except Exception as e:
            print(e)
        return jsonify({"message": "Sound removed."})
    return jsonify({"message": "Sound not found."}), 404


@app.route('/api/sounds/rename', methods=['POST'])
@auth.login_required
def rename_sound():
    data = request.json
    old_name = data.get('oldName')
    new_name = data.get('newName')
    logger(f"/api/sounds/rename '{old_name}' > '{new_name}'",
           user=request.authorization.username, method="POST")
    if old_name in config.get()["soundboard"]["sound_files"] and new_name not in config.get()["soundboard"]["sound_files"]:
        config.set(f"soundboard/sound_files/{new_name}",
                   config.get()["soundboard"]["sound_files"][old_name])
        config.remove(f"soundboard/sound_files/{old_name}")
        return jsonify({"message": "Sound renamed."})
    return jsonify({"message": "Invalid input or name already exists."}), 400

@app.route('/api/sounds/random', methods=['POST'])
@auth.login_required
async def random_sound():
    usernames = []
    for user in bot.get_channel(int(config.get()["soundboard"]["channel_id"])).members:
        usernames.append(user.name)
    if request.authorization.username not in usernames:
            return "You are not in the channel.", 403
    random_sound = await rand_sound(config.get()["soundboard"]["guild_id"])
    if random_sound == "error":
        logger(f"/api/sounds/random Already playing", user=request.authorization.username, method="POST", level="ERROR")
        return jsonify({"message": "Already playing"})
    logger(f"/api/sounds/random {rand_sound}", user=request.authorization.username, method="POST")
    return jsonify({"message": random_sound})

@app.route('/api/sounds/play', methods=['POST'])
@auth.login_required
def play_sound():
    usernames = []
    for user in bot.get_channel(int(config.get()["soundboard"]["channel_id"])).members:
        usernames.append(user.name)
    if request.authorization.username in usernames:
        data = request.json
        name = data.get('name')
        if name in config.get()["soundboard"]["sound_files"]:
            guild_id = config.get()["soundboard"]["guild_id"]
            if bot.get_guild(int(guild_id)).voice_client.is_playing():
                queue = config.get()["soundboard"]["queue"]
                queue.append(name)
                config.set("soundboard/queue", queue)
                logger(f"/api/sounds/play {name} (queued)",
                       user=request.authorization.username, method="POST")
                return jsonify({"message": "Sound added to queue."})
            logger(f"/api/sounds/play {name}",
                   user=request.authorization.username, method="POST")
            asyncio.run_coroutine_threadsafe(
                play_sound_coroutine(guild_id, name), bot.loop)
            return jsonify({"message": "Playing sound."})
        else:
            return jsonify({"message": "Sound not found."}), 404
            logger("/api/sounds/play 404", user=request.authorization.username,
                   level="ERROR", method="POST")
    else:
        return "You are not in the voice channel.", 403

async def play_sound_coroutine(guild_id, sound_name):
    guild = bot.get_guild(int(guild_id))
    if guild and guild.voice_client:
        def loop_n_queue_starter(error=None):
            config.set("soundboard/current", "")
            asyncio.run_coroutine_threadsafe(loop(guild_id), bot.loop)
            

        source = discord.FFmpegPCMAudio(
            config.get()["soundboard"]["sound_files"][sound_name],
            options=f'-filter:a "volume={config.get()["soundboard"]["volume"]}"'
        )
        config.set("soundboard/current", sound_name)
        guild.voice_client.play(source, after=loop_n_queue_starter)

async def loop(guild_id):
    if config.get()["soundboard"]["loop"] != "":
        await play_sound_coroutine(guild_id, config.get()["soundboard"]["loop"])
    elif config.get()["soundboard"]["queue"] != []:
        await play_sound_coroutine(guild_id, config.get()["soundboard"]["queue"][0])
        config.set("soundboard/queue", config.get()["soundboard"]["queue"][1:])
        pass

@app.route('/api/channel/join', methods=['POST'])
@auth.login_required
def join_channel_api():
    data = request.json
    guild_id = data.get('guild_id')
    channel_id = data.get('channel_id')
    asyncio.run_coroutine_threadsafe(
            join_channel_coroutine(guild_id, channel_id), bot.loop
    )
    logger(f"/api/channel/join {channel_id}@{guild_id}",
           user=request.authorization.username, method="POST")
    return jsonify({"message": "Joining channel."})


async def join_channel_coroutine(guild_id, channel_id):
    guild = bot.get_guild(int(guild_id))
    if guild:
        channel = guild.get_channel(int(channel_id))
        if channel:
            if not guild.voice_client:
                try:
                    await channel.connect()
                    if not config.get()["developement_mode"]:
                        await play_sound_coroutine(guild_id, "join")
                    print(f"Successfully joined channel {channel_id}")
                except Exception as e:
                    print(f"Failed to join channel: {e}")
            else:
                await leave_channel_coroutine(guild_id)
                await join_channel_coroutine(guild_id, channel_id)
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
        leave_channel_coroutine(guild_id), bot.loop
    )
    logger(f"/api/channel/leave {guild_id}",
           user=request.authorization.username, method="POST")
    return jsonify({"message": "Leaving channel."})

@app.route('/api/sounds/queue', methods=['GET'])
@auth.login_required
def queue_api():
    return jsonify(config.get()["soundboard"]["queue"])

@app.route('/api/bot/status', methods=['GET'])
@auth.login_required
def bot_status():
    if config.get()["demo_mode"]:
        return jsonify({"status": True,
                        "volume": 100,
                        "sound_count": 5,
                        "queue": [],
                        "loop": "Sound 1",
                        "lang": "en"})
    else: 
        current_config = config.get()
        guild = bot.get_guild(int(config.get()["soundboard"]["guild_id"]))
        status = False
        if guild and guild.voice_client and guild.voice_client.is_connected():
            status = True
        return jsonify({"status": status,
                        "volume": current_config["soundboard"]["volume"],
                        "sound_count": len(current_config["soundboard"]["sound_files"]),
                        "queue": current_config["soundboard"]["queue"],
                        "current": current_config["soundboard"]["current"],
                        "loop": current_config["soundboard"]["loop"],
                        "lang": current_config["lang"]
                        })


@app.route('/api/servers', methods=['GET'])
@auth.login_required
def get_servers():
    if config.get()["demo_mode"]:
        return jsonify([{"id": 0, "name": "Test Server"}])
    servers = []
    for guild in bot.guilds:
        servers.append({"id": str(guild.id), "name": guild.name})
    return jsonify(servers)


@app.route('/api/channels', methods=['POST'])
@auth.login_required
def get_channels():
    if config.get()["demo_mode"]:
        return jsonify([{"id": 0, "name": "Test Channel"}])
    data = request.json
    guild_id = int(data.get('guild_id').replace(
        "MakeTheIntAStringPleaseIHateJavaScriptWhyCantYouDeclareVariableTypes", ""))
    channels = []
    guild = bot.get_guild(guild_id)
    for channel in guild.voice_channels:
        channels.append({"id": str(channel.id), "name": channel.name})
    return jsonify(channels)


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
    if not config.get()["demo_mode"]:
        data = request.json
        guild_id = data.get('guild_id')
        channel_id = data.get('channel_id')
        if guild_id and channel_id:
            config.set("soundboard/guild_id", guild_id)
            config.set("soundboard/channel_id", channel_id)
            logger(f"/api/settings {channel_id}@{guild_id}",
                   user=request.authorization.username, method="POST")
            return jsonify({"message": "Settings updated."})
        logger("/api/settings", user=request.authorization.username, method="POST")
        return jsonify({"message": "Invalid input."}), 400
    else: 
        return jsonify({"message": "Demo mode is enabled."})


@app.route('/api/settings', methods=['GET'])
@auth.login_required
def get_settings():
    if config.get()["demo_mode"]:
        return jsonify({"guild_id": 0, "channel_id": 0})
    logger("/api/settings", user=request.authorization.username, method="GET")
    return jsonify({
        "guild_id": config.get()["soundboard"]["guild_id"],
        "channel_id": config.get()["soundboard"]["channel_id"]
    })


@app.route('/api/sounds/stop', methods=['POST'])
@auth.login_required
def stop_sound():
    logger("/api/sounds/stop", user=request.authorization.username, method="POST")
    guild_id = config.get()["soundboard"]["guild_id"]
    asyncio.run_coroutine_threadsafe(stop_sound_coroutine(guild_id), bot.loop)
    return jsonify({"message": "Stopping sound."})


async def stop_sound_coroutine(guild_id):
    guild = bot.get_guild(int(guild_id))
    config.set("soundboard/loop", "")
    if guild and guild.voice_client:
        guild.voice_client.stop()
        print(f"Stopped sound in channel for guild {guild_id}")


@app.route('/api/sounds/loop', methods=['POST'])
@auth.login_required
def loop_sound():
    data = request.json
    config.set("soundboard/loop", data.get("sound"))
    asyncio.run_coroutine_threadsafe(play_sound_coroutine(
        config.get()["soundboard"]["guild_id"], data.get("sound")), bot.loop)
    logger(f"/api/sounds/loop {data.get("sound")}",
           user=request.authorization.username, method="POST")
    return jsonify({"message": "success"})


@app.route('/api/sounds/upload', methods=['POST'])
@auth.login_required
def upload_sound():
    if 'file' not in request.files:
        logger("/api/sounds/upload Error: No file part",
               user=request.authorization.username, method="POST", level="ERROR")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        logger("/api/sounds/upload Error: No filename",
               user=request.authorization.username, method="POST", level="ERROR")
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.mp3'):
        filename = file.filename
        filepath = os.path.join(
            config.get()["soundboard"]["sounds_dir"], filename)
        file.save(filepath)

        sound_name = os.path.splitext(filename)[0]
        config.set(f"soundboard/sound_files/{sound_name}", filepath)

        logger(f"/api/sounds/upload {filename}",
               user=request.authorization.username, method="POST")
        return jsonify({'message': 'File uploaded successfully'}), 200
    else:
        logger("/api/sounds/upload Error: Invalid file type",
               user=request.authorization.username, method="POST", level="ERROR")
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/sounds/volume', methods=['POST'])
@auth.login_required
def set_volume():
    data = request.json
    volume = int(data.get('volume', 100))
    try:
        if 0 <= volume <= config.get()["soundboard"]["max_volume"]:
            volume = volume / 100
            config.set("soundboard/volume", volume)
            logger(f"/api/sounds/volume {volume*100}",
                   user=request.authorization.username, method="POST")
            return jsonify({"message": f"Volume set to {volume}%"})
        else:
            logger(f"/api/sounds/volume {volume*100}%>{config.get()['soundboard']['max_volume']}%",
                   user=request.authorization.username, method="POST", level="ERROR")
            return jsonify({"message": "Volume cant be higher than " + str(config.get()["soundboard"]["max_volume"]) + "%"})
    except Exception as e:
        pass


@app.route('/api/sounds/volume', methods=['GET'])
@auth.login_required
def get_volume():
    volume = config.get()["soundboard"]["volume"]
    max_volume = config.get()["soundboard"]["max_volume"]
    if config.get()["demo_mode"]:
        volume = 1
        max_volume = 500
    logger(f"/api/sounds/volume", user=request.authorization.username, method="GET")
    return jsonify({"volume": volume*100, "max": max_volume})


@app.route('/api/lang', methods=['GET'])
@auth.login_required
def get_language():
    lang = config.get()["lang"]
    if config.get()["demo_mode"]:
        lang = "en"
    lang_file = os.path.join(
        config.get()["interface_lang_dir"], f'{lang}.json')

    if os.path.exists(lang_file):
        with open(lang_file, 'r') as f:
            logger("/api/lang", user=request.authorization.username, method="GET")
            return jsonify(json.load(f))
    logger("/api/lang Language file not found",
           user=request.authorization.username, method="GET", level="ERROR")
    return jsonify({"error": "Language file not found"}), 404


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await change_user(config.get()["customization"]["avatar"], config.get()["customization"]["name"])
    if not config.get()["demo_mode"]:
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


@bot.tree.command(name='logincode', description="Generates a logincode.")
async def login_code(interaction: discord.Interaction):
    name = interaction.user.name
    code = gen_authcode(name)
    embed = discord.Embed(
        title=lang_manager("commands.logincode.success_embed.title"),
        description="",
        color=discord.Color.green()
    )

    embed.add_field(name=lang_manager(
        "commands.logincode.success_embed.username"), value=f"`{name}`", inline=False)
    embed.add_field(name=lang_manager(
        "commands.logincode.success_embed.code"), value=f"`{code}`", inline=False)
    embed.add_field(name=lang_manager("commands.logincode.success_embed.url"),
                    value=config.get()["flask"]["url"], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='loop', description="Loops a provided sound.")
async def loop_cmd(interaction: discord.Interaction, sound_name: str):
    config.set("soundboard/loop", sound_name)
    await interaction.response.send_message(lang_manager("commands.loop.success", sound_name))
    asyncio.run_coroutine_threadsafe(play_sound_coroutine(
        interaction.guild.id, sound_name), bot.loop)
    logger(f"commands.loop {sound_name}",
           user=interaction.user.id, location=interaction.guild.id)


@loop_cmd.autocomplete('sound_name')
async def loop_cmd_autocomlete(interaction: discord.Interaction, current: str):
    sounds = []
    for sound in config.get()["soundboard"]["sound_files"]:
        sounds.append(sound)

    filtered = [sound for sound in sounds if current.lower() in sound.lower()]
    if len(filtered) > 25:
        return [discord.app_commands.Choice(name=sound, value=sound) for sound in filtered[:25]]
    else:
        return [discord.app_commands.Choice(name=sound, value=sound) for sound in filtered]

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        await stop_sound_coroutine(member.guild.id)

@bot.tree.command(name='play', description="Plays a provided sound.")
async def play(interaction: discord.Interaction, sound_name: str):
    usernames = []
    for user in bot.get_channel(int(config.get()["soundboard"]["channel_id"])).members:
        usernames.append(user.name)
    if not interaction.user.name in usernames:
        await interaction.response.send_message(lang_manager("commands.play.not_in_channel"))
        return
    logger(f"commands.play {sound_name}",
           user=interaction.user.name, location=interaction.guild.id)
    guild_id = interaction.guild.id
    if interaction.guild.voice_client.is_playing():
        queue = config.get()["soundboard"]["queue"]
        queue.append(sound_name)
        config.set("soundboard/queue", queue)
        logger(f"commands.play {sound_name} (queued)",
               location=interaction.guild.id, user=interaction.user.name)
        await interaction.response.send_message(lang_manager("commands.play.queued", sound_name))
        return
    try:
        await play_sound_coroutine(guild_id, sound_name)
    except Exception as e:
        logger(f"commands.play Error: {e}", level="ERROR",
               location=interaction.guild.id, user=interaction.user.name)
        await interaction.response.send_message(lang_manager("commands.play.404", sound_name), ephemeral=True)
        return
    await interaction.response.send_message(lang_manager("commands.play.success", sound_name))


@play.autocomplete('sound_name')
async def play_cmd_autocomplete(interaction: discord.Interaction, current: str):
    sounds = []
    for sound in config.get()["soundboard"]["sound_files"]:
        sounds.append(sound)

    filtered = [sound for sound in sounds if current.lower() in sound.lower()]
    if len(filtered) > 25:
        return [discord.app_commands.Choice(name=sound, value=sound) for sound in filtered[:25]]
    else:
        return [discord.app_commands.Choice(name=sound, value=sound) for sound in filtered]


@bot.tree.command(name="add_sound", description="Upload an MP3 file to save it to the sounds directory.")
async def add_sound_cmd(interaction: discord.Interaction, file: discord.Attachment):
    logger(f"commands.add_sound {file.filename}",
           user=interaction.user.name, location=interaction.guild.id)
    if not file.filename.lower().endswith('.mp3'):
        logger(f"commands.add_sound Error: File was not an mp3 file: {file.filename}",
               level="ERROR", location=interaction.guild.id, user=interaction.user.name)
        await interaction.response.send_message(lang_manager("commands.add.fileformat"), ephemeral=True)
        return

        # Save the file
    try:
        file_path = f"./sounds/{file.filename}"
        await file.save(file_path)
        await interaction.response.send_message(lang_manager("commands.add.success", file.filename))
    except Exception as e:
        logger(f"commands.add_sound Error: {e}", level="ERROR",
               location=interaction.guild.id, user=interaction.user.name)
        await interaction.response.send_message(lang_manager("commands.add.error", e), ephemeral=True)


@bot.tree.command(name='stop', description="Stops the current sound.")
async def stop(interaction: discord.Interaction):
    logger("commands.stop", user=interaction.user.name,
           location=interaction.guild.id)
    guild_id = interaction.guild.id
    await stop_sound_coroutine(guild_id)
    await interaction.response.send_message(lang_manager("commands.stop.success"))


@bot.tree.command(name='volume', description="Sets the volume in %")
async def set_volume_cmd(interaction: discord.Interaction, new_volume_level: int = 100):
    logger(f"commands.volume {new_volume_level}",
           user=interaction.user.name, location=interaction.guild.id)
    if (0 < new_volume_level <= config.get()["soundboard"]["max_volume"]):
        config.set("soundboard/volume", new_volume_level / 100)
        await interaction.response.send_message(lang_manager("commands.volume.success", config.get()["soundboard"]["volume"] * 100))
    else:
        await interaction.response.send_message(lang_manager("commands.volume.max", config.get()["soundboard"]["max_volume"]))
        logger(f"commands.volume Error: {new_volume_level}>{config.get()['soundboard']['max_volume']}",
               level="ERROR", location=interaction.guild.id, user=interaction.user.name)


@bot.tree.command(name='join', description="Joins the provided channelid/Your channel")
async def join(interaction: discord.Interaction, channel_id: str = None):
    if channel_id:
        channel_id = channel_id.strip('<>#')
        try:
            guild_id = interaction.guild.id
            await join_channel_coroutine(guild_id, channel_id)
            await interaction.response.send_message(lang_manager("commands.join.success", channel_id))
            await play_sound_coroutine(guild_id, "join")
        except Exception as e:
            logger(f"commands.join Error: {e}", level="ERROR",
                   location=interaction.guild.id, user=interaction.user.name)
            print(f"An error occurred: {e}")

    else:
        if interaction.user.voice and interaction.user.voice.channel:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message(lang_manager("commands.join.success", channel.id))
            logger(f"commands.join {channel.id}",
                   location=interaction.guild.id, user=interaction.user.name)
        else:
            await interaction.response.send_message(lang_manager("commands.join.no_nothing"), ephemeral=True)
            logger(f"commands.join Error: No channel id nor user is in channel",
                   level="ERROR", location=interaction.guild.id, user=interaction.user.name)


@bot.tree.command(name='leave', description="Disconnects the bot from the current voice channel.")
async def leave(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    await leave_channel_coroutine(guild_id)
    await interaction.response.send_message(lang_manager("commands.leave.success"))
    logger(f"commands.leave", location=interaction.guild.id,
           user=interaction.user.name)


@bot.tree.command(name='list', description="Lists all sounds.")
async def list(interaction: discord.Interaction):
    logger(f"commands.list", location=interaction.guild.id,
           user=interaction.user.name)
    sound_names = config.get()["soundboard"]["sound_files"].keys()
    embed = discord.Embed(title=lang_manager(
        "commands.list.title"), color=discord.Color.blue())

    embed.description = "\n".join(sound_names)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='queue', description="Lists all sounds in the queue.")
async def list_queue(interaction: discord.Interaction, action: str = None):
    logger(f"commands.queue", location=interaction.guild.id,
           user=interaction.user.name)
    sound_names = config.get()["soundboard"]["queue"]
    embed = discord.Embed(title=lang_manager(
        "commands.queue.title"), color=discord.Color.blue())

    embed.description = "\n".join(sound_names)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='random', description="Plays a random sound.")
async def random_cmd(interaction: discord.Interaction):
    usernames = []
    for user in bot.get_channel(int(config.get()["soundboard"]["channel_id"])).members:
        usernames.append(user.name)
    if not interaction.user.name in usernames:
        await interaction.response.send_message(lang_manager("commands.random.not_in_channel"))
        return
    guild_id = interaction.guild.id
    random_sound = await rand_sound(guild_id)
    if random_sound == "error":
        await interaction.response.send_message(lang_manager("commands.random.error"))
        return
    await interaction.response.send_message(lang_manager("commands.random.success", random_sound))
    logger(f"commands.random {random_sound}",
           location=interaction.guild.id, user=interaction.user.name)


@bot.tree.command(name="language")
async def language(interaction: discord.Interaction, lang: str = None):
    if (lang):
        available_langs = os.listdir(config.get()["lang_dir"])
        if (lang + ".json" in available_langs):
            config.set("lang", lang)
            global lang_manager
            lang_manager = LangHandler(lang)
            await interaction.response.send_message(content=lang_manager("commands.language.success"))
            logger(
                f"commands.language {lang}", location=interaction.guild.id, user=interaction.user.name)
        else:
            print(f"{lang} is not in {available_langs}")
            logger(f"commands.language {lang} not in {available_langs}", level="ERROR",
                   location=interaction.guild.id, user=interaction.user.name)
    else:
        await interaction.response.send_message(content=lang_manager("commands.language.lang_empty", str(os.listdir(config.get()["lang_dir"]))), ephemeral=True)
        logger(f"commands.language Field {lang} is empty", level="ERROR",
               location=interaction.guild.id, user=interaction.user.name)


@language.autocomplete('lang')
async def language_cmd_autocomplete(interaction: discord.Interaction, current: str):
    langs = os.listdir(config.get()["lang_dir"])
    langs_no_json = []
    for lang in langs:
        if lang.endswith(".json"):
            langs_no_json.append(lang[:-5])
    filtered = [lang for lang in langs_no_json if current.lower()
                in lang.lower()]
    return [discord.app_commands.Choice(name=lang, value=lang) for lang in filtered]


async def rand_sound(guild_id, sound_group=None):
    choosables = []
    for sound in config.get()["soundboard"]["sound_files"].keys():
        choosables.append(sound)
    sound = random.choice(choosables)
    try: 
        await play_sound_coroutine(guild_id, sound)
    except Exception as e:
        logger(f"commands.random {sound} {e}", level="ERROR",
               location=guild_id, user="Unknown")
        return "error"
    return str(sound)


def run_flask_app():
    from waitress import serve
    serve(app, host=config.get()["flask"]["host"],
          port=config.get()["flask"]["port"])


if __name__ == '__main__':
    gen_authcode("watchdog")
    LOG_FILE = os.path.join(
        "logs", f"log-{datetime.now().strftime("%m-%d-%Y_%H:%M:%S")}.txt")
    LATEST_LOG_FILE = os.path.join("logs", "latest.txt")
    watchdog_process = subprocess.Popen(['python3', 'watchdog_script.py'])

    try:
        threading.Thread(target=run_flask_app).start()
        bot.run(config.get()["discord_token"])
    finally:
        open(LOG_FILE, 'a').close()
        os.rename(LATEST_LOG_FILE, LOG_FILE)
        watchdog_process.terminate()
