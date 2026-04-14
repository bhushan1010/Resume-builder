"""
database.py  –  SQLite-based user accounts, profile, and resume storage
"""

import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db")


def _get_db():
    """Get a database connection with row factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            profile_data TEXT NOT NULL,
            is_default INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            profile_id INTEGER,
            company TEXT NOT NULL,
            job_description TEXT NOT NULL,
            template TEXT NOT NULL DEFAULT 'jakes',
            max_pages INTEGER NOT NULL DEFAULT 1,
            ats_score INTEGER,
            pdf_path TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id);
        CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id);
    """)
    conn.commit()
    conn.close()


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt. Returns (hash, salt)."""
    if salt is None:
        salt = secrets.token_hex(32)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return pw_hash, salt


def create_user(email: str, password: str, name: str) -> dict:
    """Create a new user. Returns user dict or raises ValueError."""
    conn = _get_db()
    try:
        pw_hash, salt = _hash_password(password)
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, salt, name) VALUES (?, ?, ?, ?)",
            (email.lower(), pw_hash, salt, name),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        raise ValueError(f"User with email '{email}' already exists.")
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict | None:
    """Authenticate user. Returns user dict or None."""
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower(),)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    pw_hash, _ = _hash_password(password, row["salt"])
    if pw_hash != row["password_hash"]:
        return None

    conn = _get_db()
    conn.execute(
        "UPDATE users SET last_login = datetime('now') WHERE id = ?",
        (row["id"],),
    )
    conn.commit()
    conn.close()

    return dict(row)


def create_session(user_id: int, ttl_hours: int = 72) -> str:
    """Create a session token. Returns the token string."""
    token = secrets.token_urlsafe(48)
    expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()

    conn = _get_db()
    conn.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at),
    )
    conn.commit()
    conn.close()
    return token


def validate_session(token: str) -> dict | None:
    """Validate a session token. Returns user dict or None."""
    conn = _get_db()
    row = conn.execute(
        """SELECT u.* FROM users u
           JOIN sessions s ON u.id = s.user_id
           WHERE s.token = ? AND s.expires_at > datetime('now')""",
        (token,),
    ).fetchone()

    if row:
        conn.execute(
            "UPDATE sessions SET expires_at = datetime('now', '+72 hours') WHERE token = ?",
            (token,),
        )
        conn.commit()

    conn.close()
    return dict(row) if row else None


def delete_session(token: str):
    """Delete a session (logout)."""
    conn = _get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def save_profile(user_id: int, name: str, profile_data: dict, is_default: bool = False) -> int:
    """Save a profile. Returns profile id."""
    conn = _get_db()
    if is_default:
        conn.execute(
            "UPDATE profiles SET is_default = 0 WHERE user_id = ?",
            (user_id,),
        )
    cursor = conn.execute(
        """INSERT INTO profiles (user_id, name, profile_data, is_default)
           VALUES (?, ?, ?, ?)""",
        (user_id, name, json.dumps(profile_data), int(is_default)),
    )
    conn.commit()
    profile_id = cursor.lastrowid
    conn.close()
    return profile_id


def get_profiles(user_id: int) -> list[dict]:
    """Get all profiles for a user."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM profiles WHERE user_id = ? ORDER BY is_default DESC, updated_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_profile(user_id: int, profile_id: int) -> dict | None:
    """Get a specific profile."""
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM profiles WHERE id = ? AND user_id = ?",
        (profile_id, user_id),
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["profile_data"] = json.loads(result["profile_data"])
        return result
    return None


def delete_profile(user_id: int, profile_id: int) -> bool:
    """Delete a profile. Returns True if deleted."""
    conn = _get_db()
    cursor = conn.execute(
        "DELETE FROM profiles WHERE id = ? AND user_id = ?",
        (profile_id, user_id),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def save_resume(user_id: int, company: str, job_description: str,
                template: str = "jakes", max_pages: int = 1,
                profile_id: int = None, ats_score: int = None,
                pdf_path: str = None) -> int:
    """Save a generated resume record. Returns resume id."""
    conn = _get_db()
    cursor = conn.execute(
        """INSERT INTO resumes (user_id, profile_id, company, job_description,
           template, max_pages, ats_score, pdf_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, profile_id, company, job_description, template, max_pages, ats_score, pdf_path),
    )
    conn.commit()
    resume_id = cursor.lastrowid
    conn.close()
    return resume_id


def get_resumes(user_id: int, limit: int = 50) -> list[dict]:
    """Get resume history for a user."""
    conn = _get_db()
    rows = conn.execute(
        """SELECT r.*, p.name as profile_name
           FROM resumes r
           LEFT JOIN profiles p ON r.profile_id = p.id
           WHERE r.user_id = ?
           ORDER BY r.created_at DESC
           LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_resume(user_id: int, resume_id: int) -> dict | None:
    """Get a specific resume record."""
    conn = _get_db()
    row = conn.execute(
        """SELECT r.*, p.name as profile_name, p.profile_data
           FROM resumes r
           LEFT JOIN profiles p ON r.profile_id = p.id
           WHERE r.id = ? AND r.user_id = ?""",
        (resume_id, user_id),
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        if result.get("profile_data"):
            result["profile_data"] = json.loads(result["profile_data"])
        return result
    return None


def get_user_by_id(user_id: int) -> dict | None:
    """Get user by ID."""
    conn = _get_db()
    row = conn.execute("SELECT id, email, name, created_at, last_login FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
