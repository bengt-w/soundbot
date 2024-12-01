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
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        try: 
            return users[username]
        except KeyError:
            raise ValueError("User not found")

def gen_authcode(username):
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        auth_code = generate_authcode()
        users[username] = auth_code
        with open(USERFILE, 'w') as f:
            json.dump(users, f)
        return auth_code
        
def validate_authcode(username, auth_code):
    if (config.get()["demo_mode"] or config.get()["developement_mode"]) and username:
        return True
    with open(USERFILE, 'r') as f:
        users = json.load(f)
        try:
            if users[username] == auth_code:
                return True
            else:
                return False
        except KeyError:
            return False
    
    

def generate_authcode(length: int = 6):
    code_chars = string.ascii_uppercase + string.digits
    auth_code = ''.join(random.choices(code_chars, k=length))
    return auth_code
    