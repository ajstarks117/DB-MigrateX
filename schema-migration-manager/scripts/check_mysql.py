"""Small helper to verify MySQL connectivity from this project environment.

Usage (PowerShell):
  $env:DB_ENGINE='mysql'; $env:DB_NAME='testdb'; $env:DB_USER='root'; $env:DB_PASSWORD='pass'; $env:DB_HOST='127.0.0.1'; $env:DB_PORT='3306'
  python scripts/check_mysql.py

The script will attempt to connect and print server version and whether
the `schema_versions` table exists.
"""
import os
import sys
from dotenv import load_dotenv

try:
    import mysql.connector
except Exception as e:
    print('mysql-connector-python is not installed or failed to import:', e)
    sys.exit(2)


def main():
    # load .env if present so users can rely on repo .env without exporting vars
    load_dotenv()

    cfg = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST') or '127.0.0.1',
        'database': os.getenv('DB_NAME'),
    }
    port = os.getenv('DB_PORT')
    if port:
        try:
            cfg['port'] = int(port)
        except Exception:
            cfg['port'] = port

    try:
        print("Trying to connect with:")
        print(f"  user={cfg.get('user')}, host={cfg.get('host')}, port={os.getenv('DB_PORT')}, database={cfg.get('database')}")
        conn = mysql.connector.connect(**cfg)
        cur = conn.cursor()
        cur.execute('SELECT VERSION()')
        ver = cur.fetchone()
        print('Connected to MySQL version:', ver[0] if ver else '(unknown)')

        # check for schema_versions table
        cur.execute("SHOW TABLES LIKE 'schema_versions'")
        found = cur.fetchone()
        if found:
            print('schema_versions table exists.')
        else:
            print('schema_versions table NOT found.')

        cur.close()
        conn.close()
    except mysql.connector.Error as e:
        # Provide a friendly hint for common auth error 1045
        if getattr(e, 'errno', None) == 1045:
            print('MySQL connection failed: Access denied (1045).')
            print('Check that DB_USER/DB_PASSWORD are correct and that the user has privileges for the host you are connecting from.')
            print('If root login is restricted for TCP connections on your server, create a dedicated user and grant it privileges, or allow remote/root connections if appropriate.')
        else:
            print('MySQL connection failed:', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
