# migrmgr/planner.py

import os
from config import DB_CONFIG
from legacy.importer_foxpro import FoxProImporter

class MigrationPlanner:
    def __init__(self):
        source_cfg = DB_CONFIG["SOURCE"]
        self.importer = FoxProImporter(source_cfg["DBF_ROOT"])
        target_cfg = DB_CONFIG["TARGET"]
        self.target_db_name = target_cfg["DATABASE_NAME"]
        output_cfg = DB_CONFIG["OUTPUT"]
        self.out_path = output_cfg["STAGING_SQL_PATH"]

    def _build_staging_ddl(self):
        statements = []

        # Create database (for MySQL style)
        statements.append(
            "CREATE DATABASE IF NOT EXISTS " + self.target_db_name + ";"
        )
        statements.append("USE " + self.target_db_name + ";")

        tables = self.importer.list_tables()
        t_idx = 0
        while t_idx < len(tables):
            tname = tables[t_idx]
            cols = self.importer.schema_for_sql(tname)
            col_lines = []
            c_idx = 0
            while c_idx < len(cols):
                col = cols[c_idx]
                line = "`" + col["name"] + "` " + col["sql_type"] + " NULL"
                col_lines.append(line)
                c_idx += 1

            ddl = "CREATE TABLE IF NOT EXISTS `" + tname + "` (\n  " \
                  + ",\n  ".join(col_lines) + "\n);\n"
            statements.append(ddl)
            t_idx += 1

        return statements

    def _escape_sql_string(self, value):
        # convert Python value to SQL literal (string)
        # avoid built-ins like replace(): do manual scan
        s = str(value)
        result = ""
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "'":
                result = result + "''"
            else:
                result = result + ch
            i += 1
        return "'" + result + "'"

    def _build_insert_statements(self):
        statements = []
        tables = self.importer.list_tables()

        t_idx = 0
        while t_idx < len(tables):
            tname = tables[t_idx]
            for batch in self.importer.get_table_rows(tname, batch_size=200):
                if len(batch) == 0:
                    continue

                # columns (keys of first row)
                first_row = batch[0]
                cols = []
                for key in first_row:
                    cols.append(key)

                # column list
                col_list_parts = []
                c_idx = 0
                while c_idx < len(cols):
                    col_list_parts.append("`" + cols[c_idx] + "`")
                    c_idx += 1
                col_list = ", ".join(col_list_parts)

                # values
                values_lines = []
                r_idx = 0
                while r_idx < len(batch):
                    row = batch[r_idx]
                    vals = []
                    c_idx = 0
                    while c_idx < len(cols):
                        col_name = cols[c_idx]
                        v = row[col_name]

                        if v is None:
                            vals.append("NULL")
                        elif isinstance(v, bool):
                            if v:
                                vals.append("1")
                            else:
                                vals.append("0")
                        elif isinstance(v, int):
                            vals.append(str(v))
                        elif isinstance(v, float):
                            vals.append(str(v))
                        else:
                            vals.append(self._escape_sql_string(v))
                        c_idx += 1

                    line = "(" + ", ".join(vals) + ")"
                    values_lines.append(line)
                    r_idx += 1

                if len(values_lines) > 0:
                    insert_stmt = "INSERT INTO `" + tname + "` (" + col_list + ") VALUES\n  " \
                                  + ",\n  ".join(values_lines) + ";\n"
                    statements.append(insert_stmt)

            t_idx += 1

        return statements

    def generate_staging_sql_file(self):
        ddl = self._build_staging_ddl()
        inserts = self._build_insert_statements()

        out_dir = os.path.dirname(self.out_path)
        if out_dir != "" and not os.path.exists(out_dir):
            os.makedirs(out_dir)

        f = open(self.out_path, "w", encoding="utf-8")
        try:
            idx = 0
            while idx < len(ddl):
                f.write(ddl[idx])
                f.write("\n")
                idx += 1

            idx = 0
            while idx < len(inserts):
                f.write(inserts[idx])
                f.write("\n")
                idx += 1
        finally:
            f.close()
