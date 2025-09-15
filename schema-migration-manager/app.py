from flask import Flask, render_template
from migrmgr.state import DatabaseState
from migrmgr.parser import MigrationParser
from migrmgr.planner import MigrationPlanner
from migrmgr.cli import db_config
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.ERROR)

@app.route('/')
def index():
    state = DatabaseState(db_config)
    parser = MigrationParser("migrations")
    planner = MigrationPlanner(state.get_applied_migrations(), parser.get_migration_files())

    applied = state.get_applied_migrations()
    pending = [version for version, _ in planner.get_pending_migrations()]

    state.close()
    return render_template('index.html', applied=applied, pending=pending)


if __name__ == "__main__":
    app.run(debug=True)
