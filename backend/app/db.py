from __future__ import annotations

"""
SQLite persistence for local demos.

Design note:
- This is intentionally small and can be replaced later with DynamoDB.
- All DB access is encapsulated so swapping storage backends is straightforward.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .schemas import ComplaintRecord


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ComplaintRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS complaints (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    urgency TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create(self, text: str, category: str, urgency: str) -> ComplaintRecord:
        complaint_id = str(uuid4())
        created_at = _utc_now()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO complaints (id, created_at, text, category, urgency)
                VALUES (?, ?, ?, ?, ?)
                """,
                (complaint_id, created_at.isoformat(), text, category, urgency),
            )
            conn.commit()

        return ComplaintRecord(
            id=complaint_id,
            created_at=created_at,
            text=text,
            category=category,  # type: ignore[arg-type]
            urgency=urgency,  # type: ignore[arg-type]
        )

    def list(
        self,
        category: str | None = None,
        urgency: str | None = None,
        limit: int = 200,
    ) -> list[ComplaintRecord]:
        where = []
        params: list[object] = []

        if category:
            where.append("category = ?")
            params.append(category)
        if urgency:
            where.append("urgency = ?")
            params.append(urgency)

        sql = "SELECT id, created_at, text, category, urgency FROM complaints"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY datetime(created_at) DESC"
        sql += " LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        items: list[ComplaintRecord] = []
        for r in rows:
            items.append(
                ComplaintRecord(
                    id=r["id"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    text=r["text"],
                    category=r["category"],  # type: ignore[arg-type]
                    urgency=r["urgency"],  # type: ignore[arg-type]
                )
            )
        return items

