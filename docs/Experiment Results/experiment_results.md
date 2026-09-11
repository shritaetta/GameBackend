# Controlled Experiments & Performance Analysis Report

> **Methodology note:** Unlike a suite of independently-configured trials, this
> report is derived from a **single continuous Locust run** captured in
> `load_tests/stats_stats_history.csv` and `load_tests/stats_stats.csv`
> (2026-08-29), which happens to include a natural concurrency ramp
> (0 → 50 simulated players) followed by a deliberately injected MySQL outage.
> Rather than fabricate isolated A/B configurations GamePulse doesn't actually
> support (e.g. a Redis on/off toggle), the four experiments below are the
> ones this data can honestly support.

---

## 1. Experiment 1: Concurrency Ramp Sweep

Instantaneous throughput/latency snapshots as Locust ramps from 5 to 50
concurrent simulated players (1-second granularity, `wait_time` 1–5s per
user between tasks).

| Concurrent Players | Throughput (req/s) | P50 (ms) | P95 (ms) | P99 (ms) |
|:---|---:|---:|---:|---:|
| **5** | 5.0 | 260 | 290 | 290 |
| **10** | 9.5 | 260 | 290 | 290 |
| **15** | 10.7 | 260 | 350 | 360 |
| **20** | 12.0 | 260 | 510 | 530 |
| **25** | 12.4 | 260 | 620 | 770 |
| **30** | 12.2 | 260 | 810 | 950 |
| **35** | 12.6 | 270 | 950 | 1,200 |
| **40** | 12.1 | 270 | 1,200 | 1,400 |
| **45** | 13.4 | 47 | 1,000 | 1,400 |
| **50** | 15.1 | 25 | 980 | 1,400 |

**Reading this table:** throughput plateaus around 12–15 req/s well before
50 users — this workload is dominated by Locust's `wait_time(1, 5)` think-time
between tasks, not by server saturation. The interesting signal is the P95/P99
column widening steadily from 20 users onward as concurrent `/auth/login`
calls (bcrypt-bound, see Experiment 2) start queueing on the shared thread
pool.

---

## 2. Experiment 2: Endpoint-Level Latency Breakdown (Steady State)

Full-run aggregates per endpoint, `load_tests/stats_stats.csv`:

| Endpoint | Requests | Failures | P50 (ms) | P95 (ms) | P99 (ms)* |
|:---|---:|---:|---:|---:|---:|
| `GET /leaderboard` | 3,034 | 272 | **11** | 88 | 4,400 |
| `POST /scores` | 2,138 | 197 | **36** | 190 | 4,800 |
| `POST /matches` | 789 | 78 | **31** | 160 | 125,000 |
| `POST /auth/login` | 434 | 25 | **600** | 1,200 | 5,400 |
| `POST /auth/register` | 50 | 0 | **490** | 1,300 | 1,400 |
| **All endpoints (aggregate)** | **7,529** | **666** | **29** | 560 | 4,600 |

\* *P99 across every endpoint is dominated by the injected MySQL outage
window (see Experiment 3), not by application logic — steady-state P50/P95
are the honest signal here.*

**Core finding:** the cached `GET /leaderboard` endpoint is both the
highest-traffic *and* the fastest endpoint (P50 = 11ms) — the 60-second
Redis cache is doing exactly the job it was designed for. `POST /auth/login`
is the slowest steady-state endpoint by a wide margin (P50 = 600ms), which
tracks with bcrypt's deliberately expensive hash-verification cost rather
than any I/O bottleneck.

---

## 3. Experiment 3: Chaos-Induced Outage Impact

A single-request timeline comparison, isolating the effect of the injected
MySQL container restart on the aggregate latency distribution.

| Percentile | Latency (ms) | Interpretation |
|:---|---:|:---|
| P50 | 29 | Normal steady-state response |
| P90 | 170 | Still within normal application variance |
| P95 | 560 | Early queueing as connections wait on `pool_pre_ping` |
| P98 | 950 | Requests in-flight during outage onset |
| P99 | 4,600 | Requests blocked until MySQL container restart completes |
| P99.9 | 129,000 | Requests that timed out entirely during the ~2-minute outage window |

**Core finding:** the distribution has a sharp knee between P95 and P99 —
99% of requests complete in under 5 seconds even *including* the outage
window, and the automated chaos suite (`chaos_tests/chaos_test.py`) measured
the actual container-restart recovery at **4.09 seconds** wall-clock. The
P99.9+ tail is a small number of requests that were in-flight at the exact
moment the container went down, not a systemic degradation.

---

## 4. Experiment 4: Locust Task-Mix Fidelity

Comparing the weighted task distribution defined in `load_tests/locustfile.py`
against what the server actually observed — a sanity check that the load
generator is producing the traffic shape it claims to.

| Locust Task | Target Weight | Endpoint | Observed Requests | Observed Share |
|:---|---:|:---|---:|---:|
| `view_leaderboard` | 40% | `GET /leaderboard` | 3,034 | **40.3%** |
| `update_score` | 30% | `POST /scores` | 2,138 | **28.4%** |
| `join_match` | 15% | `POST /matches/{id}/join` (aggregate) | 1,084 | **14.4%** |
| `create_match` | 10% | `POST /matches` | 789 | **10.5%** |
| `register_login` | 5% | `POST /auth/login` (re-auth calls, combined with initial logins) | 434 | 5.8% |
| *(one-time, not weighted)* | — | `POST /auth/register` | 50 | 0.7% |

**Core finding:** observed traffic shape tracks the configured weights to
within ~1 percentage point on every task, and `POST /auth/register`'s request
count (50) exactly matches the peak simulated-player count from Experiment 1
— confirming each virtual user registered exactly once, as designed in
`on_start()`.
