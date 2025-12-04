# normalizer/normalizer.py

import mysql.connector
from config import DB_CONFIG
from db.db_connection import get_server_connection


class NormalizationExecutor:
    """
    Normalizes data from staging database (dbmigratex) into
    a separate normalized database (dbmigratex_norm).

    STAGING DB (dbmigratex):
        customers(CUST_ID, NAME, CITY, PHONE)
        employees(EMP_ID, EMP_NAME, DEPT, DOJ, ACTIVE)
        products(PROD_ID, PROD_NAME, PRICE, STOCK)
        orders(ORDER_ID, CUST_ID, ORDER_DT, AMOUNT)

    NORMALIZED DB (dbmigratex_norm):
        cities(city_id, city_name)
        customers_norm(cust_id, name, city_id, phone)
        departments(dept_id, dept_name)
        employees_norm(emp_id, emp_name, dept_id, doj, active)
        products_norm(prod_id, prod_name, price, stock)
        orders_norm(order_id, cust_id, order_dt, amount)
    """

    def __init__(self):
        target = DB_CONFIG["TARGET"]
        self.host = target["HOST"]
        self.port = target["PORT"]
        self.user = target["USER"]
        self.password = target["PASSWORD"]

        # staging DB: where raw FoxPro data is loaded
        self.staging_db = target["DATABASE_NAME"]           # e.g. "dbmigratex"
        # normalized DB: new database to store normalized schema
        self.normalized_db = self.staging_db + "_norm"      # e.g. "dbmigratex_norm"

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _get_normalized_connection(self):
        """
        Returns a connection to the normalized database (dbmigratex_norm).
        Assumes the database exists.
        """
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.normalized_db,
        )
        return conn

    def create_normalized_database(self):
        """
        CREATE DATABASE dbmigratex_norm IF NOT EXISTS.
        """
        conn = get_server_connection()
        cur = conn.cursor()
        try:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{self.normalized_db}`;")
            print(f"✅ Normalized database ready: {self.normalized_db}")
        finally:
            cur.close()
            conn.close()

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------

    def create_normalized_schema(self):
        """
        Creates normalized tables inside dbmigratex_norm:

            cities(city_id, city_name)
            customers_norm(cust_id, name, city_id, phone)
            departments(dept_id, dept_name)
            employees_norm(emp_id, emp_name, dept_id, doj, active)
            products_norm(prod_id, prod_name, price, stock)
            orders_norm(order_id, cust_id, order_dt, amount)
        """
        conn = self._get_normalized_connection()
        cur = conn.cursor()

        # 1) Cities master table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cities (
                city_id INT AUTO_INCREMENT PRIMARY KEY,
                city_name VARCHAR(50) UNIQUE NOT NULL
            );
            """
        )

        # 2) Normalized customers with FK to cities
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customers_norm (
                cust_id INT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                city_id INT,
                phone VARCHAR(20),
                CONSTRAINT fk_customers_norm_city
                    FOREIGN KEY (city_id) REFERENCES cities(city_id)
            );
            """
        )

        # 3) Departments master
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS departments (
                dept_id INT AUTO_INCREMENT PRIMARY KEY,
                dept_name VARCHAR(50) UNIQUE NOT NULL
            );
            """
        )

        # 4) Normalized employees with FK to departments
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employees_norm (
                emp_id INT PRIMARY KEY,
                emp_name VARCHAR(50) NOT NULL,
                dept_id INT,
                doj DATE,
                active BOOLEAN,
                CONSTRAINT fk_employees_norm_dept
                    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
            );
            """
        )

        # 5) Normalized products (1:1 from staging products)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_norm (
                prod_id INT PRIMARY KEY,
                prod_name VARCHAR(50) NOT NULL,
                price DECIMAL(10,2),
                stock INT
            );
            """
        )

        # 6) Normalized orders (1:1 from staging orders, but linked to customers_norm)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders_norm (
                order_id INT PRIMARY KEY,
                cust_id INT,
                order_dt DATE,
                amount DECIMAL(10,2),
                CONSTRAINT fk_orders_norm_customer
                    FOREIGN KEY (cust_id) REFERENCES customers_norm(cust_id)
            );
            """
        )

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Normalized schema created in", self.normalized_db)

    # ------------------------------------------------------------------
    # Data population
    # ------------------------------------------------------------------

    def populate_normalized_data(self):
        """
        Fill normalized tables from staging dbmigratex using INSERT...SELECT.

        IMPORTANT:
        - Clears existing normalized data first, so this function is safe
          to run multiple times without duplicate primary key errors.
        """
        conn = self._get_normalized_connection()
        cur = conn.cursor()

        # --- Clear existing data (to avoid duplicate PK errors on rerun) ---
        print("🧹 Clearing existing normalized data...")

        # Delete in order: children first, then parents (FK-safe)
        # orders_norm -> employees_norm -> customers_norm -> products_norm -> cities -> departments
        cur.execute("DELETE FROM orders_norm;")
        cur.execute("DELETE FROM employees_norm;")
        cur.execute("DELETE FROM customers_norm;")
        cur.execute("DELETE FROM products_norm;")
        cur.execute("DELETE FROM cities;")
        cur.execute("DELETE FROM departments;")

        conn.commit()
        print("✅ Normalized tables cleared.\n")

        # --- Populate cities table from staging customers ---
        print("➡ Populating cities...")
        cur.execute(
            f"""
            INSERT INTO cities (city_name)
            SELECT DISTINCT CITY
            FROM {self.staging_db}.customers
            WHERE CITY IS NOT NULL AND CITY <> '';
            """
        )

        # --- Populate customers_norm with FK to cities ---
        print("➡ Populating customers_norm...")
        cur.execute(
            f"""
            INSERT INTO customers_norm (cust_id, name, city_id, phone)
            SELECT
                c.CUST_ID,
                c.NAME,
                ci.city_id,
                c.PHONE
            FROM {self.staging_db}.customers c
            LEFT JOIN cities ci
                ON ci.city_name = c.CITY;
            """
        )

        # --- Populate departments from employees ---
        print("➡ Populating departments...")
        cur.execute(
            f"""
            INSERT INTO departments (dept_name)
            SELECT DISTINCT DEPT
            FROM {self.staging_db}.employees
            WHERE DEPT IS NOT NULL AND DEPT <> '';
            """
        )

        # --- Populate employees_norm with FK to departments ---
        print("➡ Populating employees_norm...")
        cur.execute(
            f"""
            INSERT INTO employees_norm (emp_id, emp_name, dept_id, doj, active)
            SELECT
                e.EMP_ID,
                e.EMP_NAME,
                d.dept_id,
                e.DOJ,
                e.ACTIVE
            FROM {self.staging_db}.employees e
            LEFT JOIN departments d
                ON d.dept_name = e.DEPT;
            """
        )

        # --- Populate products_norm as 1:1 from products ---
        print("➡ Populating products_norm...")
        cur.execute(
            f"""
            INSERT INTO products_norm (prod_id, prod_name, price, stock)
            SELECT
                PROD_ID,
                PROD_NAME,
                PRICE,
                STOCK
            FROM {self.staging_db}.products;
            """
        )

        # --- Populate orders_norm as 1:1 from orders ---
        print("➡ Populating orders_norm...")
        cur.execute(
            f"""
            INSERT INTO orders_norm (order_id, cust_id, order_dt, amount)
            SELECT
                ORDER_ID,
                CUST_ID,
                ORDER_DT,
                AMOUNT
            FROM {self.staging_db}.orders;
            """
        )

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Data populated into normalized schema.")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run_full_normalization(self):
        """
        1) Create normalized DB (if not exists)
        2) Create normalized schema (tables)
        3) Populate normalized tables from staging
        """
        self.create_normalized_database()
        self.create_normalized_schema()
        self.populate_normalized_data()
        print("🎯 Normalization step completed.")
