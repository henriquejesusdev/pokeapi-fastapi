from pydantic import BaseModel, ConfigDict


class PokemonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    name: str
    height: int
    weight: int
    types: str
