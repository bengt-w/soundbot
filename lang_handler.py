import json
import os

class LangHandler:
    def __init__(self, language):
        self.language = language
        self.translations = self.load_translations()

    def load_translations(self):
        lang_file_path = os.path.join("lang", f"{self.language}.json")
        try:
            with open(lang_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Sprachdatei {lang_file_path} nicht gefunden.")
            return {}

    def replace_placeholders(self, text, args):
        if isinstance(text, str):
            for i, arg in enumerate(args, 1):
                placeholder = f"$({i})"
                text = text.replace(placeholder, str(arg))
            
            placeholders = self.extract_placeholders(text)
            for placeholder in placeholders:
                value = self.translations.get(placeholder)
                if value:
                    text = text.replace(f"$({placeholder})", str(value))

        return text

    def extract_placeholders(self, text):
        import re
        return re.findall(r'\$\((.*?)\)', text)

    def __call__(self, key, *args):
        keys = key.split('.')
        translation = self.translations

        for k in keys:
            translation = translation.get(k)
            if translation is None:
                return f"Übersetzung für '{key}' nicht gefunden."

        return self.replace_placeholders(translation, args)
