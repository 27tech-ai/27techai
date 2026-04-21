import sqlite3
import os
import json
from datetime import datetime, timedelta
from config import ANALYTICS_DB


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(ANALYTICS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize analytics database"""
    os.makedirs(os.path.dirname(ANALYTICS_DB), exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            page TEXT,
            referrer TEXT,
            user_agent TEXT,
            ip TEXT,
            country TEXT,
            device TEXT
        );

        CREATE TABLE IF NOT EXISTS script_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            script_id TEXT,
            script_title TEXT,
            ip TEXT,
            referrer TEXT
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            details TEXT,
            user TEXT
        );

        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE PRIMARY KEY,
            page_views INTEGER DEFAULT 0,
            unique_visitors INTEGER DEFAULT 0,
            script_clicks INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


def log_page_view(page="/", referrer="", user_agent="", ip="", country="", device=""):
    """Log a page view"""
    conn = get_db()
    conn.execute(
        "INSERT INTO page_views (page, referrer, user_agent, ip, country, device) VALUES (?, ?, ?, ?, ?, ?)",
        (page, referrer, user_agent, ip, country, device)
    )
    # Update daily stats
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO daily_stats (date, page_views, unique_visitors, script_clicks)
        VALUES (?, 1, 0, 0)
        ON CONFLICT(date) DO UPDATE SET page_views = page_views + 1
    """, (today,))
    conn.commit()
    conn.close()


def log_script_click(script_id, script_title, ip="", referrer=""):
    """Log a script click"""
    conn = get_db()
    conn.execute(
        "INSERT INTO script_clicks (script_id, script_title, ip, referrer) VALUES (?, ?, ?, ?)",
        (script_id, script_title, ip, referrer)
    )
    # Update daily stats
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO daily_stats (date, page_views, unique_visitors, script_clicks)
        VALUES (?, 0, 0, 1)
        ON CONFLICT(date) DO UPDATE SET script_clicks = script_clicks + 1
    """, (today,))
    conn.commit()
    conn.close()


def log_activity(action, details="", user="admin"):
    """Log dashboard activity"""
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_log (action, details, user) VALUES (?, ?, ?)",
        (action, details, user)
    )
    conn.commit()
    conn.close()


def get_overview():
    """Get dashboard overview stats"""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    total_views = conn.execute("SELECT COALESCE(SUM(page_views), 0) FROM daily_stats").fetchone()[0]
    week_views = conn.execute(
        "SELECT COALESCE(SUM(page_views), 0) FROM daily_stats WHERE date >= ?", (week_ago,)
    ).fetchone()[0]
    total_clicks = conn.execute("SELECT COALESCE(SUM(script_clicks), 0) FROM daily_stats").fetchone()[0]
    week_clicks = conn.execute(
        "SELECT COALESCE(SUM(script_clicks), 0) FROM daily_stats WHERE date >= ?", (week_ago,)
    ).fetchone()[0]

    conn.close()
    return {
        "total_views": total_views,
        "week_views": week_views,
        "total_clicks": total_clicks,
        "week_clicks": week_clicks,
    }


def get_traffic_data(days=30):
    """Get daily traffic data for charts"""
    conn = get_db()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT date, page_views, script_clicks FROM daily_stats WHERE date >= ? ORDER BY date",
        (since,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_popular_scripts(limit=10):
    """Get most clicked scripts"""
    conn = get_db()
    rows = conn.execute("""
        SELECT script_id, script_title, COUNT(*) as clicks
        FROM script_clicks
        GROUP BY script_id
        ORDER BY clicks DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_activity(limit=50):
    """Get recent activity log"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_realtime_visitors():
    """Get count of visitors in last 5 minutes"""
    conn = get_db()
    five_min_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    count = conn.execute(
        "SELECT COUNT(DISTINCT ip) FROM page_views WHERE timestamp >= ?", (five_min_ago,)
    ).fetchone()[0]
    conn.close()
    return count
