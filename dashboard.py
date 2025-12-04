import os
import json
import time
from flask import Flask, render_template, jsonify, request
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER
from migrmgr.executor_mysql import MySQLMigrationExecutor
from cleaner.cleanser import DataCleanser
from normalizer.normalizer import NormalizationExecutor
from utils.forensics import recorder
from analysis.nds_calculator import calculate_nds

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

REPORT_FILE = "forensic_report.json"

def load_data():
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, 'r') as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    return render_template('dashboard.html')

# --- API: 1. Upload Files ---
@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    files = request.files.getlist('files[]')
    
    # Clear old uploads to avoid mixing data
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))

    saved = []
    for file in files:
        if file and file.filename.lower().endswith('.dbf'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            saved.append(filename)
    
    return jsonify({"status": "success", "count": len(saved), "files": saved})

# --- API: 2. Convert (Migrate + NDS Score) ---
@app.route('/api/step/migrate', methods=['POST'])
def step_migrate():
    try:
        mig = MySQLMigrationExecutor()
        mig.setup_database_and_schema()
        tables = mig.list_tables()
        
        # 1. Run NDS Analysis on raw files BEFORE migration
        for t in tables:
            rows_gen = mig.importer.get_table_rows(t, batch_size=500)
            try:
                first_batch = next(rows_gen)
                if first_batch:
                    score, notes = calculate_nds(t, first_batch)
                    details = f"Score: {score}/100. " + (" ".join(notes) if notes else "Structure looks good.")
                    recorder.log_quality_issue(t, "NDS_SCORE", details)
            except StopIteration:
                pass

        # 2. Run Migration
        for t in tables:
            mig.migrate_single_table(t)
            
        recorder.save_report()
        return jsonify({"status": "success", "message": "Migration & NDS Analysis Complete"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- API: 3. Analyze (Quality) ---
@app.route('/api/step/analyze', methods=['POST'])
def step_analyze():
    try:
        cleaner = DataCleanser()
        cleaner.run_diagnostics()
        recorder.save_report()
        return jsonify({"status": "success", "message": "Data Quality Scan Complete"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- API: 4. Normalize ---
@app.route('/api/step/normalize', methods=['POST'])
def step_normalize():
    try:
        norm = NormalizationExecutor()
        norm.run_full_normalization()
        recorder.save_report()
        return jsonify({"status": "success", "message": "Normalization Complete"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- API: Get Stats (Polled by UI) ---
@app.route('/api/stats')
def stats():
    data = load_data()
    migration = data.get("migration_stats", {})
    
    labels = list(migration.keys())
    values = [info.get("rows", 0) for info in migration.values()]
    errors = len(data.get("errors", []))
    quality_issues = len(data.get("data_quality_issues", []))
    
    return jsonify({
        "raw": data,
        "charts": {
            "labels": labels,
            "row_counts": values,
            "quality_score": [errors, quality_issues] 
        }
    })

if __name__ == '__main__':
    print("🚀 DB-MigrateX Dashboard running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)