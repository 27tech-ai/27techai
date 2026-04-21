import os
import json
from cryptography.fernet import Fernet

# ============================================================
# CONFIGURATION - Edit these values for your setup
# ============================================================

# Dashboard login
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "27techai2026"

# Flask settings
HOST = "0.0.0.0"
PORT = 5000
SECRET_KEY = "change-this-to-a-random-secret-string"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
WEBSITE_DIR = os.path.join(PROJECT_DIR, "website")
DATA_FILE = os.path.join(WEBSITE_DIR, "data.json")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "backups")
ANALYTICS_DB = os.path.join(BASE_DIR, "data", "analytics.db")
LOG_FILE = os.path.join(BASE_DIR, "data", "activity.log")

# GitHub (set to empty strings if not using GitHub sync)
GITHUB_USERNAME = ""
GITHUB_REPO = ""
GITHUB_TOKEN = ""

# Notifications (set to empty strings if not using)
DISCORD_WEBHOOK_URL = ""
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""


def get_github_api_url():
    if GITHUB_USERNAME and GITHUB_REPO:
        return f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/website/data.json"
    return None


def get_github_raw_url():
    if GITHUB_USERNAME and GITHUB_REPO:
        return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/website/data.json"
    return None


def load_secrets_from_enc():
    """Try to load secrets from encrypted file if it exists"""
    enc_file = os.path.join(BASE_DIR, "secrets.enc")
    key_file = os.path.join(BASE_DIR, ".key")

    if not os.path.exists(enc_file) or not os.path.exists(key_file):
        return False

    try:
        with open(key_file, "r") as f:
            key = f.read().strip().encode()
        cipher = Fernet(key)
        with open(enc_file, "rb") as f:
            encrypted = f.read()
        decrypted = cipher.decrypt(encrypted)
        secrets = json.loads(decrypted.decode())

        global GITHUB_USERNAME, GITHUB_REPO, GITHUB_TOKEN
        global DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

        GITHUB_USERNAME = secrets.get("GITHUB_USERNAME", GITHUB_USERNAME)
        GITHUB_REPO = secrets.get("GITHUB_REPO", GITHUB_REPO)
        GITHUB_TOKEN = secrets.get("GITHUB_TOKEN", GITHUB_TOKEN)
        DISCORD_WEBHOOK_URL = secrets.get("DISCORD_WEBHOOK_URL", DISCORD_WEBHOOK_URL)
        TELEGRAM_BOT_TOKEN = secrets.get("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
        TELEGRAM_CHAT_ID = secrets.get("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
        return True
    except Exception:
        return False


# Try encrypted secrets on import
load_secrets_from_enc()
