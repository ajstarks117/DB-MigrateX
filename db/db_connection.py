# db/db_connection.py

import os
import sys
import mysql.connector
from mysql.connector import errorcode

# --- ensure project root is in sys.path ---
# This lets `from config import DB_CONFIG` find your local config.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # one level up

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_CONFIG  # now this will import your config.py


def get_server_connection():
    """
    Connects to MySQL server WITHOUT specifying a database.
    This is needed to CREATE DATABASE dbmigratex if it doesn't exist.
    """
    target = DB_CONFIG["TARGET"]

    try:
        conn = mysql.connector.connect(
            host=target["HOST"],
            port=target["PORT"],
            user=target["USER"],
            password=target["PASSWORD"],
        )
        return conn

    except mysql.connector.Error as err:
        print("❌ Error connecting to MySQL server:", err)
        raise


def get_db_connection():
    """
    Connects directly to dbmigratex DATABASE.
    Assumes the database already exists.
    """
    target = DB_CONFIG["TARGET"]

    try:
        conn = mysql.connector.connect(
            host=target["HOST"],
            port=target["PORT"],
            user=target["USER"],
            password=target["PASSWORD"],
            database=target["DATABASE_NAME"],
        )
        return conn

    except mysql.connector.Error as err:
        print("❌ Error connecting to MySQL database:", err)
        raise


def create_database_if_not_exists():
    """
    Creates dbmigratex database if it does not exist.
    """
    target = DB_CONFIG["TARGET"]
    dbname = target["DATABASE_NAME"]

    conn = get_server_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}`;")
        print(f"✅ Database ready: {dbname}")
    except mysql.connector.Error as err:
        print("❌ Error creating database:", err)
    finally:
        cur.close()
        conn.close()


# Optional: simple test when you run this file directly
if __name__ == "__main__":
    create_database_if_not_exists()
    conn = get_db_connection()
    print("✅ Test connection to DB successful.")
    conn.close()
