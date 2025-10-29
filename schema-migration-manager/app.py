from flask import Flask, render_template
from migrmgr.state import DatabaseState
from migrmgr.parser import parse_migrations
from migrmgr.planner import MigrationPlanner
from migrmgr.cli import db_config
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.ERROR)

# Set the migrations directory relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")

@app.route('/')
def index():
    if not os.path.exists(MIGRATIONS_DIR):
        logging.error(f"Directory '{MIGRATIONS_DIR}' does not exist.")
        return "Error: Migrations directory not found.", 500

    state = DatabaseState(db_config)
    # Use the parser helper to obtain Migration objects and then build a plan
    migrations = parse_migrations(MIGRATIONS_DIR)
    planner = MigrationPlanner(state.get_applied_migrations())
    pending_plan = planner.build_plan(migrations)

    applied = state.get_applied_migrations()
    pending = [m.id for m in pending_plan]

    state.close()
    return render_template('index.html', applied=applied, pending=pending)


if __name__ == "__main__":
    app.run(debug=True)