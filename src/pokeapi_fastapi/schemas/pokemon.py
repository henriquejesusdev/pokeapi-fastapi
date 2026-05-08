from pydantic import BaseModel, ConfigDict


class PokemonCreate(BaseModel):
    name: str
    type: str


class PokemonUpdate(BaseModel):
    name: str | None = None
    type: str | None = None


class PokemonResponse(PokemonCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
