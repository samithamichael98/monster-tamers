
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from services.team_service.main import app
from services.team_service.database import Base, get_db
import services.team_service.main as team_main


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

    def fake_get(url, timeout=5.0):
        if url.endswith("/players/1/collection"):
            return FakeResponse([
                {"id": 1, "attack": 80, "defense": 50},
                {"id": 2, "attack": 60, "defense": 80},
                {"id": 3, "attack": 70, "defense": 100},
            ])

        if url.endswith("/monsters/1"):
            return FakeResponse({"id": 1, "attack": 80, "defense": 50})

        if url.endswith("/monsters/2"):
            return FakeResponse({"id": 2, "attack": 60, "defense": 80})

        if url.endswith("/monsters/3"):
            return FakeResponse({"id": 3, "attack": 70, "defense": 100})

        return FakeResponse({}, status_code=404)

    class FakeResponse:
        def __init__(self, data, status_code=200):
            self.data = data
            self.status_code = status_code

        def json(self):
            return self.data

        def raise_for_status(self):
            if self.status_code >= 400:
                import httpx
                raise httpx.HTTPStatusError(
                    "Request failed",
                    request=httpx.Request("GET", "http://testserver"),
                    response=httpx.Response(
                        self.status_code,
                        request=httpx.Request("GET", "http://testserver"),
                    ),
                )

    monkeypatch.setattr(team_main.httpx, "get", fake_get)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_valid_team(client):
    response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 2, 3]},
    )
    assert response.status_code == 201
    assert response.json()["team_power"] == 440


def test_create_team_with_unowned_monster(client):
    response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 4]},
    )
    assert response.status_code == 403


def test_create_team_with_duplicate_monsters(client):
    response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 1]},
    )
    assert response.status_code == 422


def test_create_team_with_more_than_three_monsters(client):
    response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 2, 3, 4]},
    )
    assert response.status_code == 422


def test_create_team_with_empty_monster_list(client):
    response = client.post(
        "/players/1/teams",
        json={"monster_ids": []},
    )
    assert response.status_code == 422


def test_create_team_with_invalid_player_id(client):
    response = client.post(
        "/players/0/teams",
        json={"monster_ids": [1]},
    )
    assert response.status_code == 400


def test_get_player_teams(client):
    client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 2, 3]},
    )

    response = client.get("/players/1/teams")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["team_power"] == 440


def test_replace_monster_in_team(client):
    create_response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 2]},
    )
    team_id = create_response.json()["id"]

    response = client.put(
        f"/players/1/teams/{team_id}/replace",
        json={
            "old_monster_id": 1,
            "new_monster_id": 3,
        },
    )

    assert response.status_code == 200
    assert set(response.json()["monster_ids"]) == {2, 3}
    assert response.json()["team_power"] == 310


def test_replace_with_monster_already_in_team(client):
    create_response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 2]},
    )
    team_id = create_response.json()["id"]

    response = client.put(
        f"/players/1/teams/{team_id}/replace",
        json={
            "old_monster_id": 1,
            "new_monster_id": 2,
        },
    )

    assert response.status_code == 409


def test_remove_monster_from_team(client):
    create_response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1, 2]},
    )
    team_id = create_response.json()["id"]

    response = client.delete(
        f"/players/1/teams/{team_id}/monsters/1"
    )

    assert response.status_code == 200

    teams_response = client.get("/players/1/teams")
    assert teams_response.json()[0]["monster_ids"] == [2]
    assert teams_response.json()[0]["team_power"] == 140


def test_cannot_remove_last_monster_from_team(client):
    create_response = client.post(
        "/players/1/teams",
        json={"monster_ids": [1]},
    )
    team_id = create_response.json()["id"]

    response = client.delete(
        f"/players/1/teams/{team_id}/monsters/1"
    )

    assert response.status_code == 400