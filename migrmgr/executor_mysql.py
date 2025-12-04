# migrmgr/executor_mysql.py

from config import DB_CONFIG
from db.db_connection import get_db_connection, create_database_if_not_exists
from legacy.importer_foxpro import FoxProImporter
from utils.forensics import recorder


class MySQLMigrationExecutor:
    def __init__(self):
        self.target_cfg = DB_CONFIG["TARGET"]
        source_cfg = DB_CONFIG["SOURCE"]

        # FoxPro importer will read all .dbf files from this folder
        self.importer = FoxProImporter(source_cfg["DBF_ROOT"])

    def _create_tables(self, conn):
        """
        Creates staging tables in MySQL based on FoxPro schema.
        One FoxPro table (.dbf) = one MySQL table.
        """
        cur = conn.cursor()
        dbname = self.target_cfg["DATABASE_NAME"]

        # USE dbmigratex;
        cur.execute(f"USE `{dbname}`;")

        tables = self.importer.list_tables()
        print("FoxPro tables found:", tables)

        for tname in tables:
            cols = self.importer.schema_for_sql(tname)

            col_defs_parts = []
            for col in cols:
                # Simple: allow NULLs; you can tighten later
                col_defs_parts.append(f"`{col['name']}` {col['sql_type']} NULL")

            col_defs = ",\n  ".join(col_defs_parts)
            
            # --- FIX APPLIED HERE ---
            # Drop the table if it exists so we don't append duplicates on re-runs
            cur.execute(f"DROP TABLE IF EXISTS `{tname}`;")
            
            # Create the table (removed 'IF NOT EXISTS' since we just dropped it)
            ddl = f"CREATE TABLE `{tname}` (\n  {col_defs}\n);"

            print(f"\nCreating table in MySQL: {tname}")
            # print(ddl)  # uncomment if you want to see full DDL
            cur.execute(ddl)

        conn.commit()
        cur.close()
        print("\n✅ All staging tables created in MySQL.")

    def _insert_data(self, conn):
        """
        Reads records from FoxPro via importer and inserts into MySQL
        using prepared (parameterized) INSERT queries.
        """
        cur = conn.cursor()
        dbname = self.target_cfg["DATABASE_NAME"]
        cur.execute(f"USE `{dbname}`;")

        tables = self.importer.list_tables()

        for tname in tables:
            print(f"\nInserting data into MySQL table: {tname}")
            try:
                for batch in self.importer.get_table_rows(tname, batch_size=200):
                    if not batch:
                        continue

                    # Determine list of columns from first row (keys of dict)
                    first_row = batch[0]
                    cols = list(first_row.keys())

                    # Build parameterized query
                    col_list = ", ".join(f"`{c}`" for c in cols)
                    placeholders = ", ".join(["%s"] * len(cols))
                    sql = f"INSERT INTO `{tname}` ({col_list}) VALUES ({placeholders})"

                    # Build list of tuples of values
                    values_list = []
                    for row in batch:
                        values = []
                        for c in cols:
                            values.append(row[c])  # None/int/float/str/bool
                        values_list.append(tuple(values))

                    # Execute batch insert
                    cur.executemany(sql, values_list)
                    conn.commit()

                # AFTER loop finishes for a table:
                total_rows = self.importer.get_record_count(tname)  # assumed available
                recorder.log_migration(tname, total_rows, "SUCCESS")

            except Exception as e:
                recorder.log_error(f"Migration-Table-{tname}", str(e))
                raise e

            print(f"✅ Data inserted into {tname}")

        cur.close()
        print("\n✅ All FoxPro data inserted into MySQL.")

    def run_full_migration(self):
        """
        Main pipeline:
        1) Create database dbmigratex if not exists
        2) Connect to dbmigratex
        3) Create tables based on FoxPro schema
        4) Insert all data from FoxPro .dbf files
        """
        # 1. Ensure database exists
        create_database_if_not_exists()

        # 2. Connect to that database
        conn = get_db_connection()
        try:
            # 3. Create the tables
            self._create_tables(conn)

            # 4. Insert the data
            self._insert_data(conn)
        finally:
            conn.close()
            print("🔌 MySQL connection closed.")