
import pytest
from fastapi.testclient import TestClient

from main import app
from app.db.database import SessionLocal
from app.db.db_models import PlayerMonsterDB

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_awarded_monster():
    db = SessionLocal()
    try:
        awarded_monster = db.get(PlayerMonsterDB, (1, 4))
        if awarded_monster is not None:
            db.delete(awarded_monster)
            db.commit()
    finally:
        db.close()


def test_get_all_monsters():
    response = client.get("/api/monsters/")

    assert response.status_code == 200

    monsters = response.json()
    assert len(monsters) >= 4
    assert monsters[0]["name"] == "Flameling"


def test_get_single_monster():
    response = client.get("/api/monsters/1")

    assert response.status_code == 200
    assert response.json()["name"] == "Flameling"
    assert response.json()["attack"] == 80


def test_get_unknown_monster():
    response = client.get("/api/monsters/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Monster not found"



def test_get_player_collection():
    response = client.get("/api/monsters/collection/1")

    assert response.status_code == 200

    collection = response.json()
    assert len(collection) == 3

    names = [monster["name"] for monster in collection]
    assert "Flameling" in names
    assert "Aquaris" in names
    assert "Stonehorn" in names
    assert "Shadowling" not in names



def test_create_valid_team():
    response = client.post(
        "/api/monsters/teams/1",
        json={"monster_ids": [1, 2, 3]},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["player_id"] == 1
    assert data["monster_ids"] == [1, 2, 3]
    assert data["team_power"] == 440



def test_create_team_with_unowned_monster():
    response = client.post(
        "/api/monsters/teams/1",
        json={"monster_ids": [1, 4]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Player does not own monster 4"


def test_create_team_with_too_many_monsters():
    response = client.post(
        "/api/monsters/teams/1",
        json={"monster_ids": [1, 2, 3, 4]},
    )

    assert response.status_code == 422


def test_create_team_with_duplicate_monsters():
    response = client.post(
        "/api/monsters/teams/1",
        json={"monster_ids": [1, 1, 2]},
    )

    assert response.status_code == 422



def test_encounter_success():
    response = client.post(
        "/api/monsters/encounters",
        json={
            "player_id": 1,
            "monster_ids": [1, 2, 3],
            "wild_monster_id": 4,
            "difficulty": 400,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["team_power"] == 440
    assert data["outcome"] == "SUCCESS"




def test_encounter_failure():
    response = client.post(
        "/api/monsters/encounters",
        json={
            "player_id": 1,
            "monster_ids": [1, 2, 3],
            "wild_monster_id": 4,
            "difficulty": 500,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["team_power"] == 440
    assert data["outcome"] == "FAILURE"



def test_successful_encounter_awards_wild_monster():
    response = client.post(
        "/api/monsters/encounters",
        json={
            "player_id": 1,
            "monster_ids": [1, 2, 3],
            "wild_monster_id": 4,
            "difficulty": 400,
        },
    )

    assert response.status_code == 200
    assert response.json()["outcome"] == "SUCCESS"

    collection_response = client.get(
        "/api/monsters/collection/1"
    )

    owned_ids = [
        monster["id"]
        for monster in collection_response.json()
    ]
    assert 4 in owned_ids


def test_encounter_is_saved_in_history():
    response = client.post(
        "/api/monsters/encounters",
        json={
            "player_id": 1,
            "monster_ids": [1, 2, 3],
            "wild_monster_id": 4,
            "difficulty": 500,
        },
    )

    assert response.status_code == 200

    history_response = client.get(
        "/api/monsters/encounters/history/1"
    )

    assert history_response.status_code == 200
    history = history_response.json()
    assert any(
        record["wild_monster_id"] == 4
        and record["outcome"] == "FAILURE"
        for record in history
    )
