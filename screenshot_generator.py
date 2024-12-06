import os
import base64
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from config_handler import get, set
import time
from user_handler import gen_authcode

users = ""

with open("users.json", "r") as f:
    users = f.read()

screenshot_dir = "screenshots"
screenshot_counter = 0

themes = [
    "light", "dark", "cyanLight", "cyanDark", "pinkLight", "pinkDark",
    "greenLight", "greenDark", "blueLight", "blueDark", "purpleLight", 
    "purpleDark", "beigeLight", "beigeDark", "redLight", "redDark", 
    "yellowLight", "yellowDark", "orangeLight", "orangeDark", 
    "greyLight", "greyDark", "uglyLight", "uglyDark", "jannikLight", "jannikDark"
]

def screenshot_path(filename):
    return os.path.join(screenshot_dir, filename)

def encode_basic_auth(username, password):
    credentials = f"{username}:{password}"
    return f"Basic {base64.b64encode(credentials.encode()).decode()}"

set("demo_mode", True)

start_time = time.time()
for lang in os.listdir(get()["lang_dir"]):
    set("lang", lang.replace(".json", ""))
    for theme in themes:
        try:
            pw = gen_authcode(theme, theme)
            def interceptor(request):
                request.headers["Authorization"] = encode_basic_auth(theme, pw)
            url = get()["flask"]["url"]

            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--enable-javascript")
            options.add_argument("--window-size=1920,1080")

            driver = webdriver.Chrome(options=options)
            driver.scopes = ['.*']  # Interceptiere alle Anfragen

            global auth_header
            auth_header = encode_basic_auth(theme, pw)
            driver.request_interceptor = interceptor

            driver.get(url)
            time.sleep(0.5) # this is a workaround to show the channel
            path = screenshot_path(f"{theme}-{lang}.png")
            driver.save_screenshot(path)
            screenshot_counter += 1
            print(f"Screenshot saved as {path}")

        finally:
            driver.quit() 
            
set("demo_mode", False)

with open("users.json", "w") as f:
    f.write(users)

print(f"Done! Took: {(time.time() - start_time):.1f}s ({screenshot_counter} screenshots that each took ~{((time.time() - start_time) / screenshot_counter):.1f}s)")