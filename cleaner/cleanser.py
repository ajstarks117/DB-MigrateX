# cleaner/cleanser.py
import mysql.connector
import yaml
import os
import re
from config import DB_CONFIG
from utils.forensics import recorder

class DataCleanser:
    def __init__(self):
        target = DB_CONFIG["TARGET"]
        self.conn = mysql.connector.connect(
            host=target["HOST"],
            port=target["PORT"],
            user=target["USER"],
            password=target["PASSWORD"],
            database=target["DATABASE_NAME"]
        )
        self.cur = self.conn.cursor(dictionary=True)
        self.rules = self._load_rules()

    def _load_rules(self):
        """Loads the YAML validation rules."""
        if not os.path.exists("rules.yaml"):
            print("⚠️ No rules.yaml found. Skipping rule-based checks.")
            return {}
        with open("rules.yaml", "r") as f:
            return yaml.safe_load(f)

    def run_diagnostics(self):
        print("🔍 Running Smart Data Quality Diagnostics...")
        
        try:
            # 1. Run Standard System Checks (Duplicates)
            self.check_duplicates_system()

            # 2. Run Configured Rules from YAML
            for table, columns in self.rules.items():
                print(f"   👉 Checking rules for table: {table}")
                for col, rules in columns.items():
                    for rule in rules:
                        self.apply_rule(table, col, rule)

        except Exception as e:
            recorder.log_error("CLEANER", str(e))
            print(f"❌ Error during cleaning: {e}")
        finally:
            self.cur.close()
            self.conn.close()
            print("✅ Diagnostics complete.")

    # --- Core Check Logic ---

    def check_duplicates_system(self):
        """Auto-detects duplicates based on primary key conventions."""
        tables = ["customers", "orders", "employees", "products"]
        for t in tables:
            pk = None
            if t == "customers": pk = "CUST_ID"
            elif t == "orders": pk = "ORDER_ID"
            elif t == "employees": pk = "EMP_ID"
            elif t == "products": pk = "PROD_ID"
            
            if pk:
                query = f"SELECT {pk}, COUNT(*) as cnt FROM {t} GROUP BY {pk} HAVING cnt > 1"
                self.cur.execute(query)
                dupes = self.cur.fetchall()
                if dupes:
                    recorder.log_quality_issue(t, "DUPLICATE_PK", f"Found {len(dupes)} duplicate IDs")

    def apply_rule(self, table, col, rule):
        """Dispatches the rule to the correct checking function."""
        rtype = rule['type']
        msg = rule.get('msg', 'Validation Failed')

        if rtype == 'required':
            self._check_required(table, col, msg)
        elif rtype == 'range':
            self._check_range(table, col, rule.get('min'), rule.get('max'), msg)
        elif rtype == 'regex':
            self._check_regex(table, col, rule.get('pattern'), msg)
        elif rtype == 'enum':
            self._check_enum(table, col, rule.get('values'), msg)

    # --- Individual Rule Implementations ---

    def _check_required(self, table, col, msg):
        # FIX: Handle MySQL Error 1525 (Comparing DATE to empty string)
        try:
            # Try checking for both NULL and Empty String (standard for text)
            query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {col} IS NULL OR {col} = ''"
            self.cur.execute(query)
            cnt = self.cur.fetchone()['cnt']
        except mysql.connector.Error as err:
            # If MySQL complains about incorrect DATE value, strictly check for NULL only
            if err.errno == 1525: 
                query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {col} IS NULL"
                self.cur.execute(query)
                cnt = self.cur.fetchone()['cnt']
            else:
                raise err # Raise any other unexpected error

        if cnt > 0:
            recorder.log_quality_issue(table, "MISSING_VALUE", f"{msg} ({cnt} rows)")

    def _check_range(self, table, col, min_val, max_val, msg):
        conditions = []
        if min_val is not None: conditions.append(f"{col} < {min_val}")
        if max_val is not None: conditions.append(f"{col} > {max_val}")
        
        if conditions:
            query = f"SELECT COUNT(*) as cnt FROM {table} WHERE " + " OR ".join(conditions)
            self.cur.execute(query)
            cnt = self.cur.fetchone()['cnt']
            if cnt > 0:
                recorder.log_quality_issue(table, "OUT_OF_RANGE", f"{msg} ({cnt} rows)")

    def _check_regex(self, table, col, pattern, msg):
        query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {col} NOT REGEXP '{pattern}' AND {col} IS NOT NULL"
        self.cur.execute(query)
        cnt = self.cur.fetchone()['cnt']
        if cnt > 0:
            recorder.log_quality_issue(table, "INVALID_FORMAT", f"{msg} ({cnt} rows)")

    def _check_enum(self, table, col, allowed_values, msg):
        safe_values = [f"'{v}'" for v in allowed_values]
        val_str = ", ".join(safe_values)
        
        query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {col} NOT IN ({val_str}) AND {col} IS NOT NULL"
        self.cur.execute(query)
        cnt = self.cur.fetchone()['cnt']
        if cnt > 0:
            recorder.log_quality_issue(table, "INVALID_CHOICE", f"{msg} ({cnt} rows)")