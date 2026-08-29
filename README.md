# GamePulse

GamePulse is a production-ready backend service built with FastAPI, SQLAlchemy, and MySQL 8. It supports player registration, authentication, match management, scoring, and leaderboards.

## Features

- **Player Management**: Register and login using JWT.
- **Matches**: Create, join, and leave matches.
- **Scoring**: Update player scores within a match.
- **Leaderboard**: View top players across all matches.
- **Event Tracking**: Internal tracking of game events (registration, login, matches, scores).
- **Structured Logging**: JSON-formatted logging for easy log aggregation.

## Requirements

- Docker
- Docker Compose

## Quick Start

1. **Clone and enter the directory**:
   ```bash
   cd GamePulse
   ```

2. **Start the application**:
   ```bash
   docker compose up --build
   ```
   This will start both the FastAPI backend and the MySQL database. The database will automatically initialize using the `schema.sql` file.

3. **Verify Health**:
   Visit [http://localhost:8000/health](http://localhost:8000/health) to ensure the service is up and connected to the database.

4. **Access the API Documentation**:
   Visit [http://localhost:8000/docs](http://localhost:8000/docs) to access the interactive Swagger UI.

## Testing

To run the smoke tests locally, you need a Python environment with `pytest` installed:
```bash
pip install -r requirements.txt
pytest tests/
```

*(Note: The smoke tests use an in-memory SQLite database, so a running MySQL instance is not strictly necessary to run them).*
