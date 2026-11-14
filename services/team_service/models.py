from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from services.team_service.database import Base


class TeamDB(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False)
    team_power: Mapped[int] = mapped_column(Integer, nullable=False)


class TeamMonsterDB(Base):
    __tablename__ = "team_monsters"

    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("teams.id"),
        primary_key=True,
    )

    # Monster IDs belong to the separate Monster Service database.
    monster_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )