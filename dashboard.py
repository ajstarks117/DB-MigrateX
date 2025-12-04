# dashboard.py
from flask import Flask, render_template, jsonify
import json
import os
import threading
from app import main as run_migration_pipeline  # Import your existing main logic

app = Flask(__name__)

REPORT_FILE = "forensic_report.json"

def load_report():
    if not os.path.exists(REPORT_FILE):
        return {"error": "No report found. Run migration first."}
    with open(REPORT_FILE, "r") as f:
        return json.load(f)

@app.route("/")
def index():
    data = load_report()
    return render_template("dashboard.html", data=data)

@app.route("/run_migration", methods=["POST"])
def trigger_migration():
    # Run in separate thread so UI doesn't freeze
    thread = threading.Thread(target=run_migration_pipeline)
    thread.start()
    return jsonify({"status": "Migration started", "message": "Watch logs for progress"})

@app.route("/api/stats")
def get_stats():
    return jsonify(load_report())

if __name__ == "__main__":
    app.run(debug=True, port=5000)