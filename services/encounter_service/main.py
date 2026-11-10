
import os
import httpx

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.encounter_service.database import Base, engine, get_db
from services.encounter_service import models
from services.encounter_service.schemas import (
    EncounterCreate,
    EncounterResponse,
    AvailableEncounter,
)


app = FastAPI(
    title="Myth.exe - Encounter Service",
    description="Handles monster encounters, battle outcomes and encounter history.",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

TEAM_SERVICE_URL = os.getenv(
    "TEAM_SERVICE_URL",
    "http://localhost:8003",
)

MONSTER_SERVICE_URL = os.getenv(
    "MONSTER_SERVICE_URL",
    "http://localhost:8002",
)


# Elemental advantages and disadvantages.
ELEMENT_MATCHUPS = {
    "Fire": {"strong": "Earth", "weak": "Water"},
    "Water": {"strong": "Fire", "weak": "Earth"},
    "Earth": {"strong": "Water", "weak": "Fire"},
    "Shadow": {"strong": "Light", "weak": "Nature"},
    "Nature": {"strong": "Shadow", "weak": "Lava"},
    "Electric": {"strong": "Water", "weak": "Wind"},
    "Ice": {"strong": "Wind", "weak": "Light"},
    "Wind": {"strong": "Electric", "weak": "Ice"},
    "Lava": {"strong": "Nature", "weak": "Electric"},
    "Light": {"strong": "Shadow", "weak": "Ice"},
}


def round_stat(value):
    """Round positive stat values to the nearest integer."""
    return int(value + 0.5)


def calculate_team_power(team_monsters, wild_monster):
    """
    Calculate adjusted team power using elemental matchups
    and automatic special abilities.
    """

    wild_type = wild_monster["type"]
    total_team_power = 0
    team_bonus_percent = 0

    for monster in team_monsters:
        monster_type = monster["type"]

        attack = monster["attack"]
        defense = monster["defense"]

        attack_bonus = 0
        defense_bonus = 0

        matchup = ELEMENT_MATCHUPS.get(monster_type, {})

        # Elemental advantage and disadvantage.
        if matchup.get("strong") == wild_type:
            attack_bonus += 20

        elif matchup.get("weak") == wild_type:
            # Shadowling ignores elemental disadvantages.
            if monster_type != "Shadow":
                attack_bonus -= 20

        # Automatic special abilities.
        if monster_type == "Fire" and wild_type == "Earth":
            attack_bonus += 15

        elif monster_type == "Water":
            defense_bonus += 15

        elif monster_type == "Earth":
            defense_bonus += 15

        elif monster_type == "Nature":
            team_bonus_percent += 10

        elif monster_type == "Electric" and wild_type == "Water":
            attack_bonus += 15

        elif monster_type == "Ice" and wild_type == "Fire":
            defense_bonus += 15

        elif monster_type == "Wind" and wild_type == "Lava":
            attack_bonus += 10

        elif monster_type == "Lava" and wild_type == "Nature":
            attack_bonus += 15

        elif monster_type == "Light":
            team_bonus_percent += 10

        # Apply combined individual stat modifiers.
        adjusted_attack = round_stat(
            attack * (1 + attack_bonus / 100)
        )

        adjusted_defense = round_stat(
            defense * (1 + defense_bonus / 100)
        )

        total_team_power += adjusted_attack + adjusted_defense

    # Leafiris and Lumira bonuses stack additively.
    final_team_power = round_stat(
        total_team_power * (1 + team_bonus_percent / 100)
    )

    return final_team_power


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "encounter-service",
    }


@app.post(
    "/encounters",
    response_model=EncounterResponse,
    status_code=201,
)
def create_encounter(
    request: EncounterCreate,
    db: Session = Depends(get_db),
):
    try:
        # Retrieve the player's teams.
        team_response = httpx.get(
            f"{TEAM_SERVICE_URL}/players/{request.player_id}/teams",
            timeout=5.0,
        )
        team_response.raise_for_status()

        teams = team_response.json()

        selected_team = next(
            (
                team for team in teams
                if team["id"] == request.team_id
            ),
            None,
        )

        if selected_team is None:
            raise HTTPException(
                status_code=404,
                detail="Team not found for this player",
            )

        # Retrieve the monster catalogue.
        monster_response = httpx.get(
            f"{MONSTER_SERVICE_URL}/monsters",
            timeout=5.0,
        )
        monster_response.raise_for_status()

        monsters = monster_response.json()

        monster_catalogue = {
            monster["id"]: monster
            for monster in monsters
        }

        # Validate the wild monster.
        wild_monster = monster_catalogue.get(
            request.wild_monster_id
        )

        if wild_monster is None:
            raise HTTPException(
                status_code=404,
                detail="Wild monster not found",
            )

        # Retrieve the individual monsters in the selected team.
        team_monsters = []

        for monster_id in selected_team["monster_ids"]:
            monster = monster_catalogue.get(monster_id)

            if monster is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Team monster {monster_id} not found",
                )

            team_monsters.append(monster)

        if not team_monsters:
            raise HTTPException(
                status_code=400,
                detail="Team must contain at least one monster",
            )

        # Calculate difficulty from the wild monster's base stats.
        difficulty = (
            wild_monster["attack"] +
            wild_monster["defense"]
        )*len(team_monsters);  # Adjust difficulty based on team size.

        # Calculate the actual adjusted team power.
        team_power = calculate_team_power(
            team_monsters,
            wild_monster,
        )

        # Determine the battle result.
        outcome = (
            "SUCCESS"
            if team_power >= difficulty
            else "FAILURE"
        )

        # Save the encounter.
        encounter = models.EncounterDB(
            player_id=request.player_id,
            team_power=team_power,
            difficulty=difficulty,
            wild_monster_id=request.wild_monster_id,
            outcome=outcome,
        )

        db.add(encounter)
        db.commit()
        db.refresh(encounter)

        # Award the wild monster after a successful encounter.
        if outcome == "SUCCESS":
            try:
                award_response = httpx.post(
                    f"{MONSTER_SERVICE_URL}/players/{request.player_id}/collection",
                    json={
                        "monster_id": request.wild_monster_id
                    },
                    timeout=5.0,
                )

                if award_response.status_code not in (201, 409):
                    award_response.raise_for_status()

            except httpx.HTTPError:
                raise HTTPException(
                    status_code=503,
                    detail="Encounter saved, but monster reward could not be processed",
                )

        return encounter

    except HTTPException:
        raise

    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="Another service is currently unavailable",
        )


@app.get(
    "/players/{player_id}/encounters",
    response_model=list[EncounterResponse],
)
def get_encounter_history(
    player_id: int,
    db: Session = Depends(get_db),
):
    if player_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid player ID",
        )

    statement = (
        select(models.EncounterDB)
        .where(models.EncounterDB.player_id == player_id)
        .order_by(models.EncounterDB.id)
    )

    return db.scalars(statement).all()


@app.get(
    "/encounters/available",
    response_model=list[AvailableEncounter],
)
def get_available_encounters():
    try:
        response = httpx.get(
            f"{MONSTER_SERVICE_URL}/monsters",
            timeout=5.0,
        )
        response.raise_for_status()

        monsters = response.json()

        return [
            AvailableEncounter(
                wild_monster_id=monster["id"],
                monster_name=monster["name"],
                monster_type=monster["type"],
                difficulty=monster["attack"] + monster["defense"],
            )
            for monster in monsters
        ]

    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="Monster Service is currently unavailable",
        )


@app.get(
    "/encounters/{encounter_id}",
    response_model=EncounterResponse,
)
def get_encounter_details(
    encounter_id: int,
    db: Session = Depends(get_db),
):
    encounter = db.get(models.EncounterDB, encounter_id)

    if encounter is None:
        raise HTTPException(
            status_code=404,
            detail="Encounter not found",
        )

    return encounter
