# Monster Tamers

Monster Tamers is a FastAPI project for managing monsters, player
collections, teams, and monster encounters. The application uses PostgreSQL
for monster and player-collection data and SQLAlchemy for database access.

## Features

- List all monsters
- Retrieve a monster by ID
- View a player's monster collection
- Create a team of up to three unique monsters
- Resolve monster encounters based on team power and difficulty
- Award a wild monster after a successful encounter
- View a player's encounter history
- Interactive OpenAPI documentation through FastAPI

## Technology stack

- Python 3.10 or newer
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Psycopg
- Pytest

## Project structure

```text
monster-tamers/
├── app/
│   ├── db/
│   │   ├── database.py       # SQLAlchemy engine and session dependency
│   │   └── db_models.py      # Database models
│   ├── routers/
│   │   └── monsters.py       # Monster API routes
│   └── models.py             # Pydantic request and response models
├── tests/
│   └── test_monsters.py      # API tests
├── docker-compose.yml        # PostgreSQL development service
├── check_db.py               # Database connectivity/query check
├── main.py                   # FastAPI application entry point
└── .gitignore
```

## Requirements

Before running the application, make sure the following are installed:

- Python 3.10+
- Docker Desktop or Docker Engine with Compose
- `pip`

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/samithamichael98/monster-tamers.git
cd monster-tamers
```

Create and activate a virtual environment:

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
python -m pip install fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" python-dotenv pytest httpx
```

## Database with Docker

The PostgreSQL database runs in Docker using
[`docker-compose.yml`](./docker-compose.yml). The Compose file creates:

- Database: `monster_tamers`
- User: `monster_user`
- Container: `monster-tamers-db`
- Host address: `127.0.0.1:5433`
- Container address: `db:5432` (only for other Docker services)

Create a local `.env.docker` file in the project root. Do not commit this file:

```dotenv
POSTGRES_PASSWORD=choose-a-local-password
```

Start the database:

```bash
docker compose --env-file .env.docker up -d db
```

Check that the container is running:

```bash
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs db
```

Stop the database without deleting its data:

```bash
docker compose --env-file .env.docker stop db
```

Stop the database and remove the container:

```bash
docker compose --env-file .env.docker down
```

The database data is stored in the named Docker volume
`monster_tamers_data`, so it remains available after the container stops.
To delete the database data permanently, run:

```bash
docker compose --env-file .env.docker down -v
```

### Application connection

When the FastAPI application runs directly on the host, connect through the
published port `5433`:

The application reads the database connection string from the
`DATABASE_URL` environment variable. If it is not set, it uses:

```text
postgresql+psycopg://samithamichael@localhost:5432/monster_tamers
```

For the Docker database, set `DATABASE_URL` to:

```bash
export DATABASE_URL="postgresql+psycopg://monster_user:<password>@127.0.0.1:5433/monster_tamers"
```

On Windows PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://monster_user:<password>@127.0.0.1:5433/monster_tamers"
```

The application loads `.env` automatically. You can alternatively store the
same `DATABASE_URL` value in a local `.env` file:

```dotenv
DATABASE_URL=postgresql+psycopg://monster_user:choose-a-local-password@127.0.0.1:5433/monster_tamers
```

Do not commit `.env`, `.env.docker`, or database passwords.

### Database schema and sample data

The current project does not run migrations or seed data automatically. After
starting the container, create the tables and sample data using the following
SQL:

```sql
CREATE TABLE monsters (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL
);

CREATE TABLE player_monsters (
    player_id INTEGER NOT NULL,
    monster_id INTEGER NOT NULL REFERENCES monsters(id),
    PRIMARY KEY (player_id, monster_id)
);

INSERT INTO monsters (id, name, type, attack, defense) VALUES
    (1, 'Flameling', 'Fire', 80, 50),
    (2, 'Aquaris', 'Water', 60, 80),
    (3, 'Stonehorn', 'Earth', 70, 100),
    (4, 'Shadowling', 'Shadow', 90, 60);

INSERT INTO player_monsters (player_id, monster_id) VALUES
    (1, 1),
    (1, 2),
    (1, 3);
```

You can run this SQL inside the running database container with:

```bash
docker exec -i monster-tamers-db \
  psql -U monster_user -d monster_tamers < seed.sql
```

Save the SQL above as `seed.sql` first, or run it through any PostgreSQL
client connected to `127.0.0.1:5433`.

If the sample data already exists, do not run the `INSERT` statements again.

You can check the database connection and list the stored monsters with:

```bash
python check_db.py
```

## Running the application

Start the database first:

```bash
docker compose --env-file .env.docker up -d db
```

Start the development server from the project root:

```bash
uvicorn main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## API endpoints

### Application endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Returns a welcome message |
| `GET` | `/health` | Returns the application health status |

### Monster endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/monsters/` | List all monsters |
| `GET` | `/api/monsters/{monster_id}` | Get one monster |
| `GET` | `/api/monsters/collection/{player_id}` | Get a player's collection |
| `POST` | `/api/monsters/teams/{player_id}` | Create a team |
| `POST` | `/api/monsters/encounters` | Resolve an encounter |
| `GET` | `/api/monsters/encounters/history/{player_id}` | Get encounter history |

### Example requests

Create a team:

```bash
curl -X POST http://127.0.0.1:8000/api/monsters/teams/1 \
  -H "Content-Type: application/json" \
  -d '{"monster_ids": [1, 2, 3]}'
```

Resolve an encounter:

```bash
curl -X POST http://127.0.0.1:8000/api/monsters/encounters \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 1,
    "monster_ids": [1, 2, 3],
    "wild_monster_id": 4,
    "difficulty": 400
  }'
```

## Testing

Start the Docker database before running the test suite:

```bash
docker compose --env-file .env.docker up -d db
python -m pytest -q
```

The tests use the configured database. Successful encounter tests add the wild
monster to the player's collection; the test fixture resets that test record
before each test.

## Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL | Docker connection on `127.0.0.1:5433` |

Do not commit passwords, API keys, or other secrets. Use local environment
variables or an untracked `.env` file for development configuration.
