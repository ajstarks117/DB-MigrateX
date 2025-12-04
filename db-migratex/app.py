# app.py
from flask import Flask, render_template, redirect, url_for
import os

from config import DB_CONFIG
from migrmgr.state import DatabaseState
from migrmgr.parser import parse_migrations
from migrmgr.planner import MigrationPlanner
from migrmgr.executor import MigrationExecutor

from legacy.importer_sql import LegacyImporter
from normalizer.normalizer import SchemaNormalizer
from normalizer.migrator import DataMigrator
from db import MySQLAdapter

app = Flask(__name__)


@app.route("/")
def index():
    state = DatabaseState()
    migrations = parse_migrations("migrations")
    applied = state.get_applied_migrations()
    planner = MigrationPlanner(applied)
    pending_plan = planner.build_plan(migrations)
    pending = [m.id for m in pending_plan]
    state.close()
    return render_template("index.html", applied=applied, pending=pending)


@app.route("/apply")
def apply_migrations():
    state = DatabaseState()
    executor = MigrationExecutor()
    migrations = parse_migrations("migrations")
    applied = state.get_applied_migrations()
    planner = MigrationPlanner(applied)
    plan = planner.build_plan(migrations)

    if not plan:
        msg = "No pending migrations."
    else:
        msgs = []
        for m in plan:
            try:
                executor.apply_migration(m, user="flask-ui", force=True, skip_integrity=True)
                msgs.append(f"Applied {m.id}")
            except Exception as e:
                msgs.append(f"Failed {m.id}: {e}")
                executor.close()
                state.close()
                return "<br>".join(msgs)
        msg = "<br>".join(msgs)

    executor.close()
    state.close()
    return msg


@app.route("/legacy/import")
def legacy_import():
    importer = LegacyImporter()
    path = os.path.join("legacy", "boxpro_data", "students.bxp")
    importer.import_students(path)
    importer.close()
    return "Legacy BoxPro students imported into raw_students."


@app.route("/normalize/analyze")
def normalize_analyze():
    # read from raw_students table
    db = MySQLAdapter(DB_CONFIG)
    db.connect()
    rows = db.fetchall("SELECT legacy_id, name, age, department FROM raw_students")
    db.close()

    norm = SchemaNormalizer().analyze(rows)

    return render_template(
        "normalize.html",
        columns=norm["columns"],
        fds=norm["functional_dependencies"],
        repeating=norm["repeating_groups"],
        duplicates=norm["duplicates"],
    )


@app.route("/normalize/migrate")
def normalize_migrate():
    migrator = DataMigrator()
    migrator.migrate_raw_students_to_norm()
    migrator.close()
    return "Data migrated from raw_students to students_norm."


if __name__ == "__main__":
    app.run(debug=True)
