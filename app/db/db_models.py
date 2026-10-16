# Database models belong in this module.

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db
from app.db.database import Base


class MonsterDB(Base):
    __tablename__ = "monsters"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    attack: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    defense: Mapped[int] = mapped_column(
        Integer, nullable=False
    )



class PlayerMonsterDB(Base):
    __tablename__ = "player_monsters"

    player_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    monster_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("monsters.id"),
        primary_key=True,
    )
