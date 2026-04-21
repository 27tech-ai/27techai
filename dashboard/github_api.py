import base64
import json
import requests
from config import GITHUB_USERNAME, GITHUB_REPO, GITHUB_TOKEN, get_github_api_url, get_github_raw_url


def get_file_sha():
    """Get the SHA of data.json on GitHub for update tracking"""
    api_url = get_github_api_url()
    if not api_url or not GITHUB_TOKEN:
        return None
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("sha")
        return None
    except requests.RequestException:
        return None


def push_to_github(data_json_str, sha=None, message="Update data from 27TechAI Dashboard"):
    """Push updated data.json to GitHub"""
    api_url = get_github_api_url()
    if not api_url or not GITHUB_TOKEN:
        return False, "GitHub not configured"

    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content = base64.b64encode(data_json_str.encode()).decode()
        payload = {
            "message": message,
            "content": content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        resp = requests.put(api_url, headers=headers, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            return True, "Pushed to GitHub"
        else:
            return False, f"GitHub error: {resp.status_code}"
    except requests.RequestException as e:
        return False, f"Network error: {e}"


def get_repo_info():
    """Get repository info from GitHub"""
    if not GITHUB_USERNAME or not GITHUB_REPO:
        return None
    try:
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "watchers": data.get("watchers_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "description": data.get("description", ""),
                "last_push": data.get("pushed_at", ""),
            }
        return None
    except requests.RequestException:
        return None


def is_configured():
    return bool(GITHUB_USERNAME and GITHUB_REPO and GITHUB_TOKEN)
