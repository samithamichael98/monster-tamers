from pydantic import BaseModel, Field, model_validator


class TeamCreate(BaseModel):
    monster_ids: list[int] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_unique_monsters(self):
        if len(self.monster_ids) != len(set(self.monster_ids)):
            raise ValueError("Duplicate monsters are not allowed")

        if any(monster_id <= 0 for monster_id in self.monster_ids):
            raise ValueError("Monster IDs must be positive")

        return self


class TeamResponse(BaseModel):
    id: int
    player_id: int
    monster_ids: list[int]
    team_power: int