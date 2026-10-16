
from fastapi import APIRouter, HTTPException
from app.models import Monster
from app.models import Monster, TeamCreate
from app.models import Monster, TeamCreate, EncounterCreate
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db
from app.db.db_models import MonsterDB
from app.db.db_models import MonsterDB, PlayerMonsterDB
from fastapi import APIRouter, HTTPException, Depends
from app.db.database import get_db
from app.db.db_models import MonsterDB, PlayerMonsterDB

router = APIRouter(
    prefix="/api/monsters",
    tags=["Monsters"],
)

monsters = [
    Monster(id=1, name="Flameling", type="Fire", attack=80, defense=50),
    Monster(id=2, name="Aquaris", type="Water", attack=60, defense=80),
    Monster(id=3, name="Stonehorn", type="Earth", attack=70, defense=100),
    Monster(id=4, name="Shadowling", type="Shadow", attack=90, defense=60),
]


@router.get("/", response_model=list[Monster])
def get_monsters(db: Session = Depends(get_db)):
    return db.scalars(
        select(MonsterDB).order_by(MonsterDB.id)
    ).all()


@router.get("/{monster_id}", response_model=Monster)
def get_monster(monster_id: int,
    db: Session = Depends(get_db),
):
    monster = db.get(MonsterDB, monster_id)

    if monster is None:
        raise HTTPException(
            status_code=404,
            detail="Monster not found",
        )

    return monster



# Temporary collection for our first player
player_collection = [1, 2, 3]


@router.get("/collection/{player_id}")
def get_player_collection(player_id: int,
    db: Session = Depends(get_db),
):
    statement = (
        select(MonsterDB)
        .join(
            PlayerMonsterDB,
            MonsterDB.id == PlayerMonsterDB.monster_id,
        )
        .where(PlayerMonsterDB.player_id == player_id)
        .order_by(MonsterDB.id)
    )

    return db.scalars(statement).all()



# Temporary saved teams
encounter_history = []
player_teams = {}


@router.post("/teams/{player_id}")
def create_team(player_id: int, team: TeamCreate):
    # Check that the player owns every selected monster
    for monster_id in team.monster_ids:
        if monster_id not in player_collection:
            raise HTTPException(
                status_code=400,
                detail=f"Player does not own monster {monster_id}",
            )

    # Find the selected monsters
    selected_monsters = [
        monster
        for monster in monsters
        if monster.id in team.monster_ids
    ]

    # Calculate team power
    team_power = sum(
        monster.attack + monster.defense
        for monster in selected_monsters
    )

    # Save the team temporarily
    player_teams[player_id] = team.monster_ids

    return {
        "player_id": player_id,
        "monster_ids": team.monster_ids,
        "team_power": team_power,
    }


@router.post("/encounters")
def create_encounter(
    encounter: EncounterCreate,
    db: Session = Depends(get_db),
):
    # Validate that the wild monster exists
    wild_monster = next(
        (m for m in monsters if m.id == encounter.wild_monster_id),
        None,
    )

    if wild_monster is None:
        raise HTTPException(
            status_code=404,
            detail="Wild monster not found",
        )

    # Validate that the player owns every selected monster
    for monster_id in encounter.monster_ids:
        if monster_id not in player_collection:
            raise HTTPException(
                status_code=400,
                detail=f"Player does not own monster {monster_id}",
            )

    # Calculate team power
    selected_monsters = [
        m for m in monsters
        if m.id in encounter.monster_ids
    ]

    team_power = sum(
        m.attack + m.defense
        for m in selected_monsters
    )

    # Resolve the encounter
    outcome = (
        "SUCCESS"
        if team_power >= encounter.difficulty
        else "FAILURE"

        
    )


    # Award the wild monster after a successful encounter
   
    # Award the wild monster after a successful encounter
    if outcome == "SUCCESS":
        owned_monster = db.get(
            PlayerMonsterDB,
            (encounter.player_id, encounter.wild_monster_id),
        )

        if owned_monster is None:
            db.add(
                PlayerMonsterDB(
                    player_id=encounter.player_id,
                    monster_id=encounter.wild_monster_id,
                )
            )
            db.commit()


    # Record the resolved encounter
    record = {
        "player_id": encounter.player_id,
        "team_power": team_power,
        "difficulty": encounter.difficulty,
        "wild_monster_id": encounter.wild_monster_id,
        "outcome": outcome,
    }

    encounter_history.append(record)
    


    

    return {
        "player_id": encounter.player_id,
        "team_power": team_power,
        "difficulty": encounter.difficulty,
        "wild_monster": wild_monster,
        "outcome": outcome,
    }



@router.get("/encounters/history/{player_id}")
def get_encounter_history(player_id: int):
    return [
        record
        for record in encounter_history
        if record["player_id"] == player_id
    ]
