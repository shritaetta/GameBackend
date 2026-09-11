from prometheus_client import Counter, Histogram, Gauge

# Request metrics
gamepulse_requests_total = Counter(
    "gamepulse_requests_total",
    "Total requests",
    ["method", "endpoint", "http_status"]
)

gamepulse_request_duration_seconds = Histogram(
    "gamepulse_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

# Domain metrics
gamepulse_active_players = Gauge(
    "gamepulse_active_players",
    "Number of currently active players"
)

gamepulse_matches_created_total = Counter(
    "gamepulse_matches_created_total",
    "Total matches created"
)

gamepulse_score_updates_total = Counter(
    "gamepulse_score_updates_total",
    "Total score updates"
)

# Cache metrics
gamepulse_cache_hits_total = Counter(
    "gamepulse_cache_hits_total",
    "Total Redis cache hits"
)

gamepulse_cache_misses_total = Counter(
    "gamepulse_cache_misses_total",
    "Total Redis cache misses"
)
