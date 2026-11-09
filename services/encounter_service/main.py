
import os

import httpx
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from services.encounter_service.database import Base, engine, get_db
from services.encounter_service import models
from services.encounter_service.schemas import (EncounterCreate, EncounterResponse, AvailableEncounter)


app = FastAPI(
    title="Myth.exe - Encounter Service",
    description="Handles monster encounters, battle outcomes and encounter history.",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

TEAM_SERVICE_URL = os.getenv(
    "TEAM_SERVICE_URL",
    "http://localhost:8003"
)

MONSTER_SERVICE_URL = os.getenv(
    "MONSTER_SERVICE_URL",
    "http://localhost:8002"
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "encounter-service"
    }


@app.post("/encounters", response_model=EncounterResponse, status_code=201)
def create_encounter(
    request: EncounterCreate,
    db: Session = Depends(get_db)
):
    try:
        # Retrieve the player's saved teams
        team_response = httpx.get(
            f"{TEAM_SERVICE_URL}/players/{request.player_id}/teams",
            timeout=5.0
        )
        team_response.raise_for_status()

        teams = team_response.json()

        selected_team = next(
            (team for team in teams if team["id"] == request.team_id),
            None
        )

        if selected_team is None:
            raise HTTPException(
                status_code=404,
                detail="Team not found for this player"
            )

        # Validate the wild monster
        monster_response = httpx.get(
            f"{MONSTER_SERVICE_URL}/monsters/{request.wild_monster_id}",
            timeout=5.0
        )
        monster_response.raise_for_status()

        # Calculate the battle result
        team_power = selected_team["team_power"]

        outcome = (
            "SUCCESS"
            if team_power >= request.difficulty
            else "FAILURE"
        )

        # Save the encounter
        encounter = models.EncounterDB(
            player_id=request.player_id,
            team_power=team_power,
            difficulty=request.difficulty,
            wild_monster_id=request.wild_monster_id,
            outcome=outcome
        )

        db.add(encounter)
        db.commit()
        db.refresh(encounter)

        # Award the wild monster only after a successful encounter
        if outcome == "SUCCESS":
            try:
                award_response = httpx.post(
                    f"{MONSTER_SERVICE_URL}/players/{request.player_id}/collection",
                    json={"monster_id": request.wild_monster_id},
                    timeout=5.0
                )

                if award_response.status_code not in (201, 409):
                    award_response.raise_for_status()

            except httpx.HTTPError:
                raise HTTPException(
                    status_code=503,
                    detail="Encounter saved, but monster reward could not be processed"
                )

        return encounter

    except HTTPException:
        raise

    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="Another service is currently unavailable"
        )


@app.get(
    "/players/{player_id}/encounters",
    response_model=list[EncounterResponse]
)
def get_encounter_history(
    player_id: int,
    db: Session = Depends(get_db)
):
    if player_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid player ID"
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

@app.get("/encounters/{encounter_id}", response_model=EncounterResponse)
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
