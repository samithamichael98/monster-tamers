
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.user_service.database import Base, engine, get_db
from services.user_service import models
from services.user_service.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
)
from services.user_service.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
)


import os
import httpx
MONSTER_SERVICE_URL = os.getenv(
    "MONSTER_SERVICE_URL",
    "http://localhost:8002",
)

TEAM_SERVICE_URL = os.getenv(
    "TEAM_SERVICE_URL",
    "http://localhost:8003",
)

ENCOUNTER_SERVICE_URL = os.getenv(
    "ENCOUNTER_SERVICE_URL",
    "http://localhost:8004",
)

STARTER_MONSTERS_ENDPOINT = (
    f"{MONSTER_SERVICE_URL}/players"
)

app = FastAPI(
    title="Monster Tamers - User Service",
    description="Handles player registration, login and authentication.",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "user-service"}


@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)


def register_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = (
        db.query(models.UserDB)
        .filter(
            (models.UserDB.username == user.username)
            | (models.UserDB.email == user.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    new_user = models.UserDB(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        response = httpx.post(
            f"{STARTER_MONSTERS_ENDPOINT}/{new_user.id}/starter-collection",
            timeout=5.0,
        )
        response.raise_for_status()

    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Account created, but starter monsters could not "
                "be assigned. Please contact support."
            ),
        )

    return new_user


@app.post("/me/starter-collection")
def retry_starter_collection(
    user_id: int = Depends(get_current_user_id),
):
    try:
        response = httpx.post(
            f"{STARTER_MONSTERS_ENDPOINT}/{user_id}/starter-collection",
            timeout=5.0,
        )
        response.raise_for_status()

        return {
            "message": "Starter collection assigned successfully",
            "player_id": user_id,
            "collection": response.json(),
        }

    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monster Service is currently unavailable. Please try again.",
        )


@app.post("/login", response_model=TokenResponse)
def login_user(user: UserLogin, db: Session = Depends(get_db)):

    existing_user = (
        db.query(models.UserDB)
        .filter(models.UserDB.username == user.username)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(existing_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/me", response_model=UserResponse)
def get_my_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    current_user = (
        db.query(models.UserDB)
        .filter(models.UserDB.id == user_id)
        .first()
    )

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return current_user

@app.get("/me/progress")
def get_my_progress(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    current_user = db.query(models.UserDB).filter(
        models.UserDB.id == user_id
    ).first()

    if current_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    try:
        collection_response = httpx.get(
            f"{MONSTER_SERVICE_URL}/players/{user_id}/collection",
            timeout=5.0,
        )
        collection_response.raise_for_status()

        teams_response = httpx.get(
            f"{TEAM_SERVICE_URL}/players/{user_id}/teams",
            timeout=5.0,
        )
        teams_response.raise_for_status()

        encounters_response = httpx.get(
            f"{ENCOUNTER_SERVICE_URL}/players/{user_id}/encounters",
            timeout=5.0,
        )
        encounters_response.raise_for_status()

        monsters_response = httpx.get(
            f"{MONSTER_SERVICE_URL}/monsters",
            timeout=5.0,
        )
        monsters_response.raise_for_status()

    except httpx.HTTPError:
        raise HTTPException(
            status_code=503,
            detail="A required service is currently unavailable",
        )

    monsters = monsters_response.json()
    encounters = encounters_response.json()

    defeated_monsters = {
        encounter["wild_monster_id"]
        for encounter in encounters
        if encounter["outcome"] == "SUCCESS"
    }

    completed = len(
        defeated_monsters.intersection(
            {monster["id"] for monster in monsters}
        )
    )

    return {
        "player": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
        "collection": collection_response.json(),
        "teams": teams_response.json(),
        "encounters": encounters,
        "progress": f"{completed}/{len(monsters)}",
    }