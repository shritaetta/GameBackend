# Chaos Testing Report

| Scenario | Start Time | End Time | Recovery (s) | Result | Details |
|----------|------------|----------|--------------|--------|---------|
| Redis container failure | 2026-08-29T18:10:21.699652 | 2026-08-29T18:10:34.964175 | N/A | PASS | Leaderboard fallback to MySQL successful. No crash. |
| Redis container restart | 2026-08-29T18:10:34.964175 | 2026-08-29T18:10:35.420297 | 0.01 | PASS | Redis successfully recovered and populated cache. |
| MySQL container failure | 2026-08-29T18:10:35.420297 | 2026-08-29T18:10:43.216863 | N/A | PASS | Controlled errors verified. Metrics active. |
| MySQL container restart | 2026-08-29T18:10:43.218145 | 2026-08-29T18:10:48.179069 | 4.09 | PASS | MySQL recovered and application reconnected successfully. |
| Redis failure during active load test | 2026-08-29T18:10:48.179702 | 2026-08-29T18:11:09.856104 | 0.69 | PASS | Survived Redis failure/recovery under active Locust load. |
