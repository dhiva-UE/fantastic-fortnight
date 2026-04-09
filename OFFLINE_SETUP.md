# Offline Setup

This project can run fully offline on a single computer.

## Recommended offline stack

- React frontend
- FastAPI backend
- local SQLite database: [inbound_inventory.db](C:/Inventory_managment_tool/Inbound_Inventory/inbound_inventory.db)

No internet connection is required for normal use.

## 1. Environment

The project root [.env](C:/Inventory_managment_tool/Inbound_Inventory/.env) should use:

```env
DB_BACKEND=sqlite
```

That makes the app use the local SQLite file automatically.

## 2. Install dependencies

Backend:

```powershell
cd C:\Inventory_managment_tool\Inbound_Inventory
python -m pip install -r backend\requirements.txt
```

Frontend:

```powershell
cd C:\Inventory_managment_tool\Inbound_Inventory\frontend
npm.cmd install
```

## 3. Run locally

Backend:

```powershell
cd C:\Inventory_managment_tool\Inbound_Inventory
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\Inventory_managment_tool\Inbound_Inventory\frontend
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:5173/
```

## 4. Files and uploads

For offline usage, uploaded files stay on the same computer:

- [product_images](C:/Inventory_managment_tool/Inbound_Inventory/product_images)
- [purchase_invoices](C:/Inventory_managment_tool/Inbound_Inventory/purchase_invoices)
- [storage](C:/Inventory_managment_tool/Inbound_Inventory/storage)

## 5. Important note about data

Switching back to SQLite changes the app to use the local database file again.

If your newest live data currently exists only in PostgreSQL, that data will not automatically appear in SQLite until we copy/migrate it back.

If you want, the next step can be:

1. add bulk import from Excel/CSV for components
2. export PostgreSQL data back into SQLite for the offline client build
