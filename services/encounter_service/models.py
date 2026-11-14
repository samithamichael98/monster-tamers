
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from services.encounter_service.database import Base


class EncounterDB(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    team_power: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    difficulty: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    wild_monster_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
