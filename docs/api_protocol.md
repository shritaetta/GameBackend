# GamePulse API Protocol

**Version:** 1.0
**Transport:** HTTP/1.1 (JSON over TCP)
**Default port:** 8000
**Interactive docs:** `GET /docs` (Swagger UI), `GET /metrics` (Prometheus text format)

---

## Authentication

GamePulse uses **OAuth2 Password Flow + JWT bearer tokens** (`python-jose`,
HS256). Protected endpoints require:

```
Authorization: Bearer <access_token>
```

Tokens are obtained from `POST /auth/login` and expire per
`ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min, see `app/core/config.py`).

---

## Connection Lifecycle

```
Client                                Server
  │                                     │
  │──── POST /auth/register ──────────►│
  │◄─── 201 PlayerResponse ────────────│
  │                                     │
  │──── POST /auth/login (form) ──────►│
  │◄─── 200 {access_token, token_type}─│
  │                                     │
  │──── POST /matches  (Bearer) ──────►│
  │◄─── 201 MatchResponse ─────────────│
  │                                     │
  │──── POST /matches/{id}/join ──────►│
  │◄─── 200 MatchResponse ─────────────│
  │                                     │
  │──── POST /scores  (Bearer) ───────►│
  │◄─── 200 ScoreResponse ─────────────│
  │                                     │
  │──── GET /leaderboard ─────────────►│
  │◄─── 200 [LeaderboardEntry, ...] ──│
```

Unlike a persistent game socket, each request is an independent HTTP call
authenticated by the bearer token — there is no server-held session state
beyond what's cached in Redis (leaderboard, active-player count).

---

## Endpoints

### `POST /auth/register`
Create a new player account.

**Request:**
```json
{ "username": "player1", "email": "player1@example.com", "password": "s3cret" }
```
**Response `201`:**
```json
{ "id": 1, "username": "player1", "email": "player1@example.com",
  "created_at": "2026-08-29T12:00:00Z", "updated_at": null }
```
**Errors:** `400` — username or email already registered.

---

### `POST /auth/login`
OAuth2-compatible form login (`application/x-www-form-urlencoded`:
`username`, `password`).

**Response `200`:**
```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```
**Errors:** `401` — incorrect username or password.

---

### `GET /auth/players/me` (also `GET /players/me`)
Return the authenticated player's profile. **Requires Bearer token.**

**Response `200`:**
```json
{ "id": 1, "username": "player1", "email": "player1@example.com",
  "created_at": "2026-08-29T12:00:00Z", "updated_at": null }
```

---

### `POST /matches`
Create a new match. **Requires Bearer token.**

**Request:**
```json
{ "name": "Match_ab12cd" }
```
**Response `201`:**
```json
{ "id": 42, "name": "Match_ab12cd", "status": "WAITING",
  "created_at": "2026-08-29T12:00:00Z", "updated_at": null }
```

---

### `POST /matches/{match_id}/join`
Join an existing match. Idempotent — joining twice returns the same
membership row rather than erroring. **Requires Bearer token.**

**Response `200`:** `MatchResponse` (see above).
**Errors:** `404` — match not found.

---

### `POST /matches/{match_id}/leave`
Leave a match. **Requires Bearer token.**

**Response `200`:**
```json
{ "detail": "Left match" }
```
**Errors:** `400` — not joined in match.

---

### `POST /scores`
Increment the authenticated player's score for a match. Invalidates the
leaderboard cache. **Requires Bearer token.**

**Request:**
```json
{ "match_id": 42, "score": 100 }
```
**Response `200`:**
```json
{ "id": 7, "match_id": 42, "player_id": 1, "score": 100,
  "created_at": "2026-08-29T12:00:00Z", "updated_at": null }
```

---

### `GET /leaderboard`
Return the top players by total score across all matches. Served from a
60-second Redis cache; falls back transparently to MySQL on cache miss or
Redis outage.

**Response `200`:**
```json
[
  { "player_id": 1, "username": "player1", "total_score": 4500 },
  { "player_id": 2, "username": "player2", "total_score": 3200 }
]
```

---

### `GET /health`
Liveness/readiness probe — executes `SELECT 1` against MySQL.

**Response `200`:**
```json
{ "status": "ok", "database": "connected" }
```
**Response `503`:** database connection failed (message includes the
underlying exception).

---

### `GET /stats`
Active-player count, backed by the same cache-aside pattern as the
leaderboard.

**Response `200`:**
```json
{ "active_players": 128, "cache_status": "hit" }
```
`cache_status` is `"hit"` or `"miss"` — useful for debugging cache
effectiveness without needing the Prometheus counters.

---

### `GET /metrics`
Prometheus text-exposition format. Excluded from the request-tracking
middleware to avoid self-referential metrics noise.

---

## Error Response Shape

Validation errors (`422`) follow FastAPI's default shape:
```json
{ "detail": [ { "loc": ["body", "score"], "msg": "field required", "type": "value_error.missing" } ],
  "body": "..." }
```

Database errors are caught globally and normalized to:
```json
{ "detail": "Internal server error" }
```
with status `500`, so infrastructure failures never leak stack traces or
connection strings to the client.
