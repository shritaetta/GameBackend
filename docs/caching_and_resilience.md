# Caching Strategy & Fault-Resilience Model

## 1. Concurrency Model

GamePulse runs as a single **ASGI application (uvicorn)**. FastAPI's route
handlers here are synchronous `def` functions, so each request's blocking I/O
(SQLAlchemy queries, `redis-py` calls, bcrypt hashing) is dispatched by
Starlette to a worker in its internal thread pool, keeping the main event loop
free to accept new connections concurrently.

```
                  ┌───────────────────────────────┐
                  │   uvicorn ASGI Event Loop      │
                  └───────────────┬───────────────┘
                                  │ run_in_threadpool()
                                  ▼
                  ┌───────────────────────────────┐
                  │  Starlette Sync Thread Pool    │
                  └──────┬────────┬───────┬───────┘
                         │        │       │
          ┌──────────────┘        │       └──────────────┐
          ▼                       ▼                      ▼
┌──────────────────┐    ┌──────────────────┐   ┌──────────────────┐
│  Request 1        │    │  Request 2        │   │ Request N        │
│  (DB session +    │    │  (DB session +    │   │ (DB session +    │
│   Redis client)   │    │   Redis client)   │   │  Redis client)   │
└─────────┬────────┘    └────────┬─────────┘   └─────────┬────────┘
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 ▼
                 ┌───────────────────────────────┐
                 │ SQLAlchemy Connection Pool     │
                 │ Redis Client (thread-safe pool)│
                 └───────────────────────────────┘
```

Each request gets its **own** `Session` via `get_db()` (a FastAPI dependency
generator with `try/finally: db.close()`), so sessions are never shared across
threads or requests — the classic SQLAlchemy footgun is avoided by
construction.

---

## 2. Cache-Aside Pattern

| Concern | Implementation | Rationale |
|:---|:---|:---|
| **Read path** | `get_cache(key)` → on hit, return JSON-decoded value; on miss/error, fall through to MySQL and repopulate with `set_cache(key, value, ex=60)` | 60s TTL bounds staleness without needing active invalidation for reads. |
| **Write path** | `delete_cache("leaderboard")` after every score update | Correctness over cleverness — no risk of caching a half-updated aggregate. |
| **Failure mode** | Every Redis call is wrapped in `except (redis.exceptions.RedisError, ConnectionError)`, logged, and returns `None`/`False` | Redis is an accelerator, never a dependency — a dead cache degrades latency, not availability. |

---

## 3. Chaos-Tested Resilience

The failure-mode design above was verified with an automated chaos suite
(`chaos_tests/chaos_test.py`) that stops/restarts the `redis` and `mysql`
containers mid-traffic and asserts the API stays up.

| Scenario | Result | Recovery Time | Notes |
|:---|:---|---:|:---|
| Redis container failure | **PASS** | N/A | Leaderboard fell back to MySQL directly; no crash. |
| Redis container restart | **PASS** | 0.01 s | Cache repopulated on next read. |
| MySQL container failure | **PASS** | N/A | Protected endpoints returned controlled 500s via the `SQLAlchemyError` exception handler; `/metrics` stayed live throughout. |
| MySQL container restart | **PASS** | 4.09 s | `pool_pre_ping=True` detected the stale connection and reconnected automatically. |
| Redis failure *during* active Locust load | **PASS** | 0.69 s | Survived cache outage/recovery under concurrent traffic with no dropped requests. |

*(Source: `chaos_results/chaos_results.json`, run 2026-08-29.)*

---

## 4. Observed Behavior Under Combined Chaos + Load

The Locust run captured in `load_tests/stats_stats.csv` includes a deliberate
MySQL outage injected mid-test. The effect is visible directly in the tail
latency of in-flight requests, and is a useful illustration of the
fail-open design in practice:

- **`GET /leaderboard`** — 3,034 requests, 272 failures during the outage
  window; **P50 = 11 ms** and **P95 = 88 ms** in steady state, with the tail
  (P99.9+) dominated entirely by the outage window (`ConnectionRefusedError`)
  rather than by application logic.
- **`POST /scores`** — 2,138 requests, 197 failures during the same window;
  **P50 = 36 ms** in steady state.
- No request hung indefinitely and no worker thread deadlocked — every
  in-flight request either completed or failed fast with a standard
  connection-level error once the container came back up.

This is the expected shape for a system that fails open rather than fails
silent: steady-state latency stays low and predictable, and outage windows
show up as a clean spike rather than a slow leak.
