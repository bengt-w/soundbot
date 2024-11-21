import os
import json
import types

CONFIG_FILE = os.path.join("config", "config.json")

def get():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def set(key, value):
    with open(CONFIG_FILE, 'r') as f:
        cfg = json.load(f)

    keys = key.split('/')

    d = cfg
    for k in keys[:-1]:
        if k not in d:
            d[k] = {}
        d = d[k]
    
    d[keys[-1]] = value

    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=4)

# def save(config):
#     if isinstance(config, dict):
#         to_save = config
#     else:
#         to_save = {key: value for key, value in config.__dict__.items() 
#             if not key.startswith('__') and not isinstance(value, (types.FunctionType, types.ModuleType))}
    
#     with open(CONFIG_FILE, 'w') as f:
#         json.dump(to_save, f, indent=4)


def save(config):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}
    
    if isinstance(config, dict):
        updated_data = {**existing_data, **config}
    else:
        updated_data = {**existing_data, **{
            key: value for key, value in config.__dict__.items()
            if not key.startswith('__') and not isinstance(value, (types.FunctionType, types.ModuleType))
        }}
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(updated_data, f, indent=4)


        
def remove(key):
    with open(CONFIG_FILE, 'r') as f:
        cfg = json.load(f)

    keys = key.split('/')

    d = cfg
    for k in keys[:-1]:
        if k not in d:
            return
        d = d[k]

    if keys[-1] in d:
        del d[keys[-1]]

    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=4)