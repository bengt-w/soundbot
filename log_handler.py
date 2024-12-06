from datetime import datetime
import os

time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
try:
    os.mkdir("logs")
except FileExistsError:
    pass

LOG_FILE = os.path.join("logs", f"log-{datetime.now().strftime("%m-%d-%Y_%H:%M:%S")}.txt")
LATEST_LOG_FILE = os.path.join("logs", "latest.txt")

open(LATEST_LOG_FILE, 'a').close()

def log(message, level="INFO", time = None, location="WEBUI", user="Unknown", method=" "):
    if time is None:
        time = datetime.now().strftime("%H:%M:%S")
        if not message:
            raise ValueError("Message cannot be empty")
        if method != " ":
            method = f" {method} "
        with open(LATEST_LOG_FILE, "a") as f:
            f.writelines(f"[{time} {level}] {user}@{location}:{method}{message}\n")
        