
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.monster_service.main import app
from services.monster_service.database import Base, get_db


@pytest.fixture
def client():
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

    db = TestingSessionLocal()

    from services.monster_service import models

    monsters = [
        models.MonsterDB(
            id=1, name="Flameling", type="Fire",
            attack=80, defense=50
        ),
        models.MonsterDB(
            id=2, name="Aquaris", type="Water",
            attack=60, defense=80
        ),
        models.MonsterDB(
            id=3, name="Stonehorn", type="Earth",
            attack=70, defense=100
        ),
        models.MonsterDB(
            id=4, name="Shadowling", type="Shadow",
            attack=90, defense=60
        ),
    ]

    db.add_all(monsters)
    db.add_all([
        models.PlayerMonsterDB(player_id=1, monster_id=1),
        models.PlayerMonsterDB(player_id=1, monster_id=2),
        models.PlayerMonsterDB(player_id=1, monster_id=3),
    ])
    db.commit()
    db.close()

    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_all_monsters(client):
    response = client.get("/monsters")
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_get_single_monster(client):
    response = client.get("/monsters/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Flameling"


def test_get_unknown_monster(client):
    response = client.get("/monsters/999")
    assert response.status_code == 404


def test_get_player_collection(client):
    response = client.get("/players/1/collection")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_acquire_monster(client):
    response = client.post(
        "/players/1/collection",
        json={"monster_id": 4},
    )
    assert response.status_code == 201


def test_acquire_already_owned_monster(client):
    response = client.post(
        "/players/1/collection",
        json={"monster_id": 1},
    )
    assert response.status_code == 409


def test_acquire_unknown_monster(client):
    response = client.post(
        "/players/1/collection",
        json={"monster_id": 999},
    )
    assert response.status_code == 404


def test_acquire_invalid_monster_id(client):
    response = client.post(
        "/players/1/collection",
        json={"monster_id": -1},
    )
    assert response.status_code == 422



def test_assign_starter_collection(client):
    response = client.post("/players/2/starter-collection")

    assert response.status_code == 200

    monsters = response.json()
    assert [monster["id"] for monster in monsters] == [1, 2, 3]


def test_assign_starter_collection_is_idempotent(client):
    first_response = client.post("/players/1/starter-collection")
    second_response = client.post("/players/1/starter-collection")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert [m["id"] for m in first_response.json()] == [1, 2, 3]
    assert [m["id"] for m in second_response.json()] == [1, 2, 3]


def test_assign_starter_collection_invalid_player(client):
    response = client.post("/players/0/starter-collection")

    assert response.status_code == 400
