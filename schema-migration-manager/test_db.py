import mysql.connector
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

# ✅ Directly using your provided credentials
DB_TYPE = "mysql"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_USER = "root"
DB_PASSWORD = "Ajaya@5621"
DB_NAME = "dbmigratex"

print("🔍 Attempting MySQL connection...")
print("---------------------------------")
print(f"Host      : {DB_HOST}")
print(f"User      : {DB_USER}")
print(f"Database  : {DB_NAME}")
print("---------------------------------")

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

    print(f"✅ SUCCESS: Connected to MySQL database '{DB_NAME}'!")
    conn.close()

except mysql.connector.Error as err:
    print("❌ ERROR: Failed to connect to MySQL.")
    print("Reason:", err)

except Exception as e:
    print("❌ Unexpected error:", e)
