import config_handler as config
sound_files = config.get()["soundboard"]["sound_files"]
sorted_sound_files = dict(sorted(sound_files.items()))
print(sorted_sound_files)
