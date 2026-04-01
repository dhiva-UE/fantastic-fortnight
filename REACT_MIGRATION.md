# React Migration

This project now includes a parallel React + FastAPI migration scaffold while preserving the working Streamlit app.

## Structure

- `app.py`
  Current Streamlit application
- `backend/`
  FastAPI backend for the new React app
- `frontend/`
  React + Vite frontend for the new app

## Current migration scope

Implemented in the new stack:

- Login API
- Dashboard API
- Suppliers API and React module
- Components API and React module
- Components Responsibility API and React module
- Purchases API and React module
- Sales API and React module
- Notes API and React module
- Users API and React module
- Reports API and React module
- Shared upload endpoints for product images and purchase invoices
- React login screen
- React dashboard shell

The rest of the modules can be migrated one by one next.

## Run the backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

## Run the frontend

Node.js is required for the React frontend.

1. Install Node.js LTS
2. Then run:

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## Notes

- The backend reuses the existing `database.py`, so PostgreSQL settings still come from `.env`.
- The Streamlit app remains available during the migration.
- The next recommended migration slice is:
  1. Permission-aware navigation
  2. Filters/export actions in reports
  3. Dedicated low-stock screen
  4. Final UI polish against company theme
