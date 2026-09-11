# Database Architecture & Relational Storage Design

## 1. Dual-Tier Storage Strategy

Leaderboards and active-player counts are read far more often than they
change. GamePulse therefore implements a **cache-aside dual-tier** model:

```
                       APPLICATION DATA PATH
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       TIER 1: CACHE (Redis)              TIER 2: SYSTEM OF RECORD
        decode_responses=True                  (MySQL 8, InnoDB)
 ┌──────────────────────────────┐ ┌──────────────────────────────┐
 │ • leaderboard (TTL 60s)      │ │ • players / matches          │
 │ • active_players (TTL 60s)   │ │ • match_players / scores     │
 │ • Invalidated on every write │ │ • game_events (audit trail)  │
 │ • Fail-open on any RedisError│ │ • Source of truth, ACID      │
 └──────────────────────────────┘ └──────────────────────────────┘
```

Writes (`POST /scores`) invalidate the cache instead of updating it in place,
which trades a guaranteed-cold read on the next request for a much simpler
consistency model (no partial-cache-update bugs).

---

## 2. Relational Schema & Entity-Relationship Model

```
 ┌──────────────────────┐         ┌──────────────────────┐
 │       players        │         │       matches         │
 ├──────────────────────┤         ├──────────────────────┤
 │ id (PK, AUTO_INC)     │◄───┐    │ id (PK, AUTO_INC)     │◄──┐
 │ username (UNIQUE)     │    │    │ name (VARCHAR)        │   │
 │ email (UNIQUE)        │    │    │ status (WAITING/      │   │
 │ hashed_password       │    │    │   IN_PROGRESS/        │   │
 │ created_at/updated_at │    │    │   FINISHED)            │   │
 └──────────────────────┘    │    │ created_at/updated_at │   │
                             │    └──────────────────────┘   │
                             │                                │
              ┌──────────────┘──────────┐        ┌───────────┘
              ▼                         ▼        ▼
   ┌──────────────────────┐   ┌──────────────────────┐
   │    match_players      │   │        scores         │
   ├──────────────────────┤   ├──────────────────────┤
   │ match_id (PK, FK)     │   │ id (PK, AUTO_INC)     │
   │ player_id (PK, FK)    │   │ match_id (FK)         │
   │ joined_at             │   │ player_id (FK)        │
   │ ON DELETE CASCADE     │   │ score (INT)           │
   └──────────────────────┘   │ UNIQUE(match_id,       │
                               │        player_id)     │
                               │ ON DELETE CASCADE     │
                               └──────────────────────┘

                     ┌──────────────────────┐
                     │      game_events       │
                     ├──────────────────────┤
                     │ id (PK, AUTO_INC)     │
                     │ event_type (VARCHAR)  │
                     │ player_id (FK, NULL)  │
                     │ match_id  (FK, NULL)  │
                     │ details (JSON)        │
                     │ created_at            │
                     │ ON DELETE SET NULL    │
                     └──────────────────────┘
```

`match_players` uses a **composite primary key** `(match_id, player_id)` —
joining twice is a no-op rather than a duplicate row (`MatchRepository.join_match`
checks for an existing row before inserting).

`scores` carries a `UNIQUE(match_id, player_id)` constraint, so
`ScoreRepository.update_score` can safely do a select-then-increment without
risking duplicate score rows for the same player in the same match.

`game_events` uses `ON DELETE SET NULL` on both foreign keys deliberately —
it's an append-only audit log, and a deleted player or match should not
delete the historical record that they once existed.

---

## 3. Indexing & Query Optimization

| Table | Column(s) | Index Type | Purpose |
|:---|:---|:---|:---|
| `players` | `username`, `email` | UNIQUE B-Tree | Login lookup + registration uniqueness in O(log N). |
| `match_players` | `(match_id, player_id)` | Composite PK | Idempotent join/leave without extra existence queries. |
| `scores` | `id` (PK, implicit index) | B-Tree | Primary lookup surface. |
| `scores` | `(match_id, player_id)` | UNIQUE B-Tree (`match_player_score_unique`) | Enforces one score row per player per match; backs the leaderboard aggregation join. |
| `game_events` | `player_id`, `match_id` | FK indexes (implicit) | Fast per-player / per-match audit trail scans. |

### Leaderboard query
```python
self.db.query(Player.id, Player.username, func.sum(Score.score))
    .join(Score, Player.id == Score.player_id)
    .group_by(Player.id)
    .order_by(func.sum(Score.score).desc())
    .limit(limit)
```
This is the one query worth protecting with a cache — it's a full aggregate
over `scores` joined to `players`, and it's the highest-traffic endpoint in
the load test suite (see `portfolio_summary.md`).

---

## 4. Data Layer Discipline

- **Repositories, not active-record models.** Every SQL access path lives in
  `app/repositories/*.py`; models (`app/models/*.py`) only define columns and
  relationships. This keeps the ORM surface auditable file-by-file.
- **Commit boundaries live in services, not repositories.** Repositories call
  `flush()` (to obtain generated IDs) and let the owning `*Service` call
  `commit()` once per logical operation — e.g. `register()` commits after both
  the player insert and the audit event insert succeed together.
- **`pool_pre_ping=True`** on the SQLAlchemy engine so a MySQL restart (see
  chaos test results) is detected and the connection silently re-established
  rather than surfacing a stale-connection error to the client.
