
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

    return new_user


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
