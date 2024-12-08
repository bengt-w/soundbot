import random
import string
import os
import json
import config_handler as config

USERFILE = "users.json"

if not os.path.exists(USERFILE):
    with open(USERFILE, 'w') as f:
        f.write("{}")

def get_authcode(username):
    username = username.lower()
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        try:
            return users[username]["otp"]
        except KeyError:
            raise ValueError("User not found")

def gen_authcode(username, theme="dark"):
    username = username.lower()
    with open(USERFILE, 'r') as f:
        users = json.load(f)
    
    auth_code = generate_authcode()
    
    if username not in users:
        users[username] = {"otp": None, "theme": theme, "joinsound": None}
    
    users[username]["otp"] = auth_code
    
    with open(USERFILE, 'w') as f:
        json.dump(users, f, indent=4)
    
    return auth_code

def validate_authcode(username, auth_code):
    if (config.get()["demo_mode"] or config.get()["developement_mode"]) and username:
        return True
    
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        try:
            return users[username.lower()]["otp"].lower() == auth_code.lower()
        except KeyError:
            return False

def generate_authcode(length: int = 6):
    code_chars = string.ascii_uppercase + string.digits
    auth_code = ''.join(random.choices(code_chars, k=length))
    return auth_code

async def get_theme(username):
    username = username.lower()
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        try:
            return users[username]["theme"]
        except KeyError:
            return "dark"

def set_theme(username, theme):
    username = username.lower()
    with open(USERFILE, 'r') as f:
        users = json.load(f)
    
    if username not in users:
        otp = random.randint(100_000_000, 999_999_999)
        users[username] = {"otp": otp, "theme": "dark", "joinsound": None}
    
    users[username]["theme"] = theme
    
    with open(USERFILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_joinsound(username):
    username = username.lower()
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        try:
            return users[username]["joinsound"]
        except KeyError:
            return None

def set_joinsound(username, sound):
    username = username.lower()
    with open(USERFILE, 'r') as f:
        users = json.load(f)
    
    if username not in users:
        otp = random.randint(100_000_000, 999_999_999)
        users[username] = {"otp": otp, "theme": "dark", "joinsound": None}
    
    users[username]["joinsound"] = sound
    
    with open(USERFILE, 'w') as f:
        json.dump(users, f, indent=4)