import os
import json
import uuid
import shutil
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit

import config
import github_api
import git_push
import notifications
import analytics
from analytics import log_activity

# ============================================================
# App Setup
# ============================================================

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure data directories exist
os.makedirs(config.BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(config.ANALYTICS_DB), exist_ok=True)
os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

# Init analytics DB
analytics.init_db()


# ============================================================
# Auth Helpers
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# Data Helpers
# ============================================================

def load_data():
    """Load data from local data.json"""
    if os.path.exists(config.DATA_FILE):
        with open(config.DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cards": [], "site": {"title": "27TechAI", "subtitle": "Scripts & Automation Hub", "accentColor": "#6c63ff", "footerText": ""}}


def save_data(data, push_to_git=True):
    """Save data to local data.json and auto-push to GitHub via git"""
    os.makedirs(os.path.dirname(config.DATA_FILE), exist_ok=True)
    with open(config.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Auto-push to GitHub via git (no API token needed)
    git_msg = None
    if push_to_git and git_push.is_git_repo():
        ok, msg = git_push.git_add_commit_push("Update data from 27TechAI Dashboard")
        git_msg = msg
        if ok:
            log_activity("git_push", msg)
    return True, git_msg


def make_backup():
    """Create a backup of data.json"""
    if not os.path.exists(config.DATA_FILE):
        return False
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(config.BACKUP_DIR, f"data_{timestamp}.json")
    shutil.copy2(config.DATA_FILE, backup_file)

    # Keep only last 20 backups
    backups = sorted(os.listdir(config.BACKUP_DIR))
    if len(backups) > 20:
        for old in backups[:len(backups) - 20]:
            os.remove(os.path.join(config.BACKUP_DIR, old))
    return True


# ============================================================
# Routes - Auth
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            session["logged_in"] = True
            session["user"] = username
            log_activity("login", f"User {username} logged in")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    log_activity("logout", "User logged out")
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# Routes - Dashboard
# ============================================================

@app.route("/")
@login_required
def dashboard():
    data = load_data()
    overview = analytics.get_overview()
    recent = analytics.get_recent_activity(10)
    popular = analytics.get_popular_scripts(5)

    total_scripts = len(data.get("cards", []))
    published = len([c for c in data.get("cards", []) if c.get("status") != "draft"])
    drafts = total_scripts - published

    return render_template("dashboard.html",
        total_scripts=total_scripts,
        published=published,
        drafts=drafts,
        overview=overview,
        recent=recent,
        popular=popular,
        github_configured=github_api.is_configured(),
        git_status=git_push.get_git_status()
    )


# ============================================================
# Routes - Scripts
# ============================================================

@app.route("/scripts")
@login_required
def scripts_page():
    data = load_data()
    cards = data.get("cards", [])
    # Get categories
    categories = sorted(set(c.get("category", "uncategorized") for c in cards))
    return render_template("scripts.html", cards=cards, categories=categories)


@app.route("/scripts/add", methods=["GET", "POST"])
@login_required
def script_add():
    if request.method == "POST":
        data = load_data()
        new_card = {
            "id": str(uuid.uuid4())[:8],
            "title": request.form.get("title", ""),
            "desc": request.form.get("desc", ""),
            "img": request.form.get("img", "") or f"https://picsum.photos/id/{len(data.get('cards', []))}/400/200",
            "link": request.form.get("link", "#"),
            "category": request.form.get("category", "uncategorized"),
            "tags": [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()],
            "status": request.form.get("status", "published"),
            "clicks": 0,
            "createdAt": datetime.now().strftime("%Y-%m-%d"),
            "updatedAt": datetime.now().strftime("%Y-%m-%d")
        }
        data["cards"].append(new_card)
        make_backup()
        save_data(data)
        log_activity("script_add", f"Added: {new_card['title']}")
        notifications.send_all(f"New script added: {new_card['title']}")
        return redirect(url_for("scripts_page"))
    return render_template("script_edit.html", script=None, action="add")


@app.route("/scripts/edit/<script_id>", methods=["GET", "POST"])
@login_required
def script_edit(script_id):
    data = load_data()
    script = None
    script_index = None
    for i, c in enumerate(data["cards"]):
        if c.get("id") == script_id:
            script = c
            script_index = i
            break

    if script is None:
        return redirect(url_for("scripts_page"))

    if request.method == "POST":
        data["cards"][script_index]["title"] = request.form.get("title", script["title"])
        data["cards"][script_index]["desc"] = request.form.get("desc", script["desc"])
        data["cards"][script_index]["img"] = request.form.get("img", script["img"])
        data["cards"][script_index]["link"] = request.form.get("link", script["link"])
        data["cards"][script_index]["category"] = request.form.get("category", script.get("category", "uncategorized"))
        data["cards"][script_index]["tags"] = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        data["cards"][script_index]["status"] = request.form.get("status", script.get("status", "published"))
        data["cards"][script_index]["updatedAt"] = datetime.now().strftime("%Y-%m-%d")

        make_backup()
        save_data(data)
        log_activity("script_edit", f"Edited: {script['title']}")
        return redirect(url_for("scripts_page"))

    return render_template("script_edit.html", script=script, action="edit")


# ============================================================
# API - Scripts
# ============================================================

@app.route("/api/scripts", methods=["GET"])
@login_required
def api_scripts_list():
    data = load_data()
    return jsonify(data.get("cards", []))


@app.route("/api/scripts", methods=["POST"])
@login_required
def api_scripts_add():
    body = request.get_json(force=True)
    data = load_data()
    new_card = {
        "id": str(uuid.uuid4())[:8],
        "title": body.get("title", ""),
        "desc": body.get("desc", ""),
        "img": body.get("img", "") or f"https://picsum.photos/id/{len(data.get('cards', []))}/400/200",
        "link": body.get("link", "#"),
        "category": body.get("category", "uncategorized"),
        "tags": body.get("tags", []),
        "status": body.get("status", "published"),
        "clicks": 0,
        "createdAt": datetime.now().strftime("%Y-%m-%d"),
        "updatedAt": datetime.now().strftime("%Y-%m-%d")
    }
    data["cards"].append(new_card)
    make_backup()
    save_data(data)
    log_activity("script_add", f"Added: {new_card['title']}")
    notifications.send_all(f"New script added: {new_card['title']}")
    return jsonify({"success": True, "script": new_card})


@app.route("/api/scripts/<script_id>", methods=["PUT"])
@login_required
def api_scripts_update(script_id):
    body = request.get_json(force=True)
    data = load_data()
    for i, c in enumerate(data["cards"]):
        if c.get("id") == script_id:
            for key in ["title", "desc", "img", "link", "category", "tags", "status"]:
                if key in body:
                    data["cards"][i][key] = body[key]
            data["cards"][i]["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
            make_backup()
            save_data(data)
            log_activity("script_edit", f"Edited: {c['title']}")
            return jsonify({"success": True})
    return jsonify({"success": False, "error": "Not found"}), 404


@app.route("/api/scripts/<script_id>", methods=["DELETE"])
@login_required
def api_scripts_delete(script_id):
    data = load_data()
    new_cards = []
    deleted = None
    for c in data["cards"]:
        if c.get("id") == script_id:
            deleted = c
        else:
            new_cards.append(c)

    if deleted:
        data["cards"] = new_cards
        make_backup()
        save_data(data)
        log_activity("script_delete", f"Deleted: {deleted['title']}")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Not found"}), 404


@app.route("/api/scripts/reorder", methods=["PUT"])
@login_required
def api_scripts_reorder():
    body = request.get_json(force=True)
    order = body.get("order", [])  # list of script IDs in new order
    data = load_data()
    card_map = {c.get("id"): c for c in data["cards"]}
    reordered = [card_map[oid] for oid in order if oid in card_map]
    # Add any cards not in the order list
    existing_ids = set(order)
    for c in data["cards"]:
        if c.get("id") not in existing_ids:
            reordered.append(c)
    data["cards"] = reordered
    make_backup()
    save_data(data)
    log_activity("script_reorder", "Reordered scripts")
    return jsonify({"success": True})


@app.route("/api/scripts/duplicate/<script_id>", methods=["POST"])
@login_required
def api_scripts_duplicate(script_id):
    data = load_data()
    for c in data["cards"]:
        if c.get("id") == script_id:
            dup = dict(c)
            dup["id"] = str(uuid.uuid4())[:8]
            dup["title"] = c["title"] + " (Copy)"
            dup["status"] = "draft"
            dup["clicks"] = 0
            dup["createdAt"] = datetime.now().strftime("%Y-%m-%d")
            dup["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
            data["cards"].append(dup)
            make_backup()
            save_data(data)
            log_activity("script_duplicate", f"Duplicated: {c['title']}")
            return jsonify({"success": True, "script": dup})
    return jsonify({"success": False, "error": "Not found"}), 404


# ============================================================
# API - Analytics
# ============================================================

@app.route("/api/analytics/overview")
@login_required
def api_analytics_overview():
    data = load_data()
    overview = analytics.get_overview()
    overview["total_scripts"] = len(data.get("cards", []))
    overview["published"] = len([c for c in data.get("cards", []) if c.get("status") != "draft"])
    overview["drafts"] = overview["total_scripts"] - overview["published"]
    return jsonify(overview)


@app.route("/api/analytics/traffic")
@login_required
def api_analytics_traffic():
    days = request.args.get("days", 30, type=int)
    return jsonify(analytics.get_traffic_data(days))


@app.route("/api/analytics/popular")
@login_required
def api_analytics_popular():
    limit = request.args.get("limit", 10, type=int)
    return jsonify(analytics.get_popular_scripts(limit))


@app.route("/api/analytics/realtime")
@login_required
def api_analytics_realtime():
    return jsonify({"active_visitors": analytics.get_realtime_visitors()})


# Tracking endpoint (public - no auth required)
@app.route("/api/tracking", methods=["POST"])
def api_tracking():
    body = request.get_json(force=True)
    event = body.get("event", "page_view")
    ip = request.remote_addr

    if event == "page_view":
        analytics.log_page_view(
            page=body.get("page", "/"),
            referrer=body.get("referrer", ""),
            user_agent=body.get("user_agent", ""),
            ip=ip,
            country=body.get("country", ""),
            device=body.get("device", "desktop")
        )
    elif event == "script_click":
        analytics.log_script_click(
            script_id=body.get("script_id", ""),
            script_title=body.get("script_title", ""),
            ip=ip,
            referrer=body.get("referrer", "")
        )
    return jsonify({"ok": True})


# ============================================================
# Routes - Analytics Page
# ============================================================

@app.route("/analytics")
@login_required
def analytics_page():
    data = load_data()
    overview = analytics.get_overview()
    traffic = analytics.get_traffic_data(30)
    popular = analytics.get_popular_scripts(10)
    return render_template("analytics_page.html",
        overview=overview,
        traffic=traffic,
        popular=popular,
        total_scripts=len(data.get("cards", []))
    )


# ============================================================
# Routes - Settings
# ============================================================

@app.route("/settings")
@login_required
def settings_page():
    data = load_data()
    return render_template("settings.html",
        site=data.get("site", {}),
        github_configured=github_api.is_configured(),
        github_username=config.GITHUB_USERNAME,
        github_repo=config.GITHUB_REPO,
        discord_configured=bool(config.DISCORD_WEBHOOK_URL),
        telegram_configured=bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)
    )


@app.route("/api/settings", methods=["PUT"])
@login_required
def api_settings_update():
    body = request.get_json(force=True)
    data = load_data()
    if "site" not in data:
        data["site"] = {}
    for key in ["title", "subtitle", "accentColor", "footerText"]:
        if key in body:
            data["site"][key] = body[key]
    make_backup()
    save_data(data)
    log_activity("settings_update", "Updated site settings")
    return jsonify({"success": True})


# ============================================================
# API - Git / Deploy
# ============================================================

@app.route("/api/git/status")
@login_required
def api_git_status():
    status = git_push.get_git_status()
    return jsonify(status)


@app.route("/api/git/push", methods=["POST"])
@login_required
def api_git_push():
    body = request.get_json(force=True) if request.is_json else {}
    message = body.get("message", "Manual push from 27TechAI Dashboard")
    ok, msg = git_push.git_add_commit_push(message)
    log_activity("git_push", msg)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/git/pull", methods=["POST"])
@login_required
def api_git_pull():
    ok, msg = git_push.git_pull()
    log_activity("git_pull", msg)
    return jsonify({"success": ok, "message": msg})


# ============================================================
# Routes - Notifications
# ============================================================

@app.route("/api/notifications/test/discord", methods=["POST"])
@login_required
def api_test_discord():
    ok, msg = notifications.test_discord()
    log_activity("test_discord", msg)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/notifications/test/telegram", methods=["POST"])
@login_required
def api_test_telegram():
    ok, msg = notifications.test_telegram()
    log_activity("test_telegram", msg)
    return jsonify({"success": ok, "message": msg})


# ============================================================
# Routes - Backups
# ============================================================

@app.route("/backups")
@login_required
def backups_page():
    backups = []
    if os.path.exists(config.BACKUP_DIR):
        for fname in sorted(os.listdir(config.BACKUP_DIR), reverse=True):
            fpath = os.path.join(config.BACKUP_DIR, fname)
            stat = os.stat(fpath)
            # Extract timestamp from filename: data_20260101_120000.json
            ts = fname.replace("data_", "").replace(".json", "")
            backups.append({
                "filename": fname,
                "timestamp": ts,
                "size": stat.st_size,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    return render_template("backups.html", backups=backups)


@app.route("/api/backups/restore/<filename>", methods=["POST"])
@login_required
def api_backup_restore(filename):
    backup_path = os.path.join(config.BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        return jsonify({"success": False, "error": "Backup not found"}), 404
    # Backup current data first
    make_backup()
    shutil.copy2(backup_path, config.DATA_FILE)
    save_data(load_data())  # Re-save to trigger GitHub push
    log_activity("backup_restore", f"Restored from {filename}")
    return jsonify({"success": True})


@app.route("/api/backups/create", methods=["POST"])
@login_required
def api_backup_create():
    ok = make_backup()
    log_activity("backup_create", "Manual backup created")
    return jsonify({"success": ok})


# ============================================================
# Routes - Activity Log
# ============================================================

@app.route("/logs")
@login_required
def logs_page():
    logs = analytics.get_recent_activity(100)
    return render_template("logs.html", logs=logs)


# ============================================================
# SocketIO - Real-time
# ============================================================

@socketio.on("connect")
def handle_connect():
    if session.get("logged_in"):
        emit("stats_update", analytics.get_overview())


@socketio.on("request_stats")
def handle_request_stats():
    if session.get("logged_in"):
        emit("stats_update", analytics.get_overview())


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  27TechAI Dashboard")
    print("=" * 50)
    print(f"  Local:   http://localhost:{config.PORT}")
    print(f"  Network: http://0.0.0.0:{config.PORT}")
    print(f"  Login:   {config.ADMIN_USERNAME} / {config.ADMIN_PASSWORD}")
    print("=" * 50)
    socketio.run(app, host=config.HOST, port=config.PORT, debug=True, allow_unsafe_werkzeug=True)
