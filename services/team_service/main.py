
import os

import httpx
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.team_service.database import Base, engine, get_db
from services.team_service import models
from services.team_service.schemas import TeamCreate, TeamResponse

app = FastAPI(
    title="Monster Tamers - Team Service",
    description="Manages player teams and calculates team power.",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

MONSTER_SERVICE_URL = os.getenv(
    "MONSTER_SERVICE_URL",
    "http://localhost:8002",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "team-service",
    }


@app.post("/players/{player_id}/teams", response_model=TeamResponse, status_code=201)
def create_team(
    player_id: int,
    team: TeamCreate,
    db: Session = Depends(get_db),
):
    if player_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid player ID")

    # Retrieve the player's collection from Monster Service.
    try:
        collection_response = httpx.get(
            f"{MONSTER_SERVICE_URL}/players/{player_id}/collection",
            timeout=5.0,
        )
        collection_response.raise_for_status()
        collection = collection_response.json()

        selected_monsters = []

        for monster_id in team.monster_ids:
            if not any(
                monster["id"] == monster_id for monster in collection
            ):
                raise HTTPException(
                    status_code=403,
                    detail=f"Player does not own monster {monster_id}",
                )

            monster_response = httpx.get(
                f"{MONSTER_SERVICE_URL}/monsters/{monster_id}",
                timeout=5.0,
            )
            monster_response.raise_for_status()
            selected_monsters.append(monster_response.json())

    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="Monster Service is currently unavailable",
        )

    # Calculate team power using the original project formula.
    team_power = sum(
        monster["attack"] + monster["defense"]
        for monster in selected_monsters
    )

    new_team = models.TeamDB(
        player_id=player_id,
        team_power=team_power,
    )

    db.add(new_team)
    db.flush()

    for monster_id in team.monster_ids:
        db.add(
            models.TeamMonsterDB(
                team_id=new_team.id,
                monster_id=monster_id,
            )
        )

    db.commit()
    db.refresh(new_team)

    return TeamResponse(
        id=new_team.id,
        player_id=new_team.player_id,
        monster_ids=team.monster_ids,
        team_power=new_team.team_power,
    )


@app.get("/players/{player_id}/teams", response_model=list[TeamResponse])
def get_player_teams(
    player_id: int,
    db: Session = Depends(get_db),
):
    teams = db.scalars(
        select(models.TeamDB)
        .where(models.TeamDB.player_id == player_id)
        .order_by(models.TeamDB.id)
    ).all()

    results = []

    for team in teams:
        monster_ids = db.scalars(
            select(models.TeamMonsterDB.monster_id)
            .where(models.TeamMonsterDB.team_id == team.id)
            .order_by(models.TeamMonsterDB.monster_id)
        ).all()

        results.append(
            TeamResponse(
                id=team.id,
                player_id=team.player_id,
                monster_ids=list(monster_ids),
                team_power=team.team_power,
            )
        )

    return results
