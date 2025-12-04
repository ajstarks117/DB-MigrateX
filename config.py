# config.py

DB_CONFIG = {
    "SOURCE": {
        "TYPE": "FOXPRO",
        "DBF_ROOT": "./data/foxpro",   # your .dbf folder
    },
    "TARGET": {
        "TYPE": "MYSQL",
        "HOST": "localhost",
        "PORT": 3306,
        "USER": "root",
        "PASSWORD": "Rishi@0211",
        "DATABASE_NAME": "dbmigratex",  # MySQL database where we’ll import
    },
    "OUTPUT": {
        # Only used if you ever want to generate a .sql file;
        # safe to keep even if we don't use it now.
        "STAGING_SQL_PATH": "./sql/staging.sql",
    },
}
