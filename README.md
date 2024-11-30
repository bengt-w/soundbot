# soundbot
This is a small discord.py soundboard bot with REST-API and webinterface using flask. 

I got the initial code with a Tkinther interface from https://github.com/JonasB2510
I changed it so it is using flask as an WebUI with HTTP-Basic-Auth

# Screenshots:
## Webui:
![](https://git.absolutely-not-a-virus.de/soundbot/soundbot/raw/branch/main/screenshots/1.png)

# Install: 
`$ git clone https://git.absolutely-not-a-virus.de/soundbot/soundbot` 

`$ cd soundbot` 

`$ python3 bot.py` 

Configure the config by following the commands in the console.
<details>
  <summary>Where to get GuildID</summary>
  To get the server ID for the first parameter, open Discord, go to Settings → Advanced and enable developer mode. Then, right-click on the server title and select "Copy ID" to get the guild ID.
</details>
<details>
  <summary>Where to get ChannelID</summary>
  To get the server ID for the first parameter, open Discord, go to Settings → Advanced and enable developer mode. Then, right-click on the voice channel and select "Copy ID" to get the channel ID.
</details>
<details>
  <summary>Where to get a bot token</summary>
  To get a Bot/Bot token first go to https://discord.com/developers/applications and click on new application, type in a name read & agree the TOS & policy. Now on the side click on bot then scroll down and enable "Message Content Intent". Now go to oauth2 on the side. Now select bot > administrator (or "View Channels", "Connect", "Speak" ⚠️ Only tested with Adminitstator permissions ⚠️) now copy your url at the bottom and copy it into a new tab and add the bot to your server.
</details>
<details>
  <summary>I don't have the htpasswd command</summary>
    Install the apache2-utils packet. e.g.:
  
    $ sudo apt install apache2-utils
</details>

Now add sound files to the sounds directory and start the bot with `$ python3 bot.py`

# API Documentation

## **Authentifizierung**

All API-Endpoints are password protected and require a HTTP Basic Auth header.

## API Endpoints

<details>
<summary><strong>1. Get Sounds</strong></summary>

- **Endpoint:** `/api/sounds`
- **Method:** `GET`
- **Description:** Gets a list of all registered sounds.

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'http://127.0.0.1:5000/api/sounds',
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>2. Add Sound</strong></summary>

- **Endpoint:** `/api/sounds/add`
- **Method:** `POST`
- **Description:** Registers a soundfile.

**Body example:**

```json
{
    "name": "example_sound",
    "path": "sounds/example_sound.mp3"
}
```

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

data = {
    "name": "example_sound",
    "path": "sounds/example_sound.mp3"
}

response = requests.post(
    'http://127.0.0.1:5000/api/sounds/add',
    json=data,
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>3. Remove Sound</strong></summary>

- **Endpoint:** `/api/sounds/remove`
- **Method:** `POST`
- **Description:** Unregisters a soundfile.

**Body example:**

```json
{
    "name": "example_sound"
}
```

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

data = {
    "name": "example_sound"
}

response = requests.post(
    'http://127.0.0.1:5000/api/sounds/remove',
    json=data,
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>4. Rename Sound</strong></summary>

- **Endpoint:** `/api/sounds/rename`
- **Method:** `POST`
- **Description:** Changes the name of an registrated sound.

**Body example:**

```json
{
    "oldName": "example_sound",
    "newName": "new_example_sound"
}
```

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

data = {
    "oldName": "example_sound",
    "newName": "new_example_sound"
}

response = requests.post(
    'http://127.0.0.1:5000/api/sounds/rename',
    json=data,
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>5. Play Sound</strong></summary>

- **Endpoint:** `/api/sounds/play`
- **Method:** `POST`
- **Description:** Plays a sound.

**Body example:**

```json
{
    "name": "example_sound"
}
```

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

data = {
    "name": "example_sound"
}

response = requests.post(
    'http://127.0.0.1:5000/api/sounds/play',
    json=data,
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>6. Stop Sound</strong></summary>

- **Endpoint:** `/api/sounds/stop`
- **Method:** `POST`
- **Description:** Stops the audio.

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    'http://127.0.0.1:5000/api/sounds/stop',
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>7. Join Channel</strong></summary>

- **Endpoint:** `/api/channel/join`
- **Method:** `POST`
- **Description:** Make the bot join a specific channel.

**Body example:**

```json
{
    "guild_id": "1234567890123456789",
    "channel_id": "1234567890123456789"
}
```

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

data = {
    "guild_id": "1234567890123456789",
    "channel_id": "1234567890123456789"
}

response = requests.post(
    'http://127.0.0.1:5000/api/channel/join',
    json=data,
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>8. Leave Channel</strong></summary>

- **Endpoint:** `/api/channel/leave`
- **Method:** `POST`
- **Description:** Make the bot leave.

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    'http://127.0.0.1:5000/api/channel/leave',
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>9. Update Settings</strong></summary>

- **Endpoint:** `/api/settings`
- **Method:** `POST`
- **Description:** Changes the settings for `guild_id` and `channel_id`.

**Body example:**

```json
{
    "guild_id": "1234567890123456789",
    "channel_id": "1234567890123456789"
}
```

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

data = {
    "guild_id": "1234567890123456789",
    "channel_id": "1234567890123456789"
}

response = requests.post(
    'http://127.0.0.1:5000/api/settings',
    json=data,
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>

<details>
<summary><strong>10. Get Settings</strong></summary>

- **Endpoint:** `/api/settings`
- **Method:** `GET`
- **Description:** Gets the current setting of: (`guild_id` and `channel_id`)

**Request example:**

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'http://127.0.0.1:5000/api/settings',
    auth=HTTPBasicAuth('admin', 'password123')
)
print(response.json())
```
</details>


# Current Features:
<details>
  <summary>Discord Bot Commands</summary>

### !play <sound_name>

Plays the specified sound in the current voice channel.

### !stop

Stops the currently playing sound.

### !join <channel_id> (Optional)

Joins the specified voice channel or the channel where the user is currently in.

### !leave

Leaves the voice channel the bot is connected to.

### !list

Lists all the available sounds in the bot.
</details>

<details>
  <summary>Watchdog</summary>
Monitors the sounds directory for changes (additions or deletions of sound files). Automatically registers or unregisters sound files with the Flask API. 

Event Handling: 

`on_created: Adds the new sound file to the registry. `

`on_deleted: Removes the sound file from the registry.`

</details>
<details>
  <summary>Configuration</summary>
Stores all configuration settings such as sound files, Discord guild ID, channel ID, and Flask server details.

Sound Files: A dictionary mapping sound names to their file paths.
Guild ID: The ID of the Discord server.
Channel ID: The ID of the Discord channel.
Discord Token: The token for your Discord bot.
Flask Settings: Includes the host, port, username, and password for the Flask server.

`{
  "sound_files": {},
  "guild_id": "your_guild_id",
  "channel_id": "your_channel_id",
  "discord_token": "YOUR_DISCORD_TOKEN",
  "flask": {
    "host": "127.0.0.1",
    "port": 5000,
    "username": "admin",
    "password": "hashed_password"
  }
}`

</details>
<details>
  <summary>Flask API Endpoints</summary>

### GET /api/sounds

Returns a list of all registered sound files.
### POST /api/sounds/add

Adds a new sound file to the registry.

    Request Body:

    json

    {
      "name": "sound_name",
      "path": "path/to/sound/file"
    }

### POST /api/sounds/remove

Removes a sound file from the registry.

    Request Body:

    json

    {
      "name": "sound_name"
    }

### POST /api/sounds/rename

Renames an existing sound file in the registry.

    Request Body:

    json

    {
      "oldName": "old_sound_name",
      "newName": "new_sound_name"
    }

### POST /api/sounds/play

Plays a registered sound in the specified Discord channel.

    Request Body:

    json

    {
      "name": "sound_name"
    }

### POST /api/channel/join

Joins a specified voice channel in a Discord server.

    Request Body:

    json

    {
      "guild_id": "your_guild_id",
      "channel_id": "your_channel_id"
    }

### POST /api/channel/leave

Leaves the voice channel in the specified Discord server.

    Request Body:

    json

    {
      "guild_id": "your_guild_id"
    }

### POST /api/sounds/stop

Stops the currently playing sound in the specified Discord server.

    Request Body:

    json

    {
      "guild_id": "your_guild_id"
    }

</details>
