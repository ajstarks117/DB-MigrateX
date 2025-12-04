# migrmgr/executor_mysql.py

from config import DB_CONFIG
from db.db_connection import get_db_connection, create_database_if_not_exists
from legacy.importer_foxpro import FoxProImporter
from utils.forensics import recorder

class MySQLMigrationExecutor:
    def __init__(self):
        self.target_cfg = DB_CONFIG["TARGET"]
        source_cfg = DB_CONFIG["SOURCE"]
        self.importer = FoxProImporter(source_cfg["DBF_ROOT"])

    def _get_primary_key(self, tname):
        """
        Heuristic to guess the Primary Key based on table name.
        Necessary for Incremental Upserts to work.
        """
        t = tname.lower()
        if "customer" in t: return "CUST_ID"
        if "employee" in t: return "EMP_ID"
        if "product"  in t: return "PROD_ID"
        if "order"    in t: return "ORDER_ID"
        return None  # Fallback: No PK (will just append)

    def setup_database_and_schema(self):
        """
        Creates tables only if they don't exist.
        Now enforces PRIMARY KEYS.
        """
        create_database_if_not_exists()
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            dbname = self.target_cfg["DATABASE_NAME"]
            cur.execute(f"USE `{dbname}`;")

            tables = self.importer.list_tables()
            print(f"📋 Verifying schema for {len(tables)} tables...")

            for tname in tables:
                cols = self.importer.schema_for_sql(tname)
                pk_col = self._get_primary_key(tname)

                col_defs_parts = []
                for col in cols:
                    # If this is the PK, make it NOT NULL
                    is_pk = (col['name'] == pk_col)
                    null_rule = "NOT NULL" if is_pk else "NULL"
                    col_defs_parts.append(f"`{col['name']}` {col['sql_type']} {null_rule}")

                # Add Primary Key constraint if detected
                if pk_col:
                    col_defs_parts.append(f"PRIMARY KEY (`{pk_col}`)")

                col_defs = ",\n  ".join(col_defs_parts)
                
                # --- CHANGE: Don't DROP. Create only if missing. ---
                ddl = f"CREATE TABLE IF NOT EXISTS `{tname}` (\n  {col_defs}\n);"
                cur.execute(ddl)
                
                # Check if we are upgrading an old table (optional robustness)
                print(f"   ✅ Schema verified for: {tname} (PK: {pk_col})")

            conn.commit()
        finally:
            cur.close()
            conn.close()

    def migrate_single_table(self, tname):
        """
        Migrates data using UPSERT (Insert ... ON DUPLICATE KEY UPDATE).
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(f"USE `{self.target_cfg['DATABASE_NAME']}`;")
            
            row_count = 0
            updated_count = 0
            
            # Use larger batch for performance
            for batch in self.importer.get_table_rows(tname, batch_size=500):
                if not batch: continue

                first_row = batch[0]
                cols = list(first_row.keys())
                
                # 1. Build INSERT part
                col_list = ", ".join(f"`{c}`" for c in cols)
                placeholders = ", ".join(["%s"] * len(cols))
                
                # 2. Build ON DUPLICATE KEY UPDATE part
                # Generates: `NAME`=VALUES(`NAME`), `CITY`=VALUES(`CITY`)...
                update_parts = [f"`{c}`=VALUES(`{c}`)" for c in cols]
                update_clause = ", ".join(update_parts)
                
                sql = f"""
                    INSERT INTO `{tname}` ({col_list}) 
                    VALUES ({placeholders}) 
                    ON DUPLICATE KEY UPDATE {update_clause}
                """

                values_list = []
                for row in batch:
                    values = [row[c] for c in cols]
                    values_list.append(tuple(values))

                cur.executemany(sql, values_list)
                conn.commit()
                row_count += len(batch)

            # Log success
            recorder.log_migration(tname, row_count, "INCREMENTAL_SYNC")
            print(f"✅ [Sync] {tname}: {row_count} records processed.")
            
        except Exception as e:
            print(f"❌ [Fail] {tname}: {e}")
            recorder.log_error(f"Migration-{tname}", str(e))
        finally:
            cur.close()
            conn.close()

    def list_tables(self):
        return self.importer.list_tables()