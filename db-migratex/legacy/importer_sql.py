# legacy/importer_sql.py
from config import DB_CONFIG
from db import MySQLAdapter
from .parser_boxpro import parse_boxpro_file
from .transformer import transform_student_record
import os


class LegacyImporter:
    def __init__(self):
        self.db = MySQLAdapter(DB_CONFIG)
        self.db.connect()

    def import_students(self, boxpro_path: str):
        if not os.path.exists(boxpro_path):
            raise FileNotFoundError(boxpro_path)

        records = parse_boxpro_file(boxpro_path)
        rows = [transform_student_record(r) for r in records]

        for r in rows:
            self.db.execute(
                """
                INSERT INTO raw_students(legacy_id, name, age, department)
                VALUES (%s, %s, %s, %s)
                """,
                (r["legacy_id"], r["name"], r["age"], r["department"]),
            )
        self.db.commit()

    def close(self):
        self.db.close()
