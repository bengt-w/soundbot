# from werkzeug.security import generate_password_hash
# print(generate_password_hash("abc"))
from config_handler import get, set
sounds = []
for sound in get()["soundboard"]["sound_files"]:
    sounds.append(sound)
print(sounds)
print()
print(get()["soundboard"]["sound_files"])