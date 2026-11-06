
from datetime import datetime

from pydantic import BaseModel, Field


class EncounterCreate(BaseModel):
    player_id: int = Field(gt=0)
    team_id: int = Field(gt=0)
    wild_monster_id: int = Field(gt=0)
    difficulty: int = Field(gt=0)


class EncounterResponse(BaseModel):
    id: int
    player_id: int
    team_power: int
    difficulty: int
    wild_monster_id: int
    outcome: str
    created_at: datetime

    model_config = {"from_attributes": True}
