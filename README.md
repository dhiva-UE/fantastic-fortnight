# Inbound Inventory

Inbound inventory management software with a React frontend and FastAPI backend.

The default project setup is now offline/local using SQLite on the same computer.

## Stack

- `frontend/`: React + Vite
- `backend/`: FastAPI API
- `database.py`: shared database access layer for PostgreSQL or SQLite

## Local development

1. Create `.env` from [.env.example](C:/Inventory_managment_tool/Inbound_Inventory/.env.example), or use the existing `.env`.
2. For offline/local mode, keep:

```env
DB_BACKEND=sqlite
```

3. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

4. Install frontend dependencies:

```bash
cd frontend
npm install
```

5. Start the backend:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

6. Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

The Vite dev server runs on `5173` and proxies `/api` and `/media` to the FastAPI backend.

Offline/local instructions are also available in [OFFLINE_SETUP.md](C:/Inventory_managment_tool/Inbound_Inventory/OFFLINE_SETUP.md).

## Production deployment

This repo now includes:

- [backend/Dockerfile](C:/Inventory_managment_tool/Inbound_Inventory/backend/Dockerfile)
- [frontend/Dockerfile](C:/Inventory_managment_tool/Inbound_Inventory/frontend/Dockerfile)
- [frontend/nginx.conf](C:/Inventory_managment_tool/Inbound_Inventory/frontend/nginx.conf)
- [docker-compose.prod.yml](C:/Inventory_managment_tool/Inbound_Inventory/docker-compose.prod.yml)

Deployment instructions are in [DEPLOYMENT.md](C:/Inventory_managment_tool/Inbound_Inventory/DEPLOYMENT.md).

## Security notes

- Set a strong `AUTH_SECRET_KEY` in production.
- Rotate any old database passwords before deploying.
- Keep `CORS_ORIGINS` limited to your real frontend domain.
- Never commit the real `.env` file.
