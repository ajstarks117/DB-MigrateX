# migrmgr/state.py
from typing import List
from db import MySQLAdapter
from config import DB_CONFIG


class DatabaseState:
    def __init__(self, _conf=None):
        self.db = MySQLAdapter(DB_CONFIG)
        self.db.connect()
        self.db.ensure_schema_versions()

    def get_applied_migrations(self) -> List[str]:
        return self.db.get_applied_ids()

    def close(self):
        self.db.close()
