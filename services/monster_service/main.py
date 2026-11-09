from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from services.monster_service.database import Base, engine, get_db
from services.monster_service import models
from services.monster_service.schemas import MonsterResponse, MonsterAcquire

app = FastAPI(
    title="Myth.exe - Monster Service",
    description="Manages the monster catalogue and player collections.",
    version="1.0.0",
)
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "monster-service",
    }


@app.get("/monsters", response_model=list[MonsterResponse])
def get_monsters(db: Session = Depends(get_db)):
    return db.scalars(
        select(models.MonsterDB).order_by(models.MonsterDB.id)
    ).all()


@app.get("/monsters/{monster_id}", response_model=MonsterResponse)
def get_monster(monster_id: int, db: Session = Depends(get_db)):
    monster = db.get(models.MonsterDB, monster_id)

    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")

    return monster


@app.get("/players/{player_id}/collection", response_model=list[MonsterResponse])
def get_player_collection(player_id: int, db: Session = Depends(get_db)):
    statement = (
        select(models.MonsterDB)
        .join(
            models.PlayerMonsterDB,
            models.MonsterDB.id == models.PlayerMonsterDB.monster_id,
        )
        .where(models.PlayerMonsterDB.player_id == player_id)
        .order_by(models.MonsterDB.id)
    )

    return db.scalars(statement).all()


@app.post(
    "/players/{player_id}/starter-collection",
    response_model=list[MonsterResponse],
)
def assign_starter_collection(
    player_id: int,
    db: Session = Depends(get_db),
):
    if player_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid player ID",
        )

    starter_monster_ids = [1, 2, 3]

    for monster_id in starter_monster_ids:
        monster = db.get(models.MonsterDB, monster_id)

        if monster is None:
            raise HTTPException(
                status_code=500,
                detail=f"Starter monster {monster_id} is missing",
            )

        existing = db.get(
            models.PlayerMonsterDB,
            (player_id, monster_id),
        )

        if existing is None:
            db.add(
                models.PlayerMonsterDB(
                    player_id=player_id,
                    monster_id=monster_id,
                )
            )

    db.commit()

    statement = (
        select(models.MonsterDB)
        .join(
            models.PlayerMonsterDB,
            models.MonsterDB.id == models.PlayerMonsterDB.monster_id,
        )
        .where(models.PlayerMonsterDB.player_id == player_id)
        .order_by(models.MonsterDB.id)
    )

    return db.scalars(statement).all()



@app.post("/players/{player_id}/collection", status_code=201)
def acquire_monster(
    player_id: int,
    request: MonsterAcquire,
    db: Session = Depends(get_db),
):
    monster = db.get(models.MonsterDB, request.monster_id)

    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")

    existing = db.get(
        models.PlayerMonsterDB,
        (player_id, request.monster_id),
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Player already owns this monster",
        )

    ownership = models.PlayerMonsterDB(
        player_id=player_id,
        monster_id=request.monster_id,
    )

    db.add(ownership)
    db.commit()

    return {
        "message": "Monster acquired successfully",
        "player_id": player_id,
        "monster": monster,
    }