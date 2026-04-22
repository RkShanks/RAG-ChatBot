# RAG Chatbot — Deployment Guide

This guide covers two scenarios:
1. **[Local Testing](#local-testing)** — run the full stack on your machine before deploying
2. **[Oracle Cloud Production](#oracle-cloud-production)** — deploy to a real server with SSL

---

## Prerequisites

Both scenarios require:
- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose plugin](https://docs.docker.com/compose/install/) (`docker compose`, not `docker-compose`)
- Your API keys: Gemini, Cohere, and optionally OpenAI/Ranker

---

## Local Testing

Run the full stack on `http://localhost` — no domain, no SSL required.

### Step 1 — Create your local `.env.docker`

```bash
cp .env.docker.example .env.docker
```

Then open `.env.docker` and fill in **at minimum**:

```env
GEMINI_API_KEY=your-real-key
COHERE_API_KEY=your-real-key
GRAFANA_ADMIN_PASSWORD=anypassword
QDRANT_API_KEY=anykey
```

> The Mongo, Qdrant, and Telegram/email fields can stay as CHANGE_ME for local testing —
> those services will still start, but alerts won't fire and Qdrant auth will be whatever you set.

### Step 2 — Start the stack

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

This merges the production compose with the local override which:
- Replaces the Loki logging driver with standard `json-file` (no plugin needed)
- Uses `config/nginx-local.conf` (HTTP only, no SSL)
- Skips Certbot (no domain required)

### Step 3 — Verify everything is running

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
```

All services should show `running` or `healthy`:

| Service | URL |
|---|---|
| Frontend (via nginx) | http://localhost |
| Backend API | http://localhost/api/v1/ |
| Health check | http://localhost/api/v1/health |
| Grafana | http://localhost:3001 (admin / your password) |
| Prometheus | http://localhost:9090 |
| Loki | http://localhost:3100 |

### Step 4 — Test the application

1. Open http://localhost
2. Create a workspace and upload a `.pdf` or `.docx` file
3. Ask a question about the document — verify citations appear
4. Click a filename in the sidebar — verify the preview modal opens
5. Check http://localhost/api/v1/health returns `{"status": "healthy"}`
6. Check http://localhost:9090/targets — `rag-backend` should show **UP**
7. In Grafana → Explore → Loki, run `{service="backend"}` — no logs will appear
   (the Loki driver is disabled locally, logs go to Docker's json-file instead)

### Step 5 — Tear down

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down

# To also delete all data volumes (full reset):
docker compose -f docker-compose.yml -f docker-compose.local.yml down -v
```

---

## Oracle Cloud Production

Full deployment with SSL, Loki logging, and Telegram/Gmail alerting.

### Infrastructure Requirements

- Oracle Cloud Ampere A1 instance (Free Tier: 4 OCPU / 24 GB RAM)
- Ubuntu 22.04
- A [DuckDNS](https://www.duckdns.org/) subdomain (free) pointing to your VM's public IP

### Step 1 — Provision the Oracle Cloud VM

1. Log in to [Oracle Cloud Console](https://cloud.oracle.com/)
2. Create a new **Compute Instance**:
   - Shape: `VM.Standard.A1.Flex` (Ampere ARM)
   - OCPU: 4, RAM: 24 GB
   - OS: Ubuntu 22.04
   - Add your SSH public key
3. Open firewall ports in the Oracle Console (Security List):
   - TCP 22 (SSH)
   - TCP 80 (HTTP / Certbot challenge)
   - TCP 443 (HTTPS)
   - TCP 3001 (Grafana — optionally restrict to your IP)

### Step 2 — Install Docker on the VM

```bash
ssh ubuntu@YOUR_VM_IP

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### Step 3 — Install the Loki Docker Logging Plugin

> **Required** — without this, `docker compose up` will fail because the backend
> uses `driver: loki` in its logging config.

```bash
docker plugin install grafana/loki-docker-driver:latest \
  --alias loki \
  --grant-all-permissions
```

### Step 4 — Set up DuckDNS

1. Register at https://www.duckdns.org/
2. Create a subdomain, e.g. `yourname-rag.duckdns.org`
3. Set it to point to your Oracle VM's **public IP**
4. Add an auto-renewal cron (keeps the IP updated if it changes):

```bash
crontab -e
# Add this line:
*/5 * * * * curl -s "https://www.duckdns.org/update?domains=yourname-rag&token=YOUR_TOKEN&ip=" > /tmp/duckdns.log 2>&1
```

### Step 5 — Clone the repository and configure

```bash
git clone https://github.com/YOUR_USERNAME/RAG-ChatBot.git
cd RAG-ChatBot

cp .env.docker.example .env.docker
nano .env.docker
```

Fill in **all** values in `.env.docker`:

| Key | Description |
|---|---|
| `MONGO_PASS` | Strong password (also update in `MONGODB_URI`) |
| `QDRANT_API_KEY` | Strong random key |
| `GEMINI_API_KEY` | From Google AI Studio |
| `COHERE_API_KEY` | From Cohere dashboard |
| `GRAFANA_ADMIN_PASSWORD` | Strong password for Grafana UI |
| `TELEGRAM_BOT_TOKEN` | From @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/group ID |
| `ALERT_EMAIL` | Gmail address for alerts |
| `DOMAIN` | Your DuckDNS subdomain (e.g. `yourname-rag.duckdns.org`) |
| `CERTBOT_EMAIL` | Email for Let's Encrypt notifications |

### Step 6 — Update nginx.conf with your domain

```bash
sed -i 's/YOUR_DOMAIN/yourname-rag.duckdns.org/g' config/nginx.conf
```

### Step 7 — Obtain the SSL certificate

> Run this BEFORE starting the full stack. nginx must be running for the ACME challenge.

```bash
# Start only nginx and certbot
docker compose up -d nginx
docker compose run --rm certbot

# Verify certs were issued
docker compose run --rm certbot certificates
```

### Step 8 — Start the full stack

```bash
docker compose up --build -d
```

### Step 9 — Verify production deployment

```bash
# Check all 9 services are healthy
docker compose ps

# Tail live logs
docker compose logs -f backend
```

| Check | URL |
|---|---|
| App (HTTPS) | https://yourname-rag.duckdns.org |
| Health endpoint | https://yourname-rag.duckdns.org/api/v1/health |
| Grafana | https://yourname-rag.duckdns.org:3001 |
| Prometheus | http://YOUR_VM_IP:9090/targets (internal only) |

### Step 10 — Import Grafana Dashboards

After confirming the stack is healthy:

1. Open Grafana at port `:3001`
2. Log in with `admin` / your `GRAFANA_ADMIN_PASSWORD`
3. Go to **Dashboards → Import**:
   - Enter ID `16110` → select **Prometheus** datasource → Import (FastAPI metrics)
   - Enter ID `13639` → select **Loki** datasource → Import (Log explorer)

### SSL Certificate Renewal

Let's Encrypt certs expire every 90 days. Test renewal works:

```bash
docker compose run --rm certbot renew --dry-run
```

To automate renewal, add to crontab:

```bash
crontab -e
# Add:
0 3 * * * cd /home/ubuntu/RAG-ChatBot && docker compose run --rm certbot renew --quiet && docker compose exec nginx nginx -s reload
```

---

## Useful Commands

```bash
# View logs for a specific service
docker compose logs -f backend
docker compose logs -f frontend

# Restart a single service (e.g. after config change)
docker compose restart nginx

# Stop everything (keep volumes / data)
docker compose down

# Full reset — deletes ALL data
docker compose down -v

# Rebuild a single service after code changes
docker compose up --build -d backend
```

---

## File Structure Reference

```
RAG-ChatBot/
├── docker-compose.yml           # Production: 9 services
├── docker-compose.local.yml     # Local override: skips SSL + Loki driver
├── .env.docker.example          # Template — copy to .env.docker and fill in
├── .env.docker                  # Real secrets — gitignored, never commit this
├── .dockerignore                # Excludes .venv, node_modules from image builds
├── docker/
│   ├── Dockerfile.backend       # Python 3.13 + uv FastAPI image
│   └── Dockerfile.frontend      # Node 20 Next.js standalone image
└── config/
    ├── nginx.conf               # Production: SSL + reverse proxy
    ├── nginx-local.conf         # Local: HTTP-only proxy
    ├── loki-config.yml          # Loki log aggregation config
    ├── prometheus.yml           # Prometheus scrape config
    ├── grafana-datasources.yml  # Auto-provisions Loki + Prometheus in Grafana
    ├── grafana-dashboards.yml   # Dashboard provider config
    ├── grafana-alerts.yml       # Alert rules (error spike, service down)
    └── grafana-contact-points.yml # Telegram + Gmail notification routing
```
