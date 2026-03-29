import os
import sqlite3
from pathlib import Path

import psycopg2

from database import create_tables


BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "inbound_inventory.db"


def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_sqlite_connection():
    return sqlite3.connect(SQLITE_DB_PATH)


def get_postgres_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "inbound_inventory"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin@123"),
    )


def reset_postgres_tables(cursor):
    cursor.execute(
        """
        TRUNCATE TABLE
            product_assignments,
            purchases,
            sales,
            notes,
            products,
            suppliers,
            users
        RESTART IDENTITY CASCADE
        """
    )


def copy_table(sqlite_conn, postgres_cursor, table_name, columns):
    column_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    rows = sqlite_conn.execute(f"SELECT {column_list} FROM {table_name}").fetchall()
    for row in rows:
        postgres_cursor.execute(
            f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
            row,
        )


def main():
    load_env_file()

    if os.getenv("DB_BACKEND", "").strip().lower() not in {"postgres", "postgresql"}:
        raise SystemExit("Set DB_BACKEND=postgres in .env before running this migration.")

    create_tables()

    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()

    try:
        postgres_cursor = postgres_conn.cursor()
        reset_postgres_tables(postgres_cursor)

        copy_table(
            sqlite_conn,
            postgres_cursor,
            "suppliers",
            ["supplier_id", "supplier_name", "contact_number", "email", "address"],
        )
        copy_table(
            sqlite_conn,
            postgres_cursor,
            "products",
            [
                "product_id",
                "product_no",
                "product_name",
                "category",
                "price",
                "quantity",
                "reorder_level",
                "supplier_id",
                "image_path",
                "assigned_to",
            ],
        )
        copy_table(
            sqlite_conn,
            postgres_cursor,
            "purchases",
            [
                "purchase_id",
                "product_id",
                "supplier_id",
                "quantity_purchased",
                "unit_price",
                "total_purchase_price",
                "purchase_date",
                "invoice_path",
            ],
        )
        copy_table(
            sqlite_conn,
            postgres_cursor,
            "sales",
            [
                "sale_id",
                "product_id",
                "quantity_sold",
                "selling_price",
                "sale_date",
                "customer_name",
            ],
        )
        copy_table(
            sqlite_conn,
            postgres_cursor,
            "product_assignments",
            [
                "assignment_id",
                "product_id",
                "assigned_to",
                "assigned_date",
                "remarks",
                "status",
            ],
        )
        copy_table(
            sqlite_conn,
            postgres_cursor,
            "users",
            [
                "user_id",
                "full_name",
                "username",
                "password",
                "role",
                "department",
                "can_edit_suppliers",
                "can_delete_suppliers",
                "can_edit_products",
                "can_delete_products",
                "can_edit_purchases",
                "can_delete_purchases",
            ],
        )
        copy_table(
            sqlite_conn,
            postgres_cursor,
            "notes",
            [
                "note_id",
                "note_title",
                "note_content",
                "created_by",
                "created_date",
                "note_status",
            ],
        )

        postgres_conn.commit()
        print("Migration completed successfully.")
    except Exception:
        postgres_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        postgres_conn.close()


if __name__ == "__main__":
    main()
