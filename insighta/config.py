import os, json, time

CONFIG_DIR = os.path.expanduser("~/.insighta")
CONFIG_FILE = os.path.join(CONFIG_DIR, "credentials.json")


def save_tokens(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def load_tokens():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE) as f:
        return json.load(f)


def clear_tokens():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


def is_expired(tokens):
    return tokens["expires_at"] < time.time()