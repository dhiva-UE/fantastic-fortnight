# Deployment Guide

This repo now supports a production-style deployment using:

- `frontend` as a static React build served by Nginx
- `backend` as a FastAPI service
- `postgres` as the database

The easiest first cloud deployment is a Linux VM with Docker Compose. After that, you can swap the built-in PostgreSQL container for a managed cloud PostgreSQL service.

## 1. Prepare environment variables

Create a real `.env` in the project root.

Minimum required values:

```env
APP_ENV=production
DB_BACKEND=postgres
DB_HOST=postgres
DB_PORT=5432
DB_NAME=inbound_inventory
DB_USER=inventory_user
DB_PASSWORD=replace_with_a_strong_password
CORS_ORIGINS=https://your-domain.com
AUTH_SECRET_KEY=replace_with_a_long_random_secret
AUTH_TOKEN_TTL_MINUTES=480
MAX_UPLOAD_BYTES=5242880
```

Important:

- `AUTH_SECRET_KEY` must be long and random in production.
- rotate any previous database password before deployment.
- if you use a managed PostgreSQL service, set `DB_HOST` to that host instead of `postgres`.

## 2. Deploy on a cloud VM

Recommended baseline:

- Ubuntu 22.04 or 24.04
- 2 vCPU
- 4 GB RAM
- attached disk for PostgreSQL and uploaded files

Copy the repo to the server, then run:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This will start:

- frontend on port `80`
- backend internally on port `8000`
- PostgreSQL internally on port `5432`

## 3. Set up HTTPS

Do not expose plain HTTP for production users.

Recommended:

- put Cloudflare, Caddy, or Nginx with Let's Encrypt in front of the VM
- point your domain to the VM
- terminate TLS at the edge or reverse proxy

If you already use a cloud load balancer, terminate HTTPS there and forward traffic to port `80` on this stack.

## 4. Persistent storage

This compose file persists:

- PostgreSQL data
- product images
- purchase invoices

Named Docker volumes are used by default. For stricter control, replace them with mounted host directories or cloud block volumes.

## 5. Managed PostgreSQL option

For a stronger cloud setup:

1. Create a managed PostgreSQL instance.
2. Update `.env` with the managed host, port, database, username, and password.
3. Remove or ignore the `postgres` service from `docker-compose.prod.yml`.
4. Keep the `frontend` and `backend` services.

That is the recommended next step after your first successful deployment.

## 6. Operational checklist

- Change the default admin password immediately after first login.
- Restrict the VM firewall to `80/443` only.
- Back up the database and uploaded files.
- Monitor container restarts and disk usage.
- Keep `CORS_ORIGINS` limited to your real frontend domain.
- Never commit the real `.env`.
