# DB-MigrateX — Schema Migration Manager

A lightweight, portable SQL schema migration manager for Python projects.  
Apply, rollback and track schema changes reliably with checksum verification, dependency ordering and multi-DB support.

---

## Key features
- Ordered up/down migrations with idempotency
- Checksum verification to detect modified migration files
- Safe rollback to previous states
- Dependency graph ordering for complex flows
- SQLite (default) and PostgreSQL support
- Dry-run mode to preview plans
- Metadata tracking and integrity checks

---

## Requirements
- Python >= 3.8 (3.11 recommended for PyYAML wheels)
- Dependencies: see `requirements.txt`
  - PyYAML==6.0
  - psycopg2 (only for PostgreSQL)
  - python-dotenv
  - pytest (for tests)

---

## Installation

1. Clone repository and enter the package
```bash
git clone https://github.com/yourusername/DB-MigrateX.git
cd DB-MigrateX/schema-migration-manager
```

2. Create and activate a virtual environment
Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

Notes:
- On Windows, if PyYAML wheel fails, use Python 3.11 or install a prebuilt wheel:
  ```powershell
  .\venv\Scripts\python.exe -m pip install PyYAML-6.0-cp311-cp311-win_amd64.whl
  ```
- Alternatively use Docker or WSL / install Visual Studio Build Tools.

---

## Quickstart (CLI)

All commands run via the module:
```bash
python -m migrmgr.cli [COMMAND] [OPTIONS]
```

Dry run (preview plan):
```bash
python -m migrmgr.cli migrate --dry-run
# or with explicit venv Python
& '.\venv\Scripts\python.exe' -m migrmgr.cli migrate --dry-run
```

Apply pending migrations (default SQLite):
```bash
python -m migrmgr.cli migrate
```

Use a custom migrations directory:
```bash
python -m migrmgr.cli migrate --migrations-dir examples/migrations
# dry-run
python -m migrmgr.cli migrate --migrations-dir examples/migrations --dry-run
```

Rollback to a migration ID (inclusive lower bound):
```bash
python -m migrmgr.cli migrate --rollback-to 002
# force even if no down file present (use with care)
python -m migrmgr.cli migrate --rollback-to 002 --force
```

PostgreSQL: create a `.env` in repo root:
```
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_pass
DB_HOST=localhost
DB_PORT=5432
```
Then run:
```bash
python -m migrmgr.cli migrate
```
Or set environment variables in PowerShell:
```powershell
$env:DB_NAME='your_db'
$env:DB_USER='your_user'
$env:DB_PASSWORD='your_pass'
$env:DB_HOST='localhost'
$env:DB_PORT='5432'
python -m migrmgr.cli migrate
```

---

## CLI flags summary
- --dry-run : preview migration plan only  
- --migrations-dir PATH : use a custom migrations folder  
- --force : force apply/rollback without down files  
- --rollback-to <id> : rollback to a target migration id  
- --skip-integrity : skip checksum/integrity verification

---

## Migration conventions

File type | Naming example | Description
--- | ---: | ---
Up migration | `001_create_users.sql` | Forward migration script
Down migration | `001_create_users_down.sql` | Reversal for corresponding up migration
Optional metadata | `001_create_users.yml` or inline YAML | Notes, dependencies, rollback info

Migrations are applied in numeric order; dependency metadata can override ordering when declared.

---

## Schema tracking table

The manager creates (if missing) a `schema_versions` table to track applied migrations:

Column | Description
--- | ---
migration_id | Sequential ID (string)
filename | Migration file name
checksum | File integrity hash
applied_by | Username who ran the migration
applied_at | Timestamp when applied
down_filename | Linked rollback file (if available)
notes | Optional description / metadata

Verify applied migrations (SQLite example):
```bash
sqlite3.exe .\dev.sqlite3 "SELECT migration_id, filename, applied_at FROM schema_versions ORDER BY migration_id;"
```

---

## Testing
Set the repository root on PYTHONPATH and run pytest:
PowerShell:
```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -q
```
If `ModuleNotFoundError: No module named 'yaml'` appears, ensure PyYAML is installed in the active environment.

---

## Troubleshooting

Problem | Solution
--- | ---
“No module named yaml” | Install PyYAML in the active venv
Nothing applies | Run with `--dry-run` to inspect pending migrations
psycopg2 install fails | Use a prebuilt wheel or install PostgreSQL client libs
Permission denied (Windows) | Run terminal as Administrator or adjust filesystem permissions

---

## Example commands

Action | Command
--- | ---
Dry run (default dir) | `python -m migrmgr.cli migrate --dry-run`
Apply all (SQLite) | `python -m migrmgr.cli migrate`
Custom dir (dry-run) | `python -m migrmgr.cli migrate --migrations-dir examples/migrations --dry-run`
Custom dir (apply) | `python -m migrmgr.cli migrate --migrations-dir examples/migrations`
Use PostgreSQL (.env) | `.env + python -m migrmgr.cli migrate`
Rollback | `python -m migrmgr.cli migrate --rollback-to 002`
Verify applied | `sqlite3.exe dev.sqlite3 "SELECT * FROM schema_versions;"`

---

## Roadmap / Future enhancements
- Auto dependency resolution via graph planner
- Multi-backend adapter layer (MySQL, MariaDB)
- Dedicated checksum verification CLI command
- Parallel migration batches
- Structured logging and verbosity flags



## 📅 Project Team
- [Ajinkya Ubale](https://github.com/ajstarks117)
- [Rishi Agrawal](https://github.com/rishiagrawal02)
- [Ajaya Nandiyawar](https://github.com/Ajaya-Nandiyawar)
- [Abhijeet Ambat](https://github.com/IPPYON596)

