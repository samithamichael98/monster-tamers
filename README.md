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

## Database Setup (PostgreSQL + pgAdmin)

Monster Tamers uses a local PostgreSQL database. Docker is not required.

### 1. Install PostgreSQL

Install PostgreSQL on your computer using the official installer for your operating system:

- PostgreSQL downloads: https://www.postgresql.org/download/
- pgAdmin: https://www.pgadmin.org/download/

You can use pgAdmin to create and manage your database and view its tables.

### 2. Create the database

Open pgAdmin, connect to your local PostgreSQL server, right-click **Databases**, and select **Create → Database**.

Use this database name:

`monster_tamers`

Use your own PostgreSQL username and password. The default local PostgreSQL port is usually `5432`.

### 3. Configure the application

Create a `.env` file in the project root. Do not commit this file or share your database password.

Add your own connection details:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_USERNAME:YOUR_PASSWORD@127.0.0.1:5432/monster_tamers
```

Replace `YOUR_USERNAME` and `YOUR_PASSWORD` with your PostgreSQL credentials. If your password contains special characters, URL-encode them in the connection URL.

The application reads `DATABASE_URL` from `.env`. If it is not configured, the default connection URL in `app/db/database.py` is used.

### 4. Create the database tables

From the project root, with your virtual environment activated, run:

```bash
python init_db.py
```

This creates any missing SQLAlchemy tables defined by the application models. It does not automatically insert the sample monsters.

### 5. Add the sample monsters

In pgAdmin, open **Tools → Query Tool** for the `monster_tamers` database and run the following SQL if the sample monsters are not already present:

```sql
INSERT INTO monsters (id, name, type, attack, defense)
VALUES
    (1, 'Flameling', 'Fire', 80, 50),
    (2, 'Aquaris', 'Water', 60, 80),
    (3, 'Stonehorn', 'Earth', 70, 100),
    (4, 'Shadowling', 'Shadow', 90, 60)
ON CONFLICT (id) DO NOTHING;

INSERT INTO player_monsters (player_id, monster_id)
VALUES
    (1, 1),
    (1, 2),
    (1, 3)
ON CONFLICT (player_id, monster_id) DO NOTHING;
```

Run the sample-data SQL only after creating the tables. If your database already contains the sample data, you do not need to run it again.

### 6. Verify the database connection

Run:

```bash
python check_db.py
```

If the connection fails, verify that PostgreSQL is running, the database exists, and your `.env` connection details are correct.
```

Save the SQL above as `seed.sql` first, or run it through any PostgreSQL
client connected to `127.0.0.1:5433`.

If the sample data already exists, do not run the `INSERT` statements again.

You can check the database connection and list the stored monsters with:

```bash
python check_db.py
```

## Running the application

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
