from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS issues (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    image_path TEXT,
                    resolution_image_path TEXT,
                    resolution_comment TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS status_updates (
                    id TEXT PRIMARY KEY,
                    issue_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (issue_id) REFERENCES issues(id)
                );
                """
            )
            conn.commit()

    def create_user(self, name: str, email: str, password_hash: str, role: str) -> dict[str, Any]:
        user_id = str(uuid4())
        created_at = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, name, email.lower(), password_hash, role, created_at),
            )
            conn.commit()
        return {"id": user_id, "name": name, "email": email.lower(), "role": role, "created_at": created_at}

    def get_user_by_email(self, email: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()

    def get_user_by_id(self, user_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def create_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        issue_id = str(uuid4())
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO issues
                (id, user_id, title, description, category, status, latitude, longitude, image_path, resolution_image_path, resolution_comment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)""",
                (
                    issue_id,
                    payload["user_id"],
                    payload["title"],
                    payload["description"],
                    payload["category"],
                    "Pending",
                    payload["latitude"],
                    payload["longitude"],
                    payload.get("image_path"),
                    now,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO status_updates (id, issue_id, old_status, new_status, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), issue_id, None, "Pending", "Issue created", now),
            )
            conn.commit()
        return self.get_issue(issue_id)

    def get_issue(self, issue_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT i.*, u.name as reporter_name, u.email as reporter_email
                FROM issues i JOIN users u ON i.user_id = u.id WHERE i.id = ?""",
                (issue_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_issues(self, filters: dict[str, Any], limit: int, offset: int) -> list[dict[str, Any]]:
        where = []
        params: list[Any] = []
        if filters.get("status"):
            where.append("i.status = ?")
            params.append(filters["status"])
        if filters.get("category"):
            where.append("i.category = ?")
            params.append(filters["category"])
        if filters.get("search"):
            where.append("(i.title LIKE ? OR i.description LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

        sql = """SELECT i.*, u.name as reporter_name, u.email as reporter_email
                 FROM issues i JOIN users u ON i.user_id = u.id"""
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY datetime(i.created_at) DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def delete_issue(self, issue_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM status_updates WHERE issue_id = ?", (issue_id,))
            conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
            conn.commit()

    def update_issue_status(self, issue_id: str, status: str, comment: str | None, resolution_image_path: str | None) -> dict[str, Any] | None:
        issue = self.get_issue(issue_id)
        if not issue:
            return None
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE issues SET status = ?, resolution_comment = COALESCE(?, resolution_comment), resolution_image_path = COALESCE(?, resolution_image_path), updated_at = ? WHERE id = ?",
                (status, comment, resolution_image_path, now, issue_id),
            )
            conn.execute(
                "INSERT INTO status_updates (id, issue_id, old_status, new_status, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), issue_id, issue["status"], status, comment, now),
            )
            conn.commit()
        return self.get_issue(issue_id)

    def list_status_updates(self, issue_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, old_status, new_status, comment, created_at FROM status_updates WHERE issue_id = ? ORDER BY datetime(created_at) ASC",
                (issue_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def analytics(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM issues").fetchone()["c"]
            pending = conn.execute("SELECT COUNT(*) AS c FROM issues WHERE status = 'Pending'").fetchone()["c"]
            completed = conn.execute("SELECT COUNT(*) AS c FROM issues WHERE status = 'Completed'").fetchone()["c"]
        return {"total_issues": total, "pending": pending, "completed": completed}
