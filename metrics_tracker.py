"""
AgriSense AI - Metrics & Analytics Tracking
Tracks: page views, actions, predictions, pipeline transitions, errors
Stored in SQLite for persistence. Viewable via built-in dashboard.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "metrics.db"

def _connect():
    return sqlite3.connect(str(DB_PATH))

def init_metrics():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now','localtime')),
                event TEXT NOT NULL,
                category TEXT NOT NULL,
                actor TEXT DEFAULT 'anonymous',
                details TEXT DEFAULT '{}'
            )
        """)
        conn.commit()

def track(event, category, actor="anonymous", details=None):
    """Record a metric event. Non-blocking, silent on error."""
    init_metrics()
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO metrics (event, category, actor, details) VALUES (?,?,?,?)",
                (event, category, actor, json.dumps(details or {}))
            )
            conn.commit()
    except Exception:
        pass  # Never crash on metrics failure

def get_summary():
    """Return a dict of aggregated metrics for the dashboard."""
    init_metrics()
    try:
        with _connect() as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as c FROM metrics").fetchone()["c"]
            if total == 0:
                return {"total": 0}

            events = {}
            for row in conn.execute("SELECT event, COUNT(*) as c FROM metrics GROUP BY event ORDER BY c DESC LIMIT 10"):
                events[row["event"]] = row["c"]

            categories = {}
            for row in conn.execute("SELECT category, COUNT(*) as c FROM metrics GROUP BY category"):
                categories[row["category"]] = row["c"]

            last_event = conn.execute("SELECT event, timestamp FROM metrics ORDER BY id DESC LIMIT 1").fetchone()

            recent = []
            for row in conn.execute("SELECT event, actor, timestamp FROM metrics ORDER BY id DESC LIMIT 20"):
                recent.append({"event": row["event"], "actor": row["actor"], "time": row["timestamp"]})

            return {
                "total": total,
                "events": events,
                "categories": categories,
                "last_event": dict(last_event) if last_event else None,
                "recent": recent,
            }
    except Exception:
        return {"total": 0, "error": "Metrics unavailable"}


# ═══════════════ Convenience trackers ═══════════════

def track_page_view(page, actor="anonymous"):
    track(f"page:{page}", "navigation", actor)

def track_prediction(farmer, risk_pct, repay_pct, level):
    track("prediction", "ml", actor=farmer, details={
        "risk": round(risk_pct, 1),
        "repay": round(repay_pct, 1),
        "level": level
    })

def track_pipeline_transition(farmer, from_status, to_status, by="system"):
    track("pipeline", "workflow", actor=by, details={
        "farmer": farmer,
        "from": from_status,
        "to": to_status
    })

def track_submission(farmer, crop, ha, insurance):
    track("submitted", "workflow", actor=farmer, details={
        "crop": crop, "ha": ha, "insurance": insurance
    })

def track_decision(farmer, decision, by="bank"):
    track("decision", "workflow", actor=by, details={
        "farmer": farmer, "decision": decision
    })

def track_registration(farmer, region, ha):
    track("registered", "workflow", actor=farmer, details={
        "region": region, "ha": ha
    })
