# Myth.exe

Myth.exe is a FastAPI microservices application for managing users,
monsters, teams, and monster encounters. Each service has its own PostgreSQL
database and runs in its own Docker container.

## Features

- User registration, login, and authenticated profiles
- Monster catalogue and player collections
- Teams containing up to three unique monsters
- Monster encounters based on team power and difficulty
- Encounter history
- Interactive OpenAPI documentation for every service

## Architecture

| Service | Container port | Host port | Responsibility |
| --- | ---: | ---: | --- |
| User service | 8001 | 8001 | Registration, login, and user profiles |
| Monster service | 8002 | 8002 | Monsters and player collections |
| Team service | 8003 | 8003 | Player teams |
| Encounter service | 8004 | 8004 | Encounters and encounter history |

Each service has a dedicated PostgreSQL database:

| Database | Host port | Database name | Database user |
| --- | ---: | --- | --- |
| User database | 5433 | `user_db` | `user_service` |
| Monster database | 5434 | `monster_db` | `monster_service` |
| Team database | 5435 | `team_db` | `team_service` |
| Encounter database | 5436 | `encounter_db` | `encounter_service` |

The team service communicates with the monster service. The encounter service
communicates with the team and monster services through the Docker network.

## Project structure

```text
monster-tamers/
├── services/
│   ├── user_service/
│   │   ├── Dockerfile
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── monster_service/
│   ├── team_service/
│   └── encounter_service/
├── tests/
│   ├── test_user_service.py
│   ├── test_monster_service.py
│   ├── test_team_service.py
│   └── test_encounter_service.py
├── docker-compose.yml
├── requirements.txt
├── init_db.py
└── .env
```

The `.env` file is local configuration and is ignored by Git. Do not commit
database passwords or JWT secrets.

## Requirements

Install the following before starting the project:

- Docker Desktop or Docker Engine with Docker Compose
- Git
- Python 3.13 or newer for local development and tests

## Docker setup

### 1. Clone the repository

```bash
git clone https://github.com/samithamichael98/monster-tamers.git
cd monster-tamers
```

### 2. Configure environment variables

Create `.env` in the project root. Use your existing local `.env` if you
already have one. Do not replace it with real credentials in this README.

The Compose file requires these variables:

```dotenv
POSTGRES_PASSWORD=your_postgres_password

USER_DB_PASSWORD=your_user_db_password
MONSTER_DB_PASSWORD=your_monster_db_password
TEAM_DB_PASSWORD=your_team_db_password
ENCOUNTER_DB_PASSWORD=your_encounter_db_password

JWT_SECRET_KEY=your_long_random_jwt_secret
```

The service-specific host and port values are supplied automatically by
Docker Compose. When running Python directly on the host, use `localhost` and
the published ports shown in the architecture table.

### 3. Build and start all services

```bash
docker compose up --build -d
```

This starts:

- Four PostgreSQL containers
- Four FastAPI service containers
- Persistent Docker volumes for the databases

Check container status:

```bash
docker compose ps
```

View all service logs:

```bash
docker compose logs -f
```

View one service's logs:

```bash
docker compose logs -f user-service
```

### 4. Check service health

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
curl http://127.0.0.1:8004/health
```

Each service should return a healthy status.

### 5. Open API documentation

FastAPI provides Swagger UI and ReDoc for each service:

| Service | Swagger UI | ReDoc |
| --- | --- | --- |
| User | <http://127.0.0.1:8001/docs> | <http://127.0.0.1:8001/redoc> |
| Monster | <http://127.0.0.1:8002/docs> | <http://127.0.0.1:8002/redoc> |
| Team | <http://127.0.0.1:8003/docs> | <http://127.0.0.1:8003/redoc> |
| Encounter | <http://127.0.0.1:8004/docs> | <http://127.0.0.1:8004/redoc> |

## API endpoints

### User service — port 8001

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check service health |
| `POST` | `/register` | Register a user |
| `POST` | `/login` | Authenticate a user |
| `GET` | `/me` | Get the authenticated user's profile |

### Monster service — port 8002

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check service health |
| `GET` | `/monsters` | List all monsters |
| `GET` | `/monsters/{monster_id}` | Get a monster |
| `GET` | `/players/{player_id}/collection` | Get a player's collection |
| `POST` | `/players/{player_id}/collection` | Add a monster to a collection |

### Team service — port 8003

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check service health |
| `POST` | `/players/{player_id}/teams` | Create a team |
| `GET` | `/players/{player_id}/teams` | List a player's teams |

### Encounter service — port 8004

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check service health |
| `POST` | `/encounters` | Resolve an encounter |
| `GET` | `/players/{player_id}/encounters` | Get encounter history |

## Example requests

Register a user:

```bash
curl -X POST http://127.0.0.1:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "SecurePass123!"
  }'
```

Log in:

```bash
curl -X POST http://127.0.0.1:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "SecurePass123!"
  }'
```

Create a team:

```bash
curl -X POST http://127.0.0.1:8003/players/1/teams \
  -H "Content-Type: application/json" \
  -d '{"monster_ids": [1, 2, 3]}'
```

Resolve an encounter:

```bash
curl -X POST http://127.0.0.1:8004/encounters \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 1,
    "team_id": 1,
    "wild_monster_id": 4,
    "difficulty": 400
  }'
```

## Running tests

The tests use in-memory SQLite databases for service data, but importing the
services requires the environment variables from `.env`. Activate the
virtual environment and run the test suite from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
```

Using the virtual environment is important. Running `pytest` with a different
system Python may fail with `ModuleNotFoundError` for FastAPI or other
dependencies.

## Stopping and resetting Docker

Stop containers while keeping database data:

```bash
docker compose down
```

Stop containers and permanently delete database volumes:

```bash
docker compose down -v
```

Only use `down -v` when you intentionally want to delete all local database
data.

## Troubleshooting

### Containers are not healthy

Check the service logs and status:

```bash
docker compose ps
docker compose logs --tail=100 user-db user-service
```

Make sure `.env` exists and contains all required variables.

### Password authentication failed

PostgreSQL stores credentials in its persistent volume. If the password in
`.env` was changed after a database volume was created, the existing database
may still use the old password. Restore the original value or intentionally
recreate the local database volumes:

```bash
docker compose down -v
docker compose up --build -d
```

### Port already in use

Stop the process using the port, or change the host-side port mapping in
`docker-compose.yml`. Do not change the container ports used for service-to-
service communication.
