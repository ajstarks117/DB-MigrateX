# 🚀 DB-MigrateX: FoxPro to MySQL Migration Engine

**DB-MigrateX** is a full-stack ETL (Extract, Transform, Load) pipeline to modernize legacy FoxPro (.dbf) systems by migrating data into MySQL, performing forensic data-quality analysis, and normalizing schemas into 3rd Normal Form (3NF). It includes a live web dashboard to monitor migration progress, data-quality issues, and logs.

---

## 🌟 Key Features

### 1. 📂 Custom FoxPro Extraction
- Zero-dependency binary reader (Python `struct`) for `.dbf` headers and records.
- Robust decoding for legacy encodings, deleted records, and field types (Character, Date, Numeric, Logical).

### 2. 🏗️ Automated Staging & Cleaning
- Dynamic MySQL `CREATE TABLE` generation from FoxPro headers.
- Smart reloading: drops and recreates staging tables to avoid duplicates.
- Data-quality engine that detects duplicate keys, critical NULLs, and orphaned records.

### 3. 📐 Relational Normalization
- Converts flat FoxPro tables to normalized 3NF schemas (e.g., extracting `CITY` into a `Cities` table).
- Resolves and links foreign keys during insertion.

### 4. 📊 Live Forensic Dashboard
- Flask-based web UI that updates periodically.
- Displays migrated rows, error counts, and data-quality warnings.
- Produces `final_report.html` and `migration_process.log` for audits.

---

## 🛠️ Tech Stack

- Language: Python 3.10+
- Database: MySQL 8.0
- Web Framework: Flask
- Frontend: HTML5, Bootstrap 5, Jinja2
- Libraries: `mysql-connector-python`, `python-dotenv`, `tqdm`

---

## 📂 Project Structure

```text
DB-MigrateX/
├── app.py                 # Main CLI pipeline (Worker)
├── dashboard.py           # Web dashboard server (Viewer)
├── config.py              # Configuration loader
├── .env                   # Environment variables (DB creds)
│
├── data/
│   └── foxpro/            # Source .dbf files
│
├── legacy/                # Extract module
│   ├── importer_foxpro.py # Process .dbf tables
│   └── utils/             # Binary parsing utilities
│
├── migrmgr/               # Load module
│   └── executor_mysql.py  # MySQL staging creation & insertion
│
├── cleaner/               # Quality module
│   └── cleanser.py        # Detect duplicates/nulls/orphans
│
├── normalizer/            # Transform module
│   └── normalizer.py      # Convert staging -> normalized DB
│
└── templates/             # HTML templates for dashboard
    └── dashboard.html
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- MySQL Server (8.0+)
- A folder with source `.dbf` files (e.g., `./data/foxpro`)

### 2. Installation
```bash
git clone https://github.com/yourusername/DB-MigrateX.git
cd DB-MigrateX
pip install flask mysql-connector-python python-dotenv tqdm
```

### 3. Configuration
Create a `.env` file in the project root with your DB credentials:
```env
# .env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=dbmigratex
```

### 4. Running
Run the dashboard and pipeline in separate terminals.

Terminal 1 — start the dashboard:
```bash
python dashboard.py
```
Open http://127.0.0.1:5000 to view the Control Center.

Terminal 2 — run the migration:
```bash
python app.py
```
Pipeline steps: Extract (.dbf) → Load (staging) → Clean (quality checks) → Normalize (production schema). Dashboard updates live.

---

## 📈 Sample Results

- Source (FoxPro): `employees.dbf`, `customers.dbf`
- Staging (MySQL): `dbmigratex.employees`, `dbmigratex.customers`
- Normalized (MySQL): `dbmigratex_norm.employees_norm`, `dbmigratex_norm.customers_norm`, `dbmigratex_norm.cities`, `dbmigratex_norm.departments`

---

## 🛡️ Forensic Reports
After each run the system generates:
- `migration_process.log` — detailed debugging log
- `final_report.html` — stakeholder-friendly summary
- `forensic_report.json` — raw statistics

---

## 👤 Author
[Your Name]  
Computer Engineering Student | Vishwakarma Institute of Technology, Pune

---

Replace placeholders (GitHub repo URL, author name, and DB credentials) as needed before sharing or deploying.