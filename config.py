# config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Resolve DBF root and staging SQL path relative to this config file
DB_CONFIG = {
    "SOURCE": {
        "TYPE": "FOXPRO",
        "DBF_ROOT": str(BASE_DIR / "data" / "foxpro"),   # your .dbf folder
    },
    "TARGET": {
        "TYPE": "MYSQL",
        "HOST": "localhost",
        "PORT": 3306,
        "USER": "root",
        "PASSWORD": "Ajaya@5621",
        "DATABASE_NAME": "dbmigratex",  # MySQL database where we’ll import
    },
    "OUTPUT": {
        # Only used if you ever want to generate a .sql file;
        # safe to keep even if we don't use it now.
        "STAGING_SQL_PATH": str(BASE_DIR / "sql" / "staging.sql"),
    },
}
