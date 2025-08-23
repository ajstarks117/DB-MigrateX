# Schema Evolution and Migration Manager 🚀

## 📌 Overview
This project is a **web-based tool** for managing seamless schema changes in relational databases.  
It allows developers and database administrators to:
- Version and apply migration scripts
- Track schema changes
- Ensure data integrity
- Rollback updates if needed

Unlike ORMs or prebuilt libraries (Alembic/SQLAlchemy), this project uses **raw SQL** migrations for better understanding of database evolution.

---

## 🛠 Tech Stack
- **Backend:** Python (Flask)
- **Database:** MySQL / PostgreSQL
- **Frontend:** HTML, CSS, JavaScript
- **DB Connector:** `mysql.connector` (for MySQL) / `psycopg2` (for PostgreSQL)
- **Migrations:** Raw SQL scripts stored in `migrations/` folder

---

## 📂 Project Structure
```bash
schema-migration-manager/
├── app.py                 # CLI/web entry
├── requirements.txt
├── README.md
│
├── migrations/            # All migration files (SQL/YAML)
│   ├── 001_create_users.sql
│   ├── 002_add_email.sql
│   └── 003_create_orders.sql
│
├── migrmgr/               # Core logic
│   ├── __init__.py
│   ├── cli.py
│   ├── state.py
│   ├── parser.py
│   ├── planner.py
│   └── executor.py
│
├── db/
│   └── schema_versions.sql
│
├── templates/             # Optional web UI
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
```


---

## ⚡ Features
- Apply schema migrations in correct sequence
- Maintain a **`schema_versions`** table to track applied changes
- Simple UI to view current schema version and pending migrations
- Rollback support (optional `*_down.sql` scripts)
- Lightweight and educational (no heavy ORM)

---
