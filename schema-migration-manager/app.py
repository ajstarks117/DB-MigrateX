from flask import Flask, render_template
from migrmgr.state import DatabaseState
from migrmgr.parser import MigrationParser
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
    parser = MigrationParser(MIGRATIONS_DIR)
    planner = MigrationPlanner(state.get_applied_migrations(), parser.get_migration_files())

    applied = state.get_applied_migrations()
    pending = [version for version, _ in planner.get_pending_migrations()]

    state.close()
    return render_template('index.html', applied=applied, pending=pending)


if __name__ == "__main__":
    app.run(debug=True)