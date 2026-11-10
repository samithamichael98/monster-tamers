
import pytest
import httpx

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.encounter_service.main import app
from services.encounter_service.database import Base, get_db
import services.encounter_service.main as encounter_main


@pytest.fixture
def client(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    class FakeResponse:
        def __init__(self, data, status_code=200):
            self.data = data
            self.status_code = status_code

        def json(self):
            return self.data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError(
                    "Request failed",
                    request=httpx.Request("GET", "http://test"),
                    response=httpx.Response(
                        self.status_code,
                        request=httpx.Request("GET", "http://test"),
                    ),
                )

    def fake_get(url, timeout=5.0):

        if url.endswith("/monsters"):
            return FakeResponse([
                {"id": 1, "name": "Flameling", "type": "Fire", "attack": 95, "defense": 55},
                {"id": 2, "name": "Aquaris", "type": "Water", "attack": 65, "defense": 85},
                {"id": 3, "name": "Stonehorn", "type": "Earth", "attack": 55, "defense": 95},
                {"id": 4, "name": "Shadowling", "type": "Shadow", "attack": 100, "defense": 50},
                {"id": 5, "name": "Leafiris", "type": "Nature", "attack": 75, "defense": 75},
                {"id": 6, "name": "Voltstrike", "type": "Electric", "attack": 105, "defense": 45},
                {"id": 7, "name": "Frostcore", "type": "Ice", "attack": 70, "defense": 80},
                {"id": 8, "name": "Skyflare", "type": "Wind", "attack": 60, "defense": 90},
                {"id": 9, "name": "Magmalius", "type": "Lava", "attack": 90, "defense": 60},
                {"id": 10, "name": "Lumira", "type": "Light", "attack": 80, "defense": 70},
            ])
            
        if "/players/1/teams" in url:
            return FakeResponse([
                {
                    "id": 4,
                    "player_id": 1,
                    "monster_ids": [1, 2, 3],
                    "team_power": 440,
                },
                {
                    "id": 5,
                    "player_id": 1,
                    "monster_ids": [1],
                    "team_power": 150,
                },
            ])

        if "/monsters/4" in url or "/monsters/1" in url:
            return FakeResponse({"id": int(url.rsplit("/", 1)[-1])})

        return FakeResponse({}, status_code=404)

    def fake_post(url, json=None, timeout=5.0):
        return FakeResponse({"message": "Monster acquired successfully"}, 201)

    monkeypatch.setattr(encounter_main.httpx, "get", fake_get)
    monkeypatch.setattr(encounter_main.httpx, "post", fake_post)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_failed_encounter_default_difficulty(client):
    response = client.post(
        "/encounters",
        json={
            "player_id": 1,
            "team_id": 5,
            "wild_monster_id": 2,
        },
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "FAILURE"
    assert response.json()["team_power"] == 131
    assert response.json()["difficulty"] == 150


def test_successful_encounter_high_difficulty(client):
    response = client.post(
        "/encounters",
        json={
            "player_id": 1,
            "team_id": 4,
            "wild_monster_id": 1,
            "difficulty": 500,
        },
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "SUCCESS"
    assert response.json()["team_power"] == 479
    assert response.json()["difficulty"] == 450

def test_nonexistent_team(client):
    response = client.post(
        "/encounters",
        json={
            "player_id": 1,
            "team_id": 999,
            "wild_monster_id": 1,
        },
    )

    assert response.status_code == 404


def test_invalid_player_id(client):
    response = client.post(
        "/encounters",
        json={
            "player_id": 0,
            "team_id": 4,
            "wild_monster_id": 1,
        },
    )

    assert response.status_code == 422


def test_encounter_history(client):
    client.post(
        "/encounters",
        json={
            "player_id": 1,
            "team_id": 5,
            "wild_monster_id": 2,
        },
    )

    response = client.get("/players/1/encounters")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["outcome"] == "FAILURE"
    assert response.json()[0]["difficulty"] == 150


def test_get_available_encounters(client):
    response = client.get("/encounters/available")

    assert response.status_code == 200
    assert len(response.json()) == 10
    assert response.json()[0]["monster_name"] == "Flameling"
    assert response.json()[0]["difficulty"] == 150


def test_get_single_encounter(client):
    create_response = client.post(
        "/encounters",
        json={
            "player_id": 1,
            "team_id": 4,
            "wild_monster_id": 1,
            "difficulty": 100,
        },
    )

    encounter_id = create_response.json()["id"]

    response = client.get(f"/encounters/{encounter_id}")

    assert response.status_code == 200
    assert response.json()["id"] == encounter_id
    assert response.json()["player_id"] == 1


def test_get_nonexistent_encounter(client):
    response = client.get("/encounters/999")

    assert response.status_code == 404
