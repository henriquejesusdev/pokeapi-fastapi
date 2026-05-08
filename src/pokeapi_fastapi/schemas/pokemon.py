from pydantic import BaseModel, ConfigDict, field_validator


class PokemonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, exclude_none=True)

    id: int
    external_id: int
    name: str
    height: int
    weight: int
    types: list[str]
    sprites: dict[str, str] | None = None

    @field_validator("types", mode="before")
    def parse_types(cls, types_value):
        if isinstance(types_value, str):
            return types_value.split(",") if types_value else []
        return types_value


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int
    next: str | None
    previous: str | None


class PokemonListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, exclude_none=True)

    data: list[PokemonResponse]
    pagination: Pagination
