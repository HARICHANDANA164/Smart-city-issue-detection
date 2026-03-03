from __future__ import annotations

from app.db.database import Database


class DashboardController:
    def __init__(self, db: Database) -> None:
        self.db = db

    def analytics(self):
        return self.db.analytics()
