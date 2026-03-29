# PostgreSQL Setup

This project can run with either SQLite or PostgreSQL.

## 1. Keep local SQLite for now

The default setting in `.env.example` is:

```env
DB_BACKEND=sqlite
```

If you do nothing, the app will continue using the local `inbound_inventory.db` file.

## 2. Move to a central PostgreSQL server

On the PostgreSQL server machine:

1. Install PostgreSQL.
2. Create a database:

```sql
CREATE DATABASE inbound_inventory;
```

3. Create an app user:

```sql
CREATE USER inventory_user WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE inbound_inventory TO inventory_user;
```

4. Connect to the new database and allow schema creation:

```sql
\c inbound_inventory
GRANT USAGE, CREATE ON SCHEMA public TO inventory_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO inventory_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO inventory_user;
```

## 3. Configure each employee PC

Create a `.env` file in the project folder using this format:

```env
DB_BACKEND=postgres
DB_HOST=192.168.1.10
DB_PORT=5432
DB_NAME=inbound_inventory
DB_USER=inventory_user
DB_PASSWORD=change_me
```

Replace `192.168.1.10` with your PostgreSQL server IP address.

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Start the app

```bash
streamlit run app.py
```

On first launch, `create_tables()` will create the required tables automatically.

## 5a. Migrate existing SQLite data

If you already have data in `inbound_inventory.db`, run:

```bash
python migrate_sqlite_to_postgres.py
```

Make sure `.env` is already configured for PostgreSQL before running it.

## 6. Shared files

Database records will be shared through PostgreSQL, but uploaded images and invoices must also be shared.

Recommended options:

1. Use a shared network folder for `product_images` and `purchase_invoices`.
2. Later, move file storage into a central file server or object storage.

If files stay on each employee PC, other users will not be able to open those files.
