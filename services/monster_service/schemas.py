from pydantic import BaseModel, Field


class MonsterResponse(BaseModel):
    id: int
    name: str
    type: str
    attack: int
    defense: int
    image_url: str | None = None

    model_config = {"from_attributes": True}


class MonsterAcquire(BaseModel):
    monster_id: int = Field(gt=0)