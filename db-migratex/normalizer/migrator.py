# normalizer/migrator.py
from config import DB_CONFIG
from db import MySQLAdapter


class DataMigrator:
    def __init__(self):
        self.db = MySQLAdapter(DB_CONFIG)
        self.db.connect()

    def migrate_raw_students_to_norm(self):
        rows = self.db.fetchall("SELECT legacy_id, name, age, department FROM raw_students")

        for r in rows:
            self.db.execute(
                """
                INSERT INTO students_norm(legacy_id, name, age, department)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    age = VALUES(age),
                    department = VALUES(department)
                """,
                (r["legacy_id"], r["name"], r["age"], r["department"]),
            )
        self.db.commit()

    def close(self):
        self.db.close()
