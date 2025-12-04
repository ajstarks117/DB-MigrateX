import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Define a dynamic 'uploads' folder
UPLOAD_FOLDER = BASE_DIR / "uploads"

DB_CONFIG = {
    "SOURCE": {
        "TYPE": "FOXPRO",
        # This now points to the folder where you upload files
        "DBF_ROOT": str(UPLOAD_FOLDER),
    },
    "TARGET": {
        "TYPE": "MYSQL",
        "HOST": "localhost",
        "PORT": 3306,
        "USER": "root",
        "PASSWORD": "@J!nky@_2005", # Update this
        "DATABASE_NAME": "dbmigratex",
    },
    "OUTPUT": {
        "STAGING_SQL_PATH": str(BASE_DIR / "sql" / "staging.sql"),
    },
}