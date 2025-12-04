# cleaner/cleanser.py
import mysql.connector
from config import DB_CONFIG
from utils.forensics import recorder

class DataCleanser:
    def __init__(self):
        cfg = DB_CONFIG["TARGET"]
        self.conn = mysql.connector.connect(
            host=cfg["HOST"],
            user=cfg["USER"],
            password=cfg["PASSWORD"],
            database=cfg["DATABASE_NAME"]
        )
        self.cur = self.conn.cursor(dictionary=True)

    def scan_duplicates(self, table, key_column):
        """Finds rows with same ID."""
        query = f"""
            SELECT {key_column}, COUNT(*) as cnt 
            FROM {table} 
            GROUP BY {key_column} 
            HAVING cnt > 1
        """
        self.cur.execute(query)
        dupes = self.cur.fetchall()
        for d in dupes:
            recorder.log_quality_issue(table, "DUPLICATE_ID", f"ID {d[key_column]} appears {d['cnt']} times")
        return len(dupes)

    def scan_nulls(self, table, required_cols):
        """Finds rows with NULLs in critical columns."""
        for col in required_cols:
            query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {col} IS NULL"
            self.cur.execute(query)
            res = self.cur.fetchone()
            if res['cnt'] > 0:
                recorder.log_quality_issue(table, "NULL_VALUE", f"Column {col} has {res['cnt']} NULLs")

    def run_full_scan(self):
        print("🔍 Starting Data Quality Scan...")
        
        # Define rules per table
        self.scan_duplicates("customers", "CUST_ID")
        self.scan_nulls("customers", ["NAME", "PHONE"])
        
        self.scan_duplicates("orders", "ORDER_ID")
        self.scan_nulls("orders", ["ORDER_DT", "AMOUNT"])
        
        # Logic check: Broken Relationships (Orders without Customers)
        self.cur.execute("""
            SELECT COUNT(*) as cnt 
            FROM orders o 
            LEFT JOIN customers c ON o.CUST_ID = c.CUST_ID 
            WHERE c.CUST_ID IS NULL
        """)
        orphans = self.cur.fetchone()['cnt']
        if orphans > 0:
            recorder.log_quality_issue("orders", "ORPHAN_RECORD", f"{orphans} orders have no valid customer")

        print("✅ Scan Complete.")