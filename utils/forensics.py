    # utils/forensics.py
import json
import logging
import time
from datetime import datetime

# Configure standard text logging
logging.basicConfig(
    filename='migration.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ForensicLab:
    def __init__(self):
        self.report_path = "forensic_report.json"
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "migration_stats": {},
            "normalization_stats": {},
            "errors": [],
            "data_quality_issues": []
        }

    def log_migration(self, table, row_count, status="SUCCESS"):
        self.stats["migration_stats"][table] = {
            "rows": row_count,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        logging.info(f"MIGRATION: {table} - {row_count} rows - {status}")

    def log_error(self, context, error_msg):
        error_entry = {"context": context, "error": str(error_msg), "time": datetime.now().isoformat()}
        self.stats["errors"].append(error_entry)
        logging.error(f"ERROR in {context}: {error_msg}")

    def log_quality_issue(self, table, issue_type, details):
        self.stats["data_quality_issues"].append({
            "table": table,
            "type": issue_type,
            "details": details
        })

    def save_report(self):
        self.stats["end_time"] = datetime.now().isoformat()
        with open(self.report_path, "w") as f:
            json.dump(self.stats, f, indent=4)
        print(f"📁 Forensic report saved to {self.report_path}")

# Global instance to be used everywhere
recorder = ForensicLab()