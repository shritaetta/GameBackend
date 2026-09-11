# GamePulse — Resilient Game Backend Platform
### Backend Engineering & Observability Case Study

---

## 1. Project Overview & Elevator Pitch

> *"I built GamePulse, a FastAPI + MySQL + Redis backend for multiplayer game
> telemetry — player accounts, matches, scoring, and a cached leaderboard —
> instrumented end-to-end with Prometheus/Grafana, load-tested with Locust,
> and validated with an automated chaos-testing suite that kills Redis and
> MySQL containers mid-traffic to prove the API degrades gracefully instead
> of falling over."*

---

## 2. Key Technical Metrics & Highlights

*(Figures pulled directly from `load_tests/stats_stats.csv` and
`chaos_results/chaos_results.json` for the 2026-08-29 test run.)*

| Metric | Achievement | Significance |
|:---|:---|:---|
| **Leaderboard read latency (P50 / P95)** | **11 ms / 88 ms** | The highest-traffic endpoint (3,034 requests in the run) stays cache-fast under load. |
| **Score write latency (P50)** | **36 ms** | Includes DB write + audit-event insert + cache invalidation, still sub-40ms median. |
| **Cache-outage recovery time** | **0.01 s** | Redis restart → leaderboard cache repopulated almost instantly. |
| **Database-outage recovery time** | **4.09 s** | MySQL restart → app reconnects automatically via `pool_pre_ping`, no redeploy needed. |
| **Fault resilience under load** | **Zero crash** | Survived a live Redis kill/restart cycle *during* an active Locust run with 0.69s recovery. |
| **Chaos suite result** | **5 / 5 scenarios PASS** | Redis failure, Redis recovery, MySQL failure, MySQL recovery, and combined failure-under-load — all automated, all green. |

---

## 3. Core Architectural Highlights

```
                          ┌───────────────────────────┐
                          │   Locust Load Generator    │
                          │   (virtual player bots)    │
                          └─────────────┬─────────────┘
                                        │ HTTP/JSON + Bearer JWT
                                        ▼
                          ┌───────────────────────────┐
                          │       FastAPI Backend      │
                          │ • Prometheus middleware    │
                          │ • Service/Repo layering    │
                          │ • Fail-open cache calls    │
                          └──────┬─────────────┬──────┘
                                 │             │
                     redis-py    │             │  SQLAlchemy
                     (pooled)    │             │  (pool_pre_ping)
                                 ▼             ▼
                          ┌────────────┐ ┌────────────┐
                          │Redis Cache │ │ MySQL 8.0  │
                          │(leaderboard│ │ (accounts, │
                          │ TTL 60s)   │ │  scores)   │
                          └────────────┘ └────────────┘
                                 ▲
                  Scrapes :8000/metrics
                          ┌──────┴─────────────┐
                          │ Prometheus/Grafana │
                          │ (5-panel dashboard)│
                          └────────────────────┘
```

### 1. Layered Service Architecture
- Clean separation of `routes → services → repositories → models`, so every
  SQL query and every cache access is in exactly one place and independently
  testable.
- JWT auth via OAuth2 password flow with bcrypt-hashed credentials — no
  plaintext passwords anywhere in the request/response cycle.

### 2. Cache-Aside Caching with a Fail-Open Guarantee
- Redis accelerates the `leaderboard` and `active_players` hot paths with a
  60-second TTL; every cache call is wrapped so a Redis outage degrades to a
  direct MySQL query rather than a 500.
- Structured `CACHE_HIT` / `CACHE_MISS` / `CACHE_INVALIDATED` JSON log events
  make cache effectiveness auditable from logs alone, independent of metrics.

### 3. Real-Time Observability
- Every request is timed and labeled by method/endpoint/status via a single
  ASGI middleware, exported as Prometheus counters and histograms.
- A provisioned Grafana dashboard (`monitoring/dashboards`) tracks requests/sec,
  latency (avg + P95), cache hit/miss rate, active players, and domain event
  counters (`matches_created`, `score_updates`) in one view.

### 4. Automated Chaos & Load Testing
- `chaos_tests/chaos_test.py` programmatically stops/starts Docker containers
  and asserts API behavior (200s, controlled 500s, recovery within timeout),
  producing a machine-readable report (`chaos_results.json`) and a
  human-readable Markdown report (`chaos_report.md`) on every run.
- `load_tests/locustfile.py` simulates realistic player behavior (weighted
  tasks: view leaderboard 40%, update score 30%, join match 15%, create match
  10%, re-auth 5%) and exports raw CSV stats per endpoint.

---

## 4. Interview Scenarios & Talking Points (STAR Method)

### Scenario A: *"Tell me about a backend project where reliability mattered."*
- **Situation**: A game telemetry API needs to stay available even when its
  cache or database has a transient outage — a crash or hang mid-match is a
  worse user experience than a slightly stale leaderboard.
- **Task**: Design a caching layer that never becomes a single point of
  failure, and prove it under real failure conditions rather than just in
  code review.
- **Action**: Wrapped every Redis call in explicit exception handling that
  falls back to MySQL and logs the miss; added `pool_pre_ping` so MySQL
  reconnects transparently after a restart; built an automated chaos suite
  that kills each dependency mid-traffic and asserts the API keeps responding.
- **Result**: All 5 chaos scenarios passed, with MySQL recovery in 4.09s and
  Redis recovery in 0.01–0.69s, including one run where Redis was killed and
  restarted *while Locust was actively generating load*.

### Scenario B: *"How do you decide what to cache and how to invalidate it?"*
- **Answer**: *"The leaderboard is a full aggregate join over the scores
  table, and it's the single most-requested endpoint in the load test —
  3,034 of 7,529 total requests. Rather than trying to keep a cached
  aggregate correct on every write, I invalidate it on every score update and
  let the next reader repopulate it with a 60-second TTL. That trades one
  guaranteed-cold read for a much simpler, harder-to-get-wrong consistency
  model."*

### Scenario C: *"How do you verify a system is actually resilient, not just
theoretically resilient?"*
- **Answer**: *"I don't trust a resilience claim I can't reproduce on demand.
  `chaos_test.py` stops the Redis and MySQL containers with `docker compose
  stop`, hits the live API, and asserts specific status codes and recovery
  windows — then does the same thing again while Locust is actively
  generating load. The results are written to `chaos_results.json` so they're
  diffable across runs, not just a one-time demo."*
