# legacy/importer_foxpro.py

import os
from legacy.utils.dbf_reader import DBFReader
from legacy.utils.type_mapping import map_foxpro_type_to_sql

class FoxProImporter:
    def __init__(self, dbf_root):
        self.dbf_root = dbf_root
        self.reader = DBFReader()

    def list_tables(self):
        names = []
        for filename in os.listdir(self.dbf_root):
            lower = filename.lower()
            if lower.endswith(".dbf"):
                base = filename[:len(filename) - 4]
                names.append(base)
        return names

    def get_table_schema(self, table_name):
        path = os.path.join(self.dbf_root, table_name + ".dbf")
        return self.reader.read_schema(path)

    def get_table_rows(self, table_name, batch_size):
        path = os.path.join(self.dbf_root, table_name + ".dbf")
        for batch in self.reader.read_rows(path, batch_size):
            yield batch

    def schema_for_sql(self, table_name):
        fox_cols = self.get_table_schema(table_name)
        sql_cols = []
        idx = 0
        while idx < len(fox_cols):
            col = fox_cols[idx]
            sql_type = map_foxpro_type_to_sql(
                col["foxpro_type"],
                col["size"],
                col["decimals"]
            )
            sql_cols.append({
                "name": col["name"],
                "sql_type": sql_type,
                "nullable": True,
            })
            idx += 1
        return sql_cols
