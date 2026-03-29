# Inbound Inventory

Simple inbound inventory management software built with Streamlit.

## Features

- Product and supplier management
- Purchase and sales tracking
- Assignment history
- Notes and reports
- PostgreSQL or SQLite backend support

## Setup

1. Install Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local environment file from the example:

```bash
copy .env.example .env
```

4. Edit `.env` with your database settings.

5. Start the app:

```bash
streamlit run app.py
```

## Multi-computer access

For multiple users, use PostgreSQL as the shared database and configure shared folders for:

- `PRODUCT_IMAGES_DIR`
- `PURCHASE_INVOICES_DIR`

See `POSTGRES_SETUP.md` for details.

## Security

- Never commit the real `.env` file.
- Do not commit local database files or uploaded documents.
