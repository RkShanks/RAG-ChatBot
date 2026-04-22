# RAG ChatBot — Retrieval-Augmented Generation Platform

> A production-ready, multi-document RAG system with persistent memory, real-time streaming, and a full observability stack. Built for portfolio demonstration of enterprise-grade full-stack AI engineering.

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.133-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7-47A248?logo=mongodb)](https://mongodb.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.13-FF4F64)](https://qdrant.tech)

---

## What Is This?

This project is a **stateful, multi-workspace RAG chatbot** that allows users to upload documents and have intelligent, context-aware conversations about their content. It goes far beyond a basic chatbot — it is a full-stack, cloud-deployable AI platform demonstrating real engineering depth.

**Key capabilities:**

- 📄 **Multi-format document ingestion** — PDF, DOCX, PPTX, XLSX, HTML, Markdown, TXT via [Docling](https://github.com/DS4SD/docling)
- 💬 **Real-time streaming responses** via Server-Sent Events (SSE) — no polling, no delays
- 🔖 **Source citations** — every answer includes the exact filename, page number, and relevance score it was derived from
- 🧠 **Persistent conversation memory** — chat history survives page refreshes, stored in MongoDB per workspace
- 🗂️ **Multi-workspace isolation** — each workspace has its own document set, history, and vector index
- 🔍 **Hybrid semantic search** — dense + sparse vector retrieval with cross-encoder reranking via Cohere
- 👁️ **Document preview** — inline modal to read source documents without leaving the chat
- 📊 **Full observability** — Prometheus metrics, Loki log aggregation, Grafana dashboards and alerting
- 🐳 **Docker-first deployment** — single `docker compose up` brings up 9 services on any machine

---

## Architecture

```
  ╔══════════════════════════════════[ app network ]═════════════════════════════════╗
  ║                                                                                  ║
  ║   ┌──────────────────────────────────────────────────────────────────────────┐   ║
  ║   │                         nginx (reverse proxy)                            │   ║
  ║   │         Port 80 → HTTPS redirect / Certbot ACME challenge                │   ║
  ║   │         Port 443 → /api/* → backend  |  /* → frontend                    │   ║
  ║   └────────────────────┬──────────────────────────────────┬──────────────────┘   ║
  ║                        │                                  │                      ║
  ║            ┌───────────▼───────────┐        ┌─────────────▼───────────────┐      ║
  ║            │    Next.js Frontend   │        │       FastAPI Backend       │      ║
  ║            │    (Node 20 · SSR)    │        │      (Python 3.13 + uv)     │      ║
  ║            └───────────────────────┘        └──────┬───────────────┬──────┘      ║
  ║                                                    │               │             ║
  ╚════════════════════════════════════════════════════╪═══════════════╪═════════════╝
                                                       │               │
                                 ┌─────────────────────┘               │
                                 │                                     │
                                 ▼                                     ▼
  ╔═══[ internal network ]═══════════════════════╗   ╔══════════════════════[ observability ]═════╗
  ║                                              ║   ║                                            ║
  ║   ┌────────────────┐       ┌──────────────┐  ║   ║   ┌──────────┐      ┌──────────┐           ║
  ║   │   MongoDB 7    │       │ Qdrant v1.13 │  ║   ║   │Prometheus│      │   Loki   │           ║
  ║   │ (chat history, │       │  (vector     │  ║   ║   │(scrapes  │      │(log aggr)│           ║
  ║   │  projects,     │       │   storage,   │  ║   ║   │ /metrics │      │          │           ║
  ║   │  file registry)│       │  dense+sparse│  ║   ║   │ · 15sec) │      │          │           ║
  ║   └────────────────┘       └──────────────┘  ║   ║   └─────┬────┘      └─────┬────┘           ║
  ║                                              ║   ║         └───────┬─────────┘                ║
  ╚══════════════════════════════════════════════╝   ║   ┌─────────────▼────────────┐             ║
                                                     ║   │ Grafana (dashbd+alerts)  │             ║
                                                     ║   └──────────────────────────┘             ║
                                                     ╚════════════════════════════════════════════╝
```

**Docker Network Topology**

| Network | Services | Purpose |
|---|---|---|
| `internal` | mongodb, qdrant, backend | Database tier — DBs are unreachable from nginx/frontend |
| `app` | nginx, frontend, backend | Traffic-facing tier — serves HTTP/HTTPS requests |
| `observability` | backend, prometheus, loki, grafana | Monitoring plane — isolated from public traffic |

---

## Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Next.js 16, TypeScript, Tailwind | Chat UI, workspace management, SSE stream rendering |
| **Backend** | FastAPI, Python 3.13, uv | REST API, SSE streaming, document ingestion pipeline |
| **LLM** | Google Gemini / OpenAI | Text generation (hot-swappable via settings UI) |
| **Embeddings** | Cohere `embed-multilingual-v3.0` | Dense vector embeddings |
| **Sparse** | SPLADE (fastembed) | Sparse vector retrieval for keyword matching |
| **Reranker** | Cohere Rerank | Cross-encoder reranking of candidate chunks |
| **Vector DB** | Qdrant v1.13 | Hybrid dense+sparse vector search |
| **Document DB** | MongoDB 7 | Project metadata, chat history, file registry |
| **Ingestion** | Docling | Multi-format document parsing with accurate page-level metadata |
| **Proxy** | nginx | Reverse proxy, SSL termination, SSE buffering disabled |
| **Observability** | Prometheus + Loki + Grafana | Metrics, logs, dashboards, Telegram/email alerting |
| **Containerization** | Docker Compose | 9-service orchestration, named volumes, health checks |

---

## Project Structure

```
RAG-ChatBot/
├── src/                          # FastAPI backend
│   ├── main.py                   # App entrypoint, lifespan, middleware
│   ├── routes/                   # API route handlers (base, data, nlp, documents, settings)
│   ├── controllers/              # Business logic layer
│   ├── models/                   # MongoDB ODM models
│   ├── services/                 # LLM, VectorDB, Ranker factory abstractions
│   └── helpers/                  # Config, logging, exceptions, enums
├── frontend/                     # Next.js frontend
│   ├── app/
│   │   ├── components/           # ChatBox, Sidebar, DocumentPreview, Settings
│   │   ├── lib/api.ts            # Axios client with global error interceptor
│   │   └── page.tsx              # Root layout and workspace orchestration
│   └── next.config.ts            # Standalone output for Docker
├── docker/
│   ├── Dockerfile.backend        # Python 3.13-slim + uv (multi-stage)
│   └── Dockerfile.frontend       # Node 20 Alpine (multi-stage standalone)
├── config/
│   ├── nginx.conf                # Production: SSL + SSE-safe proxy
│   ├── nginx-local.conf          # Local: HTTP-only proxy
│   ├── loki-config.yml           # Loki single-node config (tsdb v13)
│   ├── prometheus.yml            # Prometheus scrape config
│   ├── grafana-datasources.yml   # Auto-provisions Loki + Prometheus
│   ├── grafana-alerts.yml        # Alert rules (error spike, service down)
│   └── grafana-contact-points.yml # Telegram + Gmail routing
├── docker-compose.yml            # Production: 9 services
├── docker-compose.local.yml      # Local override: skips SSL + Loki driver
├── .env.docker.example           # Environment template — copy and fill in
└── DEPLOYMENT.md                 # Full deployment guide (local + Oracle Cloud)
```

---

## Running Locally (Docker)

The fastest way to run the full stack on your machine — no domain or SSL required.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose plugin
- API keys: Gemini and Cohere (minimum)

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/RAG-ChatBot.git
cd RAG-ChatBot

cp .env.docker.example .env.docker
# Edit .env.docker — fill in GEMINI_API_KEY, COHERE_API_KEY at minimum
```

### 2. Start the stack

```bash
docker compose --env-file .env.docker -f docker-compose.yml -f docker-compose.local.yml up --build -d
```

> **`--env-file .env.docker` is required.** Without it, Docker Compose can't interpolate
> variables like `${GRAFANA_ADMIN_PASSWORD}` and `${QDRANT_API_KEY}` in the compose file itself
> (not just inside containers), causing Grafana and Qdrant to start with blank credentials.

> **First-start note:** The backend downloads the SPLADE sparse embedding model (~110 MB)
> from HuggingFace on first launch. Expect 1–2 minutes before the API becomes responsive.
> Run `docker compose logs -f backend` to watch progress.

### 3. Open the app

| Service | URL | Login |
|---|---|---|
| **Application** | http://localhost | — |
| **API Health** | http://localhost/api/v1/health | — |
| **Grafana** | http://localhost:3001 | `admin` / value of `GRAFANA_ADMIN_PASSWORD` in `.env.docker` |
| **Prometheus** | http://localhost:9090 | — |

---

## Running Locally (Development Mode)

For active backend or frontend development with hot reload.

### Backend

```bash
cd src
uv sync                         # install dependencies into .venv
cp .env.example .env            # configure your keys
uv run uvicorn main:app --reload
```

API available at `http://localhost:8000` — interactive docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:3000`.

> In development mode the frontend calls the backend directly at `localhost:8000`.
> In Docker mode it routes through nginx at `/api/v1`.

---

## Deploying to Production

Full deployment guide with Oracle Cloud, DuckDNS, SSL, and Loki plugin setup:

👉 See **[DEPLOYMENT.md](./DEPLOYMENT.md)**

---

## API Overview

The backend exposes a versioned REST API at `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | App info and DB connection status |
| `GET` | `/health` | Health check for container orchestration |
| `POST` | `/data/upload/{project_id}` | Upload a document to a workspace |
| `GET` | `/data/files/{project_id}` | List files in a workspace |
| `DELETE` | `/data/{project_id}` | Delete a workspace and all its data |
| `GET` | `/nlp/ask/stream/{project_id}` | SSE streaming chat endpoint |
| `GET` | `/nlp/history/{project_id}` | Retrieve persistent chat history |
| `DELETE` | `/nlp/history/{project_id}/last` | Delete last message pair |
| `GET` | `/documents/preview/{project_id}/{asset_id}` | Preview a document's content |
| `GET` | `/settings/profile` | Get active LLM/embedding configuration |
| `PUT` | `/settings/llm` | Hot-swap LLM provider at runtime |

Interactive API documentation: `http://localhost:8000/docs`

---

## Key Engineering Decisions

### Why SSE instead of WebSockets?
SSE is unidirectional (server → client), which is exactly the pattern for LLM streaming. It requires no handshake, works through nginx without special configuration (except `proxy_buffering off`), and reconnects automatically on drop. WebSockets would add unnecessary complexity for a one-way stream.

### Why Qdrant for vector storage?
Qdrant supports **hybrid search** (dense + sparse vectors in a single query) natively, which is critical for RAG accuracy. Pure semantic search misses exact keyword matches; pure keyword search misses semantic similarity. Qdrant handles both in one round trip.

### Why uv instead of pip/poetry?
`uv` resolves and installs the full dependency tree in seconds vs. minutes for pip. It also generates a `uv.lock` file for reproducible builds — the same packages install in Docker as in development, every time.

### Why Docling for document ingestion?
Docling preserves document structure (headings, tables, page boundaries) during extraction. This gives accurate `page_number` metadata per chunk, which is surfaced in citations. Simple PDF text extractors flatten all of this.

### Why loginless authentication?
The system uses a **session-based anonymous identity** — a UUID is generated on first visit, stored in `localStorage`, and injected into every HTTP request via an Axios interceptor as the `X-Session-ID` header. The backend uses this header to scope workspaces and data to the session owner, with no user accounts, no passwords, and no JWT infrastructure.

This was a deliberate tradeoff: a personal RAG tool optimised for zero-friction access doesn't need full auth. The design is still secure by isolation — sessions cannot access each other's data — and can be replaced with real auth later without touching the backend data model.

### Why a custom exception pipeline?
Rather than letting FastAPI's default error responses leak into the frontend, the project implements a typed, end-to-end error contract:

1. **`CustomAPIException`** — a structured exception carrying a `signal` enum (machine-readable), a `message` (user-facing), a `status_code`, and `dev_detail` (for logs).
2. **`custom_api_exception_handler`** — catches every `CustomAPIException` and formats it into a consistent JSON response, also attaching the `X-Request-ID` correlation ID so errors can be traced across frontend and backend logs.
3. **`global_exception_handler`** — a safety net that catches all other unhandled exceptions and returns the same structured format rather than an HTML 500 page.
4. **Axios response interceptor** (frontend) — reads the `signal` field from every error response and routes it to the global toast notification system — no per-component error handling needed.

The result: any exception thrown anywhere in the backend automatically surfaces as a human-readable toast in the UI, with a request ID the user can report.


## Observability

The stack runs a full three-layer monitoring pipeline:

- **Prometheus** scrapes `/metrics` from the FastAPI backend every 15 seconds — request count, latency histograms (P50/P95/P99), error rates, broken down by endpoint
- **Loki** collects structured JSON logs from the backend container via the Loki Docker logging driver *(production only — disabled locally)*
- **Grafana** auto-provisions both datasources and fires alerts to **Telegram** and **Gmail** when error rate spikes or the backend goes silent *(production only)*

---

## Grafana Dashboards

Grafana starts with datasources pre-configured but no dashboards — import them manually via the UI.

### How to Import (Local or Production)

1. Open Grafana → **http://localhost:3001** (local) or **https://your-domain:3001** (Oracle Cloud)
2. Log in: `admin` / your `GRAFANA_ADMIN_PASSWORD`
3. Go to **Dashboards → New → Import**
4. Enter the dashboard ID → **Load** → select the correct datasource → **Import**

---

### ✅ Works Locally + Production

| Dashboard | ID | Datasource | What you see |
|---|---|---|---|
| [FastAPI Observability](https://grafana.com/grafana/dashboards/16110) | `16110` | Prometheus | Request rate, latency P50/P95/P99, error rate, per-endpoint breakdown |
| [Prometheus Stats](https://grafana.com/grafana/dashboards/11074) | `11074` | Prometheus | Prometheus internals — scrape health, target status, memory usage |

> These work locally because Prometheus **is** running and scraping the backend's `/metrics`.
> Import these first — they'll have live data immediately after the backend starts.

---

### 🚀 Production Only (Oracle Cloud)

| Dashboard | ID | Datasource | What you see | Extra Requirement |
|---|---|---|---|---|
| [Loki Logs / App](https://grafana.com/grafana/dashboards/15141) | `15141` | Loki | Live backend log stream with label filtering | Loki Docker plugin on VM |
| [Node Exporter Full](https://grafana.com/grafana/dashboards/1860) | `1860` | Prometheus | VM CPU, RAM, disk I/O, network | Add `node-exporter` service |
| [Docker Containers](https://grafana.com/grafana/dashboards/11467) | `11467` | Prometheus | Per-container CPU/RAM/network stats | Add `cadvisor` service |

> **Loki dashboards** require the [Loki Docker logging plugin](https://grafana.com/docs/loki/latest/send-data/docker-driver/)
> installed on the Oracle VM. Without it, no logs flow to Loki and dashboards will be empty.
> See [DEPLOYMENT.md](./DEPLOYMENT.md) Step 3 for plugin installation.

---

### Adding Node Exporter (Oracle Cloud — VM-level metrics)

To enable dashboard `1860`, add to `docker-compose.yml`:

```yaml
node-exporter:
  image: prom/node-exporter:latest
  pid: host
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/rootfs:ro
  command:
    - '--path.procfs=/host/proc'
    - '--path.sysfs=/host/sys'
    - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
  networks:
    - observability
```

Add a scrape target to `config/prometheus.yml`:

```yaml
- job_name: node-exporter
  static_configs:
    - targets: ['node-exporter:9100']
```

> Not included by default — requires `pid: host` and access to host filesystem mounts,
> which only makes sense on a real Linux VM. Do not add it for local testing.

---

### Loki Log Explorer (Production — no dashboard ID needed)

Use **Grafana Explore** to query backend logs directly:

1. Click **Explore** (compass icon) → select **Loki** datasource
2. Useful queries:

```logql
{service="backend"}                              # all backend logs
{service="backend"} |= "ERROR"                  # errors only
{service="backend"} | json | level="ERROR"       # structured error filter
{service="backend"} | json | request_id="<id>"  # trace a specific request
```

> The `request_id` in the last query matches the ID shown in error toasts in the frontend UI —
> this creates a direct link from a user-reported error to the exact log line in the backend.

---

## License

MIT