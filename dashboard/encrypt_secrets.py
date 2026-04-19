from cryptography.fernet import Fernet
import json

# Replace with your generated encryption key
KEY = b'YOUR_GENERATED_KEY_HERE'

# Replace with your actual secrets - ALL API KEYS IN ONE ENCRYPTED FILE
secrets = {
    # GitHub Configuration
    "GITHUB_USERNAME": "your_github_username",
    "GITHUB_REPO": "your_repo_name",
    "GITHUB_TOKEN": "ghp_your_personal_access_token",

    # AI API Keys
    "OPENROUTER_API_KEY": "sk-or-v1-your_openrouter_api_key",
    "OPENAI_API_KEY": "sk-proj-your_openai_api_key",
    "ANTHROPIC_API_KEY": "sk-ant-your_anthropic_api_key",
    "GOOGLE_AI_API_KEY": "your_google_ai_api_key",
    "HUGGINGFACE_API_KEY": "hf_your_huggingface_token",

    # Optional: Social Media & Other APIs
    "TELEGRAM_BOT_TOKEN": "your_telegram_bot_token",
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/your_webhook",
    "TWITTER_API_KEY": "your_twitter_api_key",

    # Site Configuration
    "SITE_URL": "https://yourusername.github.io/yourrepo",
    "ADMIN_PASSWORD": "your_admin_password"
}

def encrypt_secrets():
    """Encrypt sensitive data and save to secrets.enc"""
    try:
        cipher = Fernet(KEY)
        json_str = json.dumps(secrets, ensure_ascii=False, indent=2)
        encrypted = cipher.encrypt(json_str.encode())

        with open("secrets.enc", "wb") as f:
            f.write(encrypted)

        print("[OK] Secrets encrypted and saved to secrets.enc")
        print("[WARNING] Do NOT upload secrets.enc or your key to GitHub!")
    except Exception as e:
        print(f"[ERROR] Encryption failed: {e}")

if __name__ == "__main__":
    encrypt_secrets()
