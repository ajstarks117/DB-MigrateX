# dashboard.py
from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

REPORT_FILE = "forensic_report.json"

def load_data():
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, 'r') as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def stats():
    """Returns JSON data for the dashboard to consume."""
    data = load_data()
    
    # Process data for Charts
    migration = data.get("migration_stats", {})
    
    # 1. Bar Chart Data (Rows per Table)
    labels = list(migration.keys())
    values = [info.get("rows", 0) for info in migration.values()]
    
    # 2. Status Counts (Success vs Fail)
    errors = len(data.get("errors", []))
    quality_issues = len(data.get("data_quality_issues", []))
    
    response = {
        "raw": data,
        "charts": {
            "labels": labels,
            "row_counts": values,
            "quality_score": [errors, quality_issues] 
        }
    }
    return jsonify(response)

if __name__ == '__main__':
    print("🚀 Modern Dashboard running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)