import os
import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path

import pandas as pd
from pandas.api.types import is_scalar

try:
    import psycopg2
    from psycopg2 import IntegrityError as PostgresIntegrityError
except ImportError:
    psycopg2 = None
    PostgresIntegrityError = None

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "inbound_inventory.db"
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000


def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file()

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").strip().lower()


def using_postgresql():
    return DB_BACKEND in {"postgres", "postgresql"}


def get_connection():
    if using_postgresql():
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 is required for PostgreSQL. Install it with 'pip install psycopg2-binary'."
            )

        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "inbound_inventory"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        )

    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def adapt_query(query):
    if using_postgresql():
        return query.replace("?", "%s")
    return query


def is_integrity_error(error):
    integrity_errors = [sqlite3.IntegrityError]
    if PostgresIntegrityError is not None:
        integrity_errors.append(PostgresIntegrityError)
    return isinstance(error, tuple(integrity_errors))


def adapt_param_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except (ValueError, TypeError):
            return value
    return value


def adapt_params(params):
    if params is None:
        return None
    if isinstance(params, dict):
        return {key: adapt_param_value(value) for key, value in params.items()}
    if isinstance(params, (list, tuple)):
        return tuple(adapt_param_value(value) for value in params)
    if is_scalar(params):
        return adapt_param_value(params)
    return params


def execute(query, params=(), fetchone=False, fetchall=False):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(adapt_query(query), adapt_params(params))
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def read_dataframe(query, params=()):
    conn = get_connection()
    try:
        return pd.read_sql_query(adapt_query(query), conn, params=adapt_params(params))
    finally:
        conn.close()


def current_date_sql():
    return "CURRENT_DATE"


def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${password_hash}"


def is_hashed_password(value):
    return isinstance(value, str) and value.startswith(f"{PASSWORD_SCHEME}$")


def verify_password(password, stored_password):
    if not stored_password:
        return False

    if not is_hashed_password(stored_password):
        return hmac.compare_digest(password, stored_password)

    try:
        _, iterations, salt, stored_hash = stored_password.split("$", 3)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(password_hash, stored_hash)
    except (TypeError, ValueError):
        return False


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def require_text(value, field_name):
    normalized = normalize_text(value)
    if not normalized:
        raise ValueError(f"{field_name} is required.")
    return normalized


def require_non_negative_number(value, field_name):
    if value is None or float(value) < 0:
        raise ValueError(f"{field_name} must be zero or greater.")
    return float(value)


def require_positive_int(value, field_name):
    if value is None or int(value) <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return int(value)


# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if using_postgresql():
            create_tables_postgresql(cursor)
        else:
            create_tables_sqlite(cursor)

        ensure_column_exists(cursor, "product_assignments", "status", "TEXT DEFAULT 'In Progress'")
        ensure_column_exists(cursor, "users", "department", "TEXT")
        ensure_column_exists(cursor, "users", "date_of_joining", "TEXT")
        ensure_column_exists(cursor, "users", "office_email", "TEXT")
        ensure_column_exists(cursor, "users", "company_email", "TEXT")
        ensure_column_exists(cursor, "users", "contact_number", "TEXT")
        ensure_column_exists(cursor, "users", "can_edit_suppliers", "INTEGER DEFAULT 0")
        ensure_column_exists(cursor, "users", "can_delete_suppliers", "INTEGER DEFAULT 0")
        ensure_column_exists(cursor, "users", "can_edit_products", "INTEGER DEFAULT 0")
        ensure_column_exists(cursor, "users", "can_delete_products", "INTEGER DEFAULT 0")
        ensure_column_exists(cursor, "users", "can_edit_purchases", "INTEGER DEFAULT 0")
        ensure_column_exists(cursor, "users", "can_delete_purchases", "INTEGER DEFAULT 0")
        ensure_column_exists(cursor, "notes", "assigned_to", "TEXT")
        ensure_column_exists(cursor, "products", "is_active", "INTEGER DEFAULT 1")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    create_default_admin()


def create_tables_sqlite(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            contact_number TEXT,
            email TEXT,
            address TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_no TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            price REAL,
            quantity INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 5,
            supplier_id INTEGER,
            image_path TEXT,
            assigned_to TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            supplier_id INTEGER,
            quantity_purchased INTEGER,
            unit_price REAL,
            total_purchase_price REAL,
            purchase_date TEXT,
            invoice_path TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity_sold INTEGER,
            selling_price REAL,
            sale_date TEXT,
            customer_name TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            assigned_to TEXT,
            assigned_date TEXT,
            remarks TEXT,
            status TEXT DEFAULT 'In Progress',
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            date_of_joining TEXT,
            office_email TEXT,
            company_email TEXT,
            contact_number TEXT,
            can_edit_suppliers INTEGER DEFAULT 0,
            can_delete_suppliers INTEGER DEFAULT 0,
            can_edit_products INTEGER DEFAULT 0,
            can_delete_products INTEGER DEFAULT 0,
            can_edit_purchases INTEGER DEFAULT 0,
            can_delete_purchases INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_title TEXT NOT NULL,
            note_content TEXT NOT NULL,
            created_by TEXT,
            created_date TEXT,
            note_status TEXT DEFAULT 'Open',
            assigned_to TEXT
        )
    """)


def create_tables_postgresql(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            supplier_name TEXT NOT NULL,
            contact_number TEXT,
            email TEXT,
            address TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            product_no TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            price DOUBLE PRECISION,
            quantity INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 5,
            supplier_id INTEGER REFERENCES suppliers(supplier_id),
            image_path TEXT,
            assigned_to TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            product_id INTEGER REFERENCES products(product_id),
            supplier_id INTEGER REFERENCES suppliers(supplier_id),
            quantity_purchased INTEGER,
            unit_price DOUBLE PRECISION,
            total_purchase_price DOUBLE PRECISION,
            purchase_date TEXT,
            invoice_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            product_id INTEGER REFERENCES products(product_id),
            quantity_sold INTEGER,
            selling_price DOUBLE PRECISION,
            sale_date TEXT,
            customer_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_assignments (
            assignment_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            product_id INTEGER REFERENCES products(product_id),
            assigned_to TEXT,
            assigned_date TEXT,
            remarks TEXT,
            status TEXT DEFAULT 'In Progress'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            date_of_joining TEXT,
            office_email TEXT,
            company_email TEXT,
            contact_number TEXT,
            can_edit_suppliers INTEGER DEFAULT 0,
            can_delete_suppliers INTEGER DEFAULT 0,
            can_edit_products INTEGER DEFAULT 0,
            can_delete_products INTEGER DEFAULT 0,
            can_edit_purchases INTEGER DEFAULT 0,
            can_delete_purchases INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            note_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            note_title TEXT NOT NULL,
            note_content TEXT NOT NULL,
            created_by TEXT,
            created_date TEXT,
            note_status TEXT DEFAULT 'Open',
            assigned_to TEXT
        )
    """)


# ---------------- SAFE COLUMN CREATOR ----------------
def ensure_column_exists(cursor, table_name, column_name, column_type):
    if using_postgresql():
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table_name, column_name),
        )
        exists = cursor.fetchone() is not None
    else:
        cursor.execute(f"PRAGMA table_info({table_name})")
        exists = column_name in [column[1] for column in cursor.fetchall()]

    if not exists:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


# ---------------- PRODUCT NUMBER AUTO GENERATION ----------------
def generate_product_no():
    result = execute(
        "SELECT product_no FROM products ORDER BY product_id DESC LIMIT 1",
        fetchone=True,
    )

    if result is None:
        return "PRD001"

    last_no = result[0]
    number = int(last_no.replace("PRD", "")) + 1
    return f"PRD{number:03d}"


# ---------------- SUPPLIERS ----------------
def add_supplier(name, contact, email, address):
    supplier_name = require_text(name, "Supplier name")
    execute(
        """
        INSERT INTO suppliers (supplier_name, contact_number, email, address)
        VALUES (?, ?, ?, ?)
        """,
        (supplier_name, normalize_text(contact), normalize_text(email), normalize_text(address)),
    )


def get_suppliers():
    return read_dataframe("SELECT * FROM suppliers ORDER BY supplier_id DESC")


def get_supplier_dropdown():
    return read_dataframe("""
        SELECT supplier_id, supplier_name
        FROM suppliers
        ORDER BY supplier_name
    """)


def update_supplier(supplier_id, name, contact, email, address):
    supplier_name = require_text(name, "Supplier name")
    execute(
        """
        UPDATE suppliers
        SET supplier_name = ?, contact_number = ?, email = ?, address = ?
        WHERE supplier_id = ?
        """,
        (supplier_name, normalize_text(contact), normalize_text(email), normalize_text(address), supplier_id),
    )


def delete_supplier(supplier_id):
    execute("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))


# ---------------- PRODUCTS ----------------
def add_product(product_no, name, category, price, reorder_level, supplier_id, image_path, assigned_to):
    product_no = require_text(product_no, "Product number")
    product_name = require_text(name, "Product name")
    normalized_category = normalize_text(category)
    validated_price = require_non_negative_number(price, "Price")
    validated_reorder_level = require_positive_int(reorder_level, "Reorder level")
    normalized_assigned_to = normalize_text(assigned_to)
    normalized_image_path = normalize_text(image_path)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        if using_postgresql():
            cursor.execute(
                adapt_query("""
                    INSERT INTO products (
                        product_no, product_name, category, price, reorder_level, supplier_id, image_path, assigned_to, is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING product_id
                """),
                (
                    product_no,
                    product_name,
                    normalized_category,
                    validated_price,
                    validated_reorder_level,
                    supplier_id,
                    normalized_image_path,
                    normalized_assigned_to,
                    1,
                ),
            )
            inserted_product_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                adapt_query("""
                    INSERT INTO products (
                        product_no, product_name, category, price, reorder_level, supplier_id, image_path, assigned_to, is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """),
                (
                    product_no,
                    product_name,
                    normalized_category,
                    validated_price,
                    validated_reorder_level,
                    supplier_id,
                    normalized_image_path,
                    normalized_assigned_to,
                    1,
                ),
            )
            inserted_product_id = cursor.lastrowid

        if normalized_assigned_to:
            cursor.execute(
                adapt_query(f"""
                    INSERT INTO product_assignments (product_id, assigned_to, assigned_date, remarks, status)
                    VALUES (?, ?, {current_date_sql()}, ?, ?)
                """),
                (inserted_product_id, normalized_assigned_to, "Initial Assignment", "In Progress"),
            )

        conn.commit()
        return "Product added successfully"
    except Exception as error:
        conn.rollback()
        if is_integrity_error(error):
            return "Product No already exists"
        raise
    finally:
        conn.close()


def get_products():
    return read_dataframe("""
        SELECT p.product_id, p.product_no, p.product_name, p.category, p.price,
               p.quantity, p.reorder_level, p.supplier_id, p.image_path,
               p.assigned_to, p.is_active, s.supplier_name
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.is_active = 1
        ORDER BY p.product_id DESC
    """)


def get_product_dropdown():
    return read_dataframe("""
        SELECT product_id, product_no, product_name, price, assigned_to
        FROM products
        WHERE is_active = 1
        ORDER BY product_name
    """)


def update_product(product_id, name, category, price, reorder_level, supplier_id, assigned_to, image_path=None):
    product_name = require_text(name, "Product name")
    validated_price = require_non_negative_number(price, "Price")
    validated_reorder_level = require_positive_int(reorder_level, "Reorder level")
    normalized_assigned_to = normalize_text(assigned_to)
    normalized_image_path = normalize_text(image_path) if image_path is not None else None
    normalized_category = normalize_text(category)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("SELECT assigned_to FROM products WHERE product_id = ?"),
            (product_id,),
        )
        existing_row = cursor.fetchone()
        previous_assigned_to = normalize_text(existing_row[0]) if existing_row else ""

        if image_path is not None:
            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET product_name = ?, category = ?, price = ?, reorder_level = ?, supplier_id = ?, assigned_to = ?, image_path = ?
                    WHERE product_id = ?
                """),
                (
                    product_name,
                    normalized_category,
                    validated_price,
                    validated_reorder_level,
                    supplier_id,
                    normalized_assigned_to,
                    normalized_image_path,
                    product_id,
                ),
            )
        else:
            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET product_name = ?, category = ?, price = ?, reorder_level = ?, supplier_id = ?, assigned_to = ?
                    WHERE product_id = ?
                """),
                (
                    product_name,
                    normalized_category,
                    validated_price,
                    validated_reorder_level,
                    supplier_id,
                    normalized_assigned_to,
                    product_id,
                ),
            )

        if normalized_assigned_to and normalized_assigned_to != previous_assigned_to:
            cursor.execute(
                adapt_query(f"""
                    INSERT INTO product_assignments (product_id, assigned_to, assigned_date, remarks, status)
                    VALUES (?, ?, {current_date_sql()}, ?, ?)
                """),
                (product_id, normalized_assigned_to, "Updated from component form", "In Progress"),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_product(product_id):
    execute("UPDATE products SET is_active = 0 WHERE product_id = ?", (product_id,))


# ---------------- PRODUCT ASSIGNMENTS ----------------
def update_product_assignment(product_id, assigned_to, assigned_date, remarks, status):
    assigned_to = require_text(assigned_to, "Assigned to")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("""
                UPDATE products
                SET assigned_to = ?
                WHERE product_id = ?
            """),
            (assigned_to, product_id),
        )

        cursor.execute(
            adapt_query("""
                INSERT INTO product_assignments (product_id, assigned_to, assigned_date, remarks, status)
                VALUES (?, ?, ?, ?, ?)
            """),
            (product_id, assigned_to, assigned_date, normalize_text(remarks), require_text(status, "Status")),
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_assignment_history():
    return read_dataframe("""
        SELECT pa.assignment_id, p.product_no, p.product_name,
               pa.assigned_to, pa.assigned_date, pa.remarks, pa.status
        FROM product_assignments pa
        LEFT JOIN products p ON pa.product_id = p.product_id
        ORDER BY pa.assignment_id DESC
    """)


# ---------------- PURCHASES ----------------
def add_purchase(product_id, supplier_id, quantity, unit_price, total_purchase_price, purchase_date, invoice_path):
    quantity = require_positive_int(quantity, "Quantity")
    unit_price = require_non_negative_number(unit_price, "Unit price")
    total_purchase_price = require_non_negative_number(total_purchase_price, "Total purchase price")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("""
                INSERT INTO purchases (
                    product_id, supplier_id, quantity_purchased, unit_price, total_purchase_price, purchase_date, invoice_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """),
            (product_id, supplier_id, quantity, unit_price, total_purchase_price, purchase_date, normalize_text(invoice_path)),
        )

        cursor.execute(
            adapt_query("""
                UPDATE products
                SET quantity = quantity + ?
                WHERE product_id = ?
            """),
            (quantity, product_id),
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_purchases():
    return read_dataframe("""
        SELECT pu.purchase_id, pu.product_id, pu.supplier_id,
               p.product_no, p.product_name, s.supplier_name,
               pu.quantity_purchased, pu.unit_price, pu.total_purchase_price,
               pu.purchase_date, pu.invoice_path
        FROM purchases pu
        LEFT JOIN products p ON pu.product_id = p.product_id
        LEFT JOIN suppliers s ON pu.supplier_id = s.supplier_id
        ORDER BY pu.purchase_id DESC
    """)


def update_purchase(purchase_id, quantity, supplier_id, purchase_date, invoice_path):
    quantity = require_positive_int(quantity, "Quantity")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("""
                SELECT product_id, quantity_purchased
                FROM purchases
                WHERE purchase_id = ?
            """),
            (purchase_id,),
        )
        old_data = cursor.fetchone()

        if old_data:
            product_id, old_quantity = old_data

            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET quantity = quantity - ?
                    WHERE product_id = ?
                """),
                (old_quantity, product_id),
            )

            cursor.execute(
                adapt_query("""
                    UPDATE purchases
                    SET quantity_purchased = ?, supplier_id = ?, total_purchase_price = unit_price * ?, purchase_date = ?, invoice_path = ?
                    WHERE purchase_id = ?
                """),
                (quantity, supplier_id, quantity, purchase_date, normalize_text(invoice_path), purchase_id),
            )

            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET quantity = quantity + ?
                    WHERE product_id = ?
                """),
                (quantity, product_id),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_purchase(purchase_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("""
                SELECT product_id, quantity_purchased
                FROM purchases
                WHERE purchase_id = ?
            """),
            (purchase_id,),
        )
        old_data = cursor.fetchone()

        if old_data:
            product_id, old_quantity = old_data

            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET quantity = quantity - ?
                    WHERE product_id = ?
                """),
                (old_quantity, product_id),
            )

        cursor.execute(adapt_query("DELETE FROM purchases WHERE purchase_id = ?"), (purchase_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------- SALES ----------------
def add_sale(product_id, quantity_sold, selling_price, sale_date, customer_name):
    quantity_sold = require_positive_int(quantity_sold, "Quantity sold")
    selling_price = require_non_negative_number(selling_price, "Selling price")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(adapt_query("SELECT quantity FROM products WHERE product_id = ?"), (product_id,))
        result = cursor.fetchone()

        if result is None:
            return "Product not found"

        available_stock = result[0]

        if quantity_sold > available_stock:
            return "Not enough stock available"

        cursor.execute(
            adapt_query("""
                INSERT INTO sales (product_id, quantity_sold, selling_price, sale_date, customer_name)
                VALUES (?, ?, ?, ?, ?)
            """),
            (product_id, quantity_sold, selling_price, sale_date, normalize_text(customer_name)),
        )

        cursor.execute(
            adapt_query("""
                UPDATE products
                SET quantity = quantity - ?
                WHERE product_id = ?
            """),
            (quantity_sold, product_id),
        )

        conn.commit()
        return "Sale added successfully"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sales():
    return read_dataframe("""
        SELECT s.sale_id, s.product_id, p.product_no, p.product_name,
               s.quantity_sold, s.selling_price,
               s.sale_date, s.customer_name,
               (s.quantity_sold * s.selling_price) AS total_sales_value
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id
        ORDER BY s.sale_id DESC
    """)


def update_sale(sale_id, quantity_sold, sale_date, customer_name):
    quantity_sold = require_positive_int(quantity_sold, "Quantity sold")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("""
                SELECT product_id, quantity_sold
                FROM sales
                WHERE sale_id = ?
            """),
            (sale_id,),
        )
        old_data = cursor.fetchone()

        if old_data:
            product_id, old_quantity = old_data

            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET quantity = quantity + ?
                    WHERE product_id = ?
                """),
                (old_quantity, product_id),
            )

            cursor.execute(adapt_query("SELECT price, quantity FROM products WHERE product_id = ?"), (product_id,))
            product_data = cursor.fetchone()
            selling_price = product_data[0]
            available_stock = product_data[1]

            if quantity_sold > available_stock:
                conn.rollback()
                return "Not enough stock available"

            cursor.execute(
                adapt_query("""
                    UPDATE sales
                    SET quantity_sold = ?, selling_price = ?, sale_date = ?, customer_name = ?
                    WHERE sale_id = ?
                """),
                (quantity_sold, selling_price, sale_date, normalize_text(customer_name), sale_id),
            )

            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET quantity = quantity - ?
                    WHERE product_id = ?
                """),
                (quantity_sold, product_id),
            )

        conn.commit()
        return "Sale updated successfully"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_sale(sale_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt_query("""
                SELECT product_id, quantity_sold
                FROM sales
                WHERE sale_id = ?
            """),
            (sale_id,),
        )
        old_data = cursor.fetchone()

        if old_data:
            product_id, old_quantity = old_data

            cursor.execute(
                adapt_query("""
                    UPDATE products
                    SET quantity = quantity + ?
                    WHERE product_id = ?
                """),
                (old_quantity, product_id),
            )

        cursor.execute(adapt_query("DELETE FROM sales WHERE sale_id = ?"), (sale_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------- LOW STOCK ----------------
def get_low_stock():
    return read_dataframe("""
        SELECT product_id, product_no, product_name, category, quantity, reorder_level, assigned_to
        FROM products
        WHERE quantity <= reorder_level
        ORDER BY quantity ASC
    """)


# ---------------- USERS / LOGIN SYSTEM ----------------
def create_default_admin():
    existing_admin = execute(
        "SELECT user_id FROM users WHERE username = ?",
        ("admin",),
        fetchone=True,
    )

    if existing_admin:
        return

    execute(
        """
        INSERT INTO users (
            full_name, username, password, role, department,
            date_of_joining, office_email, company_email, contact_number,
            can_edit_suppliers, can_delete_suppliers,
            can_edit_products, can_delete_products,
            can_edit_purchases, can_delete_purchases
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "System Administrator", "admin", hash_password("admin123"), "Admin", "Administration",
            "", "", "", "",
            1, 1, 1, 1, 1, 1,
        ),
    )


def add_user(full_name, username, password, role, department,
             date_of_joining, office_email, company_email, contact_number,
             can_edit_suppliers, can_delete_suppliers,
             can_edit_products, can_delete_products,
             can_edit_purchases, can_delete_purchases):
    full_name = require_text(full_name, "Full name")
    username = require_text(username, "Username")
    password = require_text(password, "Password")
    role = require_text(role, "Role")
    try:
        execute(
            """
            INSERT INTO users (
                full_name, username, password, role, department,
                date_of_joining, office_email, company_email, contact_number,
                can_edit_suppliers, can_delete_suppliers,
                can_edit_products, can_delete_products,
                can_edit_purchases, can_delete_purchases
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name, username, hash_password(password), role, normalize_text(department),
                normalize_text(date_of_joining), normalize_text(office_email),
                normalize_text(company_email), normalize_text(contact_number),
                can_edit_suppliers, can_delete_suppliers,
                can_edit_products, can_delete_products,
                can_edit_purchases, can_delete_purchases,
            ),
        )
        return "User added successfully"
    except Exception as error:
        if is_integrity_error(error):
            return "Username already exists"
        raise


def get_users():
    return read_dataframe("""
        SELECT user_id, full_name, username, role, department,
               date_of_joining, office_email, company_email, contact_number,
               can_edit_suppliers, can_delete_suppliers,
               can_edit_products, can_delete_products,
               can_edit_purchases, can_delete_purchases
        FROM users
        ORDER BY user_id DESC
    """)


def get_user_by_id(user_id):
    return execute(
        """
        SELECT user_id, full_name, username, role, department,
               date_of_joining, office_email, company_email, contact_number,
               can_edit_suppliers, can_delete_suppliers,
               can_edit_products, can_delete_products,
               can_edit_purchases, can_delete_purchases
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
        fetchone=True,
    )


def get_user_dropdown():
    return read_dataframe("""
        SELECT user_id, full_name, username, role
        FROM users
        ORDER BY full_name
    """)


def update_user(user_id, full_name, username, password, role, department,
                date_of_joining, office_email, company_email, contact_number,
                can_edit_suppliers, can_delete_suppliers,
                can_edit_products, can_delete_products,
                can_edit_purchases, can_delete_purchases):
    full_name = require_text(full_name, "Full name")
    username = require_text(username, "Username")
    role = require_text(role, "Role")
    department = normalize_text(department)

    if password and password.strip():
        hashed_password = hash_password(password.strip())
        execute(
            """
            UPDATE users
            SET full_name = ?, username = ?, password = ?, role = ?, department = ?,
                date_of_joining = ?, office_email = ?, company_email = ?, contact_number = ?,
                can_edit_suppliers = ?, can_delete_suppliers = ?,
                can_edit_products = ?, can_delete_products = ?,
                can_edit_purchases = ?, can_delete_purchases = ?
            WHERE user_id = ?
            """,
            (
                full_name, username, hashed_password, role, department,
                normalize_text(date_of_joining), normalize_text(office_email),
                normalize_text(company_email), normalize_text(contact_number),
                can_edit_suppliers, can_delete_suppliers,
                can_edit_products, can_delete_products,
                can_edit_purchases, can_delete_purchases,
                user_id,
            ),
        )
    else:
        execute(
            """
            UPDATE users
            SET full_name = ?, username = ?, role = ?, department = ?,
                date_of_joining = ?, office_email = ?, company_email = ?, contact_number = ?,
                can_edit_suppliers = ?, can_delete_suppliers = ?,
                can_edit_products = ?, can_delete_products = ?,
                can_edit_purchases = ?, can_delete_purchases = ?
            WHERE user_id = ?
            """,
            (
                full_name, username, role, department,
                normalize_text(date_of_joining), normalize_text(office_email),
                normalize_text(company_email), normalize_text(contact_number),
                can_edit_suppliers, can_delete_suppliers,
                can_edit_products, can_delete_products,
                can_edit_purchases, can_delete_purchases,
                user_id,
            ),
        )


def login_user(username, password):
    username = require_text(username, "Username")
    password = require_text(password, "Password")

    user = execute(
        """
        SELECT user_id, full_name, username, password, role, department,
               can_edit_suppliers, can_delete_suppliers,
               can_edit_products, can_delete_products,
               can_edit_purchases, can_delete_purchases
        FROM users
        WHERE username = ?
        """,
        (username,),
        fetchone=True,
    )

    if not user:
        return None

    stored_password = user[3]
    if not verify_password(password, stored_password):
        return None

    if not is_hashed_password(stored_password):
        execute(
            "UPDATE users SET password = ? WHERE user_id = ?",
            (hash_password(password), user[0]),
        )

    return (
        user[0],
        user[1],
        user[2],
        user[4],
        user[5],
        user[6],
        user[7],
        user[8],
        user[9],
        user[10],
        user[11],
    )


def delete_user(user_id):
    execute("DELETE FROM users WHERE user_id = ?", (user_id,))


# ---------------- NOTES ----------------
def add_note(note_title, note_content, created_by, created_date, note_status="Open", assigned_to=""):
    note_title = require_text(note_title, "Note title")
    note_content = require_text(note_content, "Note content")
    execute(
        """
        INSERT INTO notes (note_title, note_content, created_by, created_date, note_status, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            note_title,
            note_content,
            normalize_text(created_by),
            created_date,
            require_text(note_status, "Note status"),
            normalize_text(assigned_to),
        ),
    )


def get_notes():
    return read_dataframe("""
        SELECT *
        FROM notes
        ORDER BY note_id DESC
    """)


def update_note(note_id, note_title, note_content, note_status, assigned_to=""):
    note_title = require_text(note_title, "Note title")
    note_content = require_text(note_content, "Note content")
    execute(
        """
        UPDATE notes
        SET note_title = ?, note_content = ?, note_status = ?, assigned_to = ?
        WHERE note_id = ?
        """,
        (note_title, note_content, require_text(note_status, "Note status"), normalize_text(assigned_to), note_id),
    )


def delete_note(note_id):
    execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
