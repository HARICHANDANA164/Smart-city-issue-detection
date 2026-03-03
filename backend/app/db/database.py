from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
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

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
        cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_verified INTEGER NOT NULL DEFAULT 1,
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

                CREATE TABLE IF NOT EXISTS otp_codes (
                    id TEXT PRIMARY KEY,
                    identifier TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    code TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column(conn, "users", "phone", "phone TEXT UNIQUE")
            self._ensure_column(conn, "users", "is_verified", "is_verified INTEGER NOT NULL DEFAULT 1")
            conn.commit()

    def create_otp(self, identifier: str, purpose: str, code: str, ttl_seconds: int = 300) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        with self._connect() as conn:
            conn.execute("DELETE FROM otp_codes WHERE identifier = ? AND purpose = ?", (identifier.lower(), purpose))
            conn.execute(
                "INSERT INTO otp_codes (id, identifier, purpose, code, expires_at, consumed_at, created_at) VALUES (?, ?, ?, ?, ?, NULL, ?)",
                (str(uuid4()), identifier.lower(), purpose, code, expires_at.isoformat(), now.isoformat()),
            )
            conn.commit()
        return {"identifier": identifier.lower(), "purpose": purpose, "expires_at": expires_at.isoformat()}

    def consume_otp(self, identifier: str, purpose: str, code: str) -> bool:
        now_iso = utc_now_iso()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, expires_at, consumed_at, code FROM otp_codes WHERE identifier = ? AND purpose = ? ORDER BY datetime(created_at) DESC LIMIT 1",
                (identifier.lower(), purpose),
            ).fetchone()
            if not row:
                return False
            if row["consumed_at"] is not None or row["code"] != code:
                return False
            if datetime.fromisoformat(row["expires_at"]).timestamp() < datetime.now(timezone.utc).timestamp():
                return False
            conn.execute("UPDATE otp_codes SET consumed_at = ? WHERE id = ?", (now_iso, row["id"]))
            conn.commit()
            return True

    def create_user(self, name: str, identifier: str, password_hash: str, role: str, is_verified: bool = True) -> dict[str, Any]:
        user_id = str(uuid4())
        created_at = utc_now_iso()
        is_email = "@" in identifier
        email = identifier.lower() if is_email else None
        phone = None if is_email else identifier
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users (id, name, email, phone, password_hash, role, is_verified, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, name, email, phone, password_hash, role, 1 if is_verified else 0, created_at),
            )
            conn.commit()
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": role,
            "is_verified": bool(is_verified),
            "created_at": created_at,
        }

    def get_user_by_identifier(self, identifier: str) -> sqlite3.Row | None:
        key = identifier.lower()
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (key, identifier)).fetchone()

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
                """SELECT i.*, u.name as reporter_name, COALESCE(u.email, u.phone, '') as reporter_contact
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

        sql = """SELECT i.*, u.name as reporter_name, COALESCE(u.email, u.phone, '') as reporter_contact
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
            pending = conn.execute("SELECT COUNT(*) AS c FROM issues WHERE status IN ('Pending', 'Not Started')").fetchone()["c"]
            completed = conn.execute("SELECT COUNT(*) AS c FROM issues WHERE status = 'Completed'").fetchone()["c"]
        return {"total_issues": total, "pending": pending, "completed": completed}
