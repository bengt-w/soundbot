import os
import requests
from requests.auth import HTTPBasicAuth
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json

# Lade die Konfigurationsdaten aus der config.json
def load_config():
    with open('./config/config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('./config/config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()
username = config['flask']['username']
password_clear = config['flask']['password_clear']  # Passwort im Klartext
host = config['flask']['host']
port = config['flask']['port']

# API Credentials
auth = HTTPBasicAuth(username, password_clear)
base_url = f'http://{host}:{port}/api/sounds'

# Funktion zum Überprüfen, ob der Sound bereits registriert ist
def is_sound_registered(name):
    response = requests.get(base_url, auth=auth)
    if response.status_code == 200:
        sounds = response.json()
        return name in sounds
    else:
        print("Failed to get sound:", response.json())
        return False

# Funktion zum Hinzufügen eines Sounds
def add_sound(file_name):
    sound_name = os.path.splitext(file_name)[0]
    if not is_sound_registered(sound_name):
        data = {
            "name": sound_name,  # Name ohne Dateiendung
            "path": f"sounds/{file_name}"
        }
        response = requests.post(f'{base_url}/add', json=data, auth=auth)
        print(f'Added: {data["name"]}', response.json())
    else:
        print(f'Sound "{sound_name}" already registered.')

# Funktion zum Entfernen eines Sounds
def remove_sound(file_name):
    sound_name = os.path.splitext(file_name)[0]
    if is_sound_registered(sound_name):
        data = {
            "name": sound_name  # Name ohne Dateiendung
        }
        response = requests.post(f'{base_url}/remove', json=data, auth=auth)
        print(f'Removed: {data["name"]}', response.json())
    else:
        print(f'Sound "{sound_name}" not found.')

# Event-Handler für Dateiänderungen
class SoundEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            if(event.src_path.endswith('.wav') or event.src_path.endswith('.mp3')):
                if(not event.src_path in requests.get(f'{base_url}')):
                    add_sound(os.path.basename(event.src_path))

    def on_deleted(self, event):
        if not event.is_directory:
            remove_sound(os.path.basename(event.src_path))

# Hauptfunktion
if __name__ == "__main__":
    path = config["soundboard"]["sounds_dir"]
    event_handler = SoundEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    print(f"Watching directory: {path}")
    
    try:
        while True:
            # Hier könnten weitere Operationen durchgeführt werden, wenn nötig
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
