
from pydantic import BaseModel, Field


class Monster(BaseModel):
    id: int
    name: str
    type: str
    attack: int
    defense: int


from pydantic import BaseModel, Field, model_validator


class TeamCreate(BaseModel):
    monster_ids: list[int] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def check_unique_monsters(self):
        if len(self.monster_ids) != len(set(self.monster_ids)):
            raise ValueError("Duplicate monsters are not allowed")
        return self


class EncounterCreate(BaseModel):
    player_id: int
    monster_ids: list[int] = Field(min_length=1, max_length=3)
    wild_monster_id: int
    difficulty: int = Field(gt=0)


class EncounterCreate(BaseModel):
    player_id: int
    monster_ids: list[int] = Field(min_length=1, max_length=3)
    wild_monster_id: int
    difficulty: int = Field(gt=0)
