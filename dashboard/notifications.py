import requests
from config import DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_discord(message):
    """Send notification to Discord via webhook"""
    if not DISCORD_WEBHOOK_URL:
        return False, "Discord not configured"
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
        if resp.status_code == 204:
            return True, "Sent to Discord"
        return False, f"Discord error: {resp.status_code}"
    except requests.RequestException as e:
        return False, f"Discord error: {e}"


def send_telegram(message):
    """Send notification to Telegram via bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "Telegram not configured"
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        if resp.status_code == 200:
            return True, "Sent to Telegram"
        return False, f"Telegram error: {resp.status_code}"
    except requests.RequestException as e:
        return False, f"Telegram error: {e}"


def send_all(message):
    """Send notification to all configured channels"""
    results = {}
    if DISCORD_WEBHOOK_URL:
        ok, msg = send_discord(message)
        results["discord"] = {"success": ok, "message": msg}
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        ok, msg = send_telegram(message)
        results["telegram"] = {"success": ok, "message": msg}
    return results


def test_discord():
    return send_discord("Test notification from 27TechAI Dashboard")


def test_telegram():
    return send_telegram("Test notification from 27TechAI Dashboard")
