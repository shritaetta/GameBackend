# 🎮 GamePulse — Resilient Multiplayer Game Backend

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=python&logoColor=white)](https://www.sqlalchemy.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-Dashboards-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Locust](https://img.shields.io/badge/Locust-Load_Testing-000000?style=for-the-badge&logo=python&logoColor=white)](https://locust.io/)

**A FastAPI backend for multiplayer game telemetry — players, matches, scoring, and a cached leaderboard — built with a fail-open Redis cache, chaos-tested MySQL resilience, and full Prometheus/Grafana observability.**

[Architecture](#-system-architecture) • [Benchmarks](#-load-test-results) • [Chaos Testing](#-chaos-engineering--resilience) • [Quickstart](#-quickstart-guide) • [Case Study](docs/portfolio_summary.md)

</div>

---

## 🚀 Key Highlights

| Metric | Result | Context |
|:---|---:|:---|
| **Leaderboard Read Latency (P50 / P95)** | **11 ms / 88 ms** | Highest-traffic endpoint (3,034 of 7,529 total requests in the load test run) |
| **Score Write Latency (P50)** | **36 ms** | DB write + audit event + cache invalidation |
| **Redis Outage Recovery** | **0.01 s** | Cache repopulates almost instantly after a Redis restart |
| **MySQL Outage Recovery** | **4.09 s** | `pool_pre_ping` reconnects automatically — no redeploy needed |
| **Fault Tolerance Under Load** | **0 Crashes** | Survived a live Redis kill/restart cycle *during* an active Locust run |
| **Automated Chaos Suite** | **5 / 5 PASS** | Redis failure, Redis recovery, MySQL failure, MySQL recovery, combined failure-under-load |

*(All figures sourced directly from `load_tests/stats_stats.csv` and `chaos_results/chaos_results.json` — see [`docs/portfolio_summary.md`](docs/portfolio_summary.md) for full methodology.)*

---

## 🏛 System Architecture

```
                                    CLIENT LAYER
                   ┌──────────────────────────────────────────────┐
                   │        Locust Load Generator (Bots)          │
                   │        REST clients / Swagger UI (/docs)     │
                   └──────────────────────┬───────────────────────┘
                                          │ HTTP/JSON (Bearer JWT)
                                          ▼
                               APPLICATION SERVER LAYER
                   ┌──────────────────────────────────────────────┐
                   │                FastAPI App (uvicorn)          │
                   │  ┌─────────────────────────────────────────┐  │
                   │  │  Metrics Middleware (per-request timer) │  │
                   │  └───────────────────┬─────────────────────┘  │
                   │                      ▼                        │
                   │  /auth  /matches  /scores  /leaderboard        │
                   │  /health  /stats  /players/me                 │
                   │                      │                        │
                   │  ┌───────────────────▼─────────────────────┐  │
                   │  │  Services → Repositories (SQLAlchemy)    │  │
                   │  └───────────────────┬─────────────────────┘  │
                   │           ┌──────────┼──────────┐              │
                   │           ▼          ▼          ▼              │
                   │       Redis      MySQL 8     /metrics          │
                   │      (cache)     (SoR)      (Prometheus)       │
                   └──────────────────────┬───────────────────────┘
                                          │
                   ┌──────────────────────┴───────────────────────┐
                   ▼                                              ▼
          IN-MEMORY CACHE (Redis)                     PERSISTENCE (MySQL 8)
 ┌────────────────────────────────────┐         ┌─────────────────────────────────┐
 │ • leaderboard (TTL 60s)            │         │ • players / matches              │
 │ • active_players (TTL 60s)         │         │ • match_players / scores         │
 │ • Fail-open on RedisError/ConnErr  │         │ • game_events (audit trail)      │
 └────────────────────────────────────┘         └─────────────────────────────────┘
```

Full breakdown, request-lifecycle sequence diagram, and component notes:
[`docs/architecture.md`](docs/architecture.md).

---

## ⚡ Quickstart Guide

### One-Command Docker Compose

```bash
# Launch backend, MySQL, Redis, Prometheus, Grafana & Locust
docker compose up --build
```

- **API**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Raw Metrics**: `http://localhost:8000/metrics`
- **Grafana Dashboard**: `http://localhost:3000` (`admin` / `admin`)
- **Prometheus UI**: `http://localhost:9090`
- **Locust UI**: `http://localhost:8089`

The MySQL container auto-initializes from `schema.sql` on first boot — no
manual migration step required.

### Running the Smoke Tests

```bash
pip install -r requirements.txt
pytest tests/
```

Smoke tests run against an in-memory SQLite database, so a live MySQL
instance is not required just to validate the API contract.

---

## 📊 Controlled Benchmark Experiments

| Experiment | Focus | Core Finding | Report Link |
|:---|:---|:---|:---|
| **Exp 1: Concurrency Ramp Sweep** | 5 → 50 simulated players | Throughput plateaus at **~12–15 req/s**, bounded by Locust think-time, not server saturation. | [Details](docs/Experiment%20Results/experiment_results.md#1-experiment-1-concurrency-ramp-sweep) |
| **Exp 2: Endpoint Latency Breakdown** | Per-endpoint P50/P95/P99 | Cached `GET /leaderboard` is both highest-traffic *and* fastest (**P50 = 11 ms**). | [Details](docs/Experiment%20Results/experiment_results.md#2-experiment-2-endpoint-level-latency-breakdown-steady-state) |
| **Exp 3: Chaos-Induced Outage Impact** | Latency during MySQL restart | Sharp P95→P99 knee; **99% of requests still complete under 5s** even including the outage. | [Details](docs/Experiment%20Results/experiment_results.md#3-experiment-3-chaos-induced-outage-impact) |
| **Exp 4: Locust Task-Mix Fidelity** | Configured vs. observed traffic shape | Observed request share tracks configured task weights to **within ~1 pt** on every task. | [Details](docs/Experiment%20Results/experiment_results.md#4-experiment-4-locust-task-mix-fidelity) |

---

## 📊 Load Test Results

Simulated with `load_tests/locustfile.py` (register → login → weighted task
mix: view leaderboard 40%, update score 30%, join match 15%, create match
10%, re-auth 5%):

| Endpoint | Requests | Failures | P50 | P95 |
|:---|---:|---:|---:|---:|
| `GET /leaderboard` | 3,034 | 272* | 11 ms | 88 ms |
| `POST /scores` | 2,138 | 197* | 36 ms | 190 ms |
| `POST /matches` | 789 | 78* | 31 ms | 160 ms |
| `POST /auth/login` | 434 | 25* | 600 ms | 1,200 ms |
| `POST /auth/register` | 50 | 0 | 310 ms | 1,300 ms |

\* *Failures concentrated in a deliberately injected MySQL outage window
during the chaos-under-load scenario — see below — not steady-state errors.*

Full CSV exports: [`load_tests/stats_stats.csv`](load_tests/stats_stats.csv),
[`stats_failures.csv`](load_tests/stats_failures.csv).

---

## 🛡️ Chaos Engineering & Resilience

`chaos_tests/chaos_test.py` stops and restarts the Redis and MySQL containers
mid-traffic and asserts the API stays available:

```
[Chaos Test 1] Redis container failure          ──► PASS (Leaderboard falls back to MySQL, no crash)
[Chaos Test 2] Redis container restart          ──► PASS (Cache repopulated in 0.01s)
[Chaos Test 3] MySQL container failure          ──► PASS (Controlled 500s, /metrics stays live)
[Chaos Test 4] MySQL container restart          ──► PASS (Reconnected automatically in 4.09s)
[Chaos Test 5] Redis failure during active load ──► PASS (Recovered in 0.69s under Locust traffic)
```

Full report: [`chaos_results/chaos_report.md`](chaos_results/chaos_report.md)
· [`chaos_results/chaos_results.json`](chaos_results/chaos_results.json).

Run it yourself:
```bash
docker compose up -d
python chaos_tests/chaos_test.py
```

---

## 📁 Repository Structure

```
├── app/                         # FastAPI application
│   ├── api/                     # Routers (auth, matches, scores, leaderboard, health, stats)
│   │   └── dependencies.py      # get_db, get_current_user (JWT)
│   ├── services/                # PlayerService, MatchService, ScoreService
│   ├── repositories/            # SQLAlchemy query layer (one file per entity)
│   ├── models/                  # ORM models (Player, Match, MatchPlayer, Score, GameEvent)
│   ├── schemas/                 # Pydantic request/response models
│   ├── core/                    # config, database, redis, security, logger, metrics
│   └── main.py                  # App factory, Prometheus middleware, exception handlers
├── schema.sql                   # MySQL 8 schema (auto-applied on container init)
├── tests/                       # Pytest smoke tests (in-memory SQLite)
├── load_tests/                  # Locust load test suite + exported CSV stats
├── chaos_tests/                 # Automated fault-injection & resilience runner
├── chaos_results/               # Generated chaos test reports (JSON + Markdown)
├── monitoring/                  # Grafana datasource + dashboard provisioning
├── prometheus.yml                # Prometheus scrape config
├── docker-compose.yml            # backend, mysql, redis, prometheus, grafana, locust
├── Dockerfile                    # Backend container build
├── docs/                         # Technical architecture & portfolio case studies
│   ├── architecture.md           # Component breakdown & request lifecycle
│   ├── database_design.md        # Schema, ERD, and indexing strategy
│   ├── caching_and_resilience.md # Cache-aside model & chaos test analysis
│   ├── api_protocol.md           # Full REST API reference
│   └── portfolio_summary.md      # Interview-ready case study
└── requirements.txt
```

---

## 📄 Documentation

- [`docs/architecture.md`](docs/architecture.md) — system topology, component breakdown, request lifecycle
- [`docs/database_design.md`](docs/database_design.md) — schema, ER diagram, indexing strategy
- [`docs/caching_and_resilience.md`](docs/caching_and_resilience.md) — cache-aside pattern & chaos test analysis
- [`docs/api_protocol.md`](docs/api_protocol.md) — full REST API reference with examples
- [`docs/portfolio_summary.md`](docs/portfolio_summary.md) — case study & interview talking points
