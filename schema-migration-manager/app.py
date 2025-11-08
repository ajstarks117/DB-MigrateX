from flask import Flask, render_template
from migrmgr.state import DatabaseState
from migrmgr.parser import parse_migrations
from migrmgr.planner import MigrationPlanner
from migrmgr.cli import db_config
from migrmgr.executor import MigrationExecutor
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Path to migrations folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")


@app.route("/")
def index():
    """Homepage: show applied and pending migrations"""

    if not os.path.exists(MIGRATIONS_DIR):
        return "❌ Migrations directory not found", 500

    # load DB state (schema_versions)
    state = DatabaseState(db_config)

    # ALL migrations from folder
    migrations = parse_migrations(MIGRATIONS_DIR)

    # already applied
    applied = state.get_applied_migrations()

    # build dependency plan
    planner = MigrationPlanner(applied)
    pending_plan = planner.build_plan(migrations)

    pending = [m.id for m in pending_plan]  # list of only IDs

    state.close()

    return render_template(
        "index.html",
        applied=applied,
        pending=pending
    )


@app.route("/apply")
def apply_migrations():
    """Apply all pending migrations"""

    # load db state + executor
    state = DatabaseState(db_config)
    executor = MigrationExecutor(db_config)  # ✅ using latest working adapter

    # load migration files
    migrations = parse_migrations(MIGRATIONS_DIR)
    applied = state.get_applied_migrations()

    # get plan for only pending migrations
    planner = MigrationPlanner(applied)
    pending_plan = planner.build_plan(migrations)

    if not pending_plan:
        state.close()
        executor.close()
        return "✅ No pending migrations. Database is already up to date."

    output = []

    # apply in order
    for mig in pending_plan:
        try:
            executor.apply_migration(mig, user="flask-ui")
            output.append(f"✅ Applied {mig.id} — {mig.filename}")
        except Exception as e:
            output.append(f"❌ Failed {mig.id}: {e}")
            executor.close()
            state.close()
            return "<br>".join(output)

    executor.close()
    state.close()

    output.append("<br>✅ All migrations applied successfully!")
    return "<br>".join(output)


@app.route("/reset")
def reset_db():
    import mysql.connector
    from mysql.connector import errorcode

    dbname = db_config.get("dbname")
    user = db_config.get("user")
    password = db_config.get("password")
    host = db_config.get("host")
    port = db_config.get("port")

    try:
        # Connect without database first
        conn = mysql.connector.connect(
            user=user, password=password, host=host, port=port
        )
        cursor = conn.cursor()

        # Drop DB
        cursor.execute(f"DROP DATABASE IF EXISTS {dbname}")
        cursor.execute(f"CREATE DATABASE {dbname}")

        conn.commit()
        cursor.close()
        conn.close()

        return "✅ Database has been reset successfully!<br>Go back and refresh the homepage."

    except Exception as e:
        return f"❌ ERROR resetting DB: {e}"


if __name__ == "__main__":
    app.run(debug=True)
