# Deploy Reef backend on Google Compute Engine (GCE)

Run Reef on a single VM with **Docker Compose**: FastAPI + Postgres + Coral CLI with persistent Coral config. **nginx + Let's Encrypt** terminate HTTPS on `:443`; uvicorn stays on `127.0.0.1:8000` only.

Best for:
- Real `CORAL_MODE=cli` investigations in the cloud
- Persistent investigation history (Postgres volume)
- Coral source config that survives restarts (`/data/coral` volume)

---

## Architecture

```text
Internet
   │
   ▼
GCE VM (e2-medium recommended)
   ├── nginx :443 (Let's Encrypt TLS) → proxy → 127.0.0.1:8000
   ├── docker compose
   │     ├── postgres:16  → volume postgres_data
   │     └── reef-api     → volume coral_data (/data/coral)
   │           ├── uvicorn (localhost only)
   │           ├── coral CLI (subprocess)
   │           └── setup_coral_sources.sh on startup
   └── firewall: tcp:80, tcp:443
```

Frontend stays on **Vercel**; set `VITE_API_BASE_URL=https://api.yourdomain.com`.

---

## 1. Create the VM

Use a **zone** (e.g. `us-east1-b`), not a region (`us-east1` will fail).

```bash
export PROJECT_ID=your-gcp-project
export ZONE=us-east1-b          # us-east1-b | us-east1-c | us-east1-d
export VM_NAME=reef-backend

gcloud config set project "$PROJECT_ID"

gcloud compute instances create "$VM_NAME" \
  --zone="$ZONE" \
  --machine-type=e2-medium \
  --boot-disk-size=30GB \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --tags=reef-api

gcloud compute firewall-rules create allow-reef-https \
  --allow=tcp:80,tcp:443 \
  --target-tags=reef-api \
  --description="HTTP (ACME) and HTTPS for Reef API"
```

Reserve a static IP and point your DNS **A record** (e.g. `api.yourdomain.com`) at it:

```bash
gcloud compute addresses create reef-api-ip --region=us-east1
gcloud compute addresses describe reef-api-ip --region=us-east1 --format='get(address)'

# Attach to the VM (stop first if already running with an ephemeral IP)
gcloud compute instances delete-access-config "$VM_NAME" --zone="$ZONE" --access-config-name="External NAT" 2>/dev/null || true
gcloud compute instances add-access-config "$VM_NAME" \
  --zone="$ZONE" \
  --access-config-name="External NAT" \
  --address="$(gcloud compute addresses describe reef-api-ip --region=us-east1 --format='get(address)')"
```

If you previously created `allow-reef-api` (port 8000), remove it — the API should not be public on 8000:

```bash
gcloud compute firewall-rules delete allow-reef-api --quiet
```

---

## 2. SSH and install Docker

```bash
gcloud compute ssh "$VM_NAME" --zone="$ZONE"
```

On the VM:

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
```

---

## 3. Clone repo and configure env

```bash
git clone https://github.com/YOUR_ORG/coral_hackers.git
cd coral_hackers/backend

cp ../deploy/gce/env.production.example .env
nano .env   # fill tokens, POSTGRES_PASSWORD, CORS_ORIGINS
```

Required for `CORAL_MODE=cli`:
- `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`
- `SENTRY_ORG`, `SENTRY_TOKEN`
- `SLACK_TOKEN`
- `VERCEL_TOKEN`

Set `CORS_ORIGINS` to your Vercel URL, e.g.:

```bash
CORS_ORIGINS=https://reef-demo.vercel.app
```

Bind the API to localhost only (edit `docker-compose.yml` **ports** for the `api` service):

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

---

## 4. Start the stack

```bash
cd ~/coral_hackers/backend
docker compose up -d --build
docker compose logs -f api
```

First boot will:
1. Wait for Postgres
2. Run `init_db()` (create tables)
3. Run `setup_coral_sources.sh` (register github/sentry/slack/vercel)
4. Start uvicorn on `127.0.0.1:8000`

Health check on the VM:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

---

## 5. nginx + Let's Encrypt (HTTPS on :443)

On the VM, install nginx and Certbot:

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/reef-api` (replace `api.yourdomain.com`):

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and obtain a certificate:

```bash
sudo ln -sf /etc/nginx/sites-available/reef-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d api.yourdomain.com
```

Certbot will add TLS on `:443` and redirect HTTP → HTTPS. Renewal is automatic via `certbot` systemd timer.

From your laptop:

```bash
curl https://api.yourdomain.com/health
# {"status":"ok"}
```

---

## 6. Wire the frontend (Vercel)

In Vercel project settings → Environment variables:

```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

Redeploy the frontend. The dashboard will call `https://api.yourdomain.com/api/v1/...`.

---

## 7. Sentry webhook

Point Sentry internal integration to:

```text
https://api.yourdomain.com/api/v1/webhooks/sentry
```

---

## Optional: Cloud SQL instead of container Postgres

1. Create Cloud SQL Postgres instance
2. On the VM, set in `.env`:

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@/reef?host=/cloudsql/PROJECT:REGION:INSTANCE
```

3. Remove the `postgres` service from `docker-compose.yml` or run API only:

```bash
docker compose up -d --build api
```

Authorize the VM service account for Cloud SQL Auth Proxy if using the proxy sidecar.

---

## Operations

| Task | Command |
|------|---------|
| Logs | `docker compose logs -f api` |
| Restart | `docker compose restart api` |
| Rebuild after git pull | `docker compose up -d --build` |
| Re-run Coral setup | `docker compose exec api /app/scripts/setup_coral_sources.sh` |
| Shell into API container | `docker compose exec api bash` |
| Renew TLS (manual) | `sudo certbot renew` |
| nginx reload | `sudo nginx -t && sudo systemctl reload nginx` |

---

## Troubleshooting

**`Invalid value for field 'zone': 'us-east1'`**  
You set a region instead of a zone. Use `us-east1-b`, `us-east1-c`, or `us-east1-d`:

```bash
gcloud compute zones list --filter="region:us-east1"
```

**Coral setup fails on startup**

- **`GLIBC_2.39 not found`**: the API image must use a recent base (e.g. `python:3.12-slim-trixie` in `backend/Dockerfile`). Rebuild with `docker compose build --no-cache api`.
- **Missing tokens**: ensure `GITHUB_TOKEN`, `SENTRY_ORG`, `SENTRY_TOKEN`, `SLACK_TOKEN`, `VERCEL_TOKEN` are set in `backend/.env`.

```bash
docker compose exec api coral --version
docker compose exec api /app/scripts/setup_coral_sources.sh
```

**Investigations empty / mock data**  
Confirm `CORAL_MODE=cli` in `.env` and Coral sources listed:

```bash
docker compose exec api coral source list
```

**CORS errors from Vercel**  
Add your exact frontend origin to `CORS_ORIGINS` (scheme + host, no trailing slash).

**502 from nginx**  
Confirm the API is up and bound to localhost:

```bash
curl http://127.0.0.1:8000/health
docker compose ps
```

**Data lost after rebuild**  
Do not `docker compose down -v` unless you intend to wipe volumes. Postgres and Coral config live in named volumes.

---

## Cost ballpark

- `e2-medium` VM: ~$25–30/mo (region-dependent)
- Static external IP: small monthly charge if reserved
- Cloud SQL: extra if you switch from container Postgres

Stop the VM when not demoing to save cost:

```bash
gcloud compute instances stop "$VM_NAME" --zone="$ZONE"
```
