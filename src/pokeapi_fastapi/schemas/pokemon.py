from pydantic import BaseModel, ConfigDict, Field, field_validator


class PokemonSprites(BaseModel):
    front_default: str | None = None
    back_default: str | None = None


class PokemonCreate(BaseModel):
    external_id: int = Field(ge=1)
    name: str = Field(min_length=1)
    height: int = Field(ge=0)
    weight: int = Field(ge=0)
    types: list[str] = Field(min_length=1)
    sprites: PokemonSprites | None = None

    @field_validator("name")
    def normalize_name(cls, name_value):
        normalized_name = name_value.strip().lower()
        if not normalized_name:
            raise ValueError("name must not be empty")
        return normalized_name

    @field_validator("types")
    def normalize_types(cls, types_value):
        normalized_types = [
            pokemon_type.strip().lower()
            for pokemon_type in types_value
            if pokemon_type.strip()
        ]
        if not normalized_types:
            raise ValueError("types must not be empty")
        return normalized_types


class PokemonUpdate(BaseModel):
    external_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1)
    height: int | None = Field(default=None, ge=0)
    weight: int | None = Field(default=None, ge=0)
    types: list[str] | None = Field(default=None, min_length=1)
    sprites: PokemonSprites | None = None

    @field_validator("name")
    def normalize_name(cls, name_value):
        normalized_name = name_value.strip().lower()
        if not normalized_name:
            raise ValueError("name must not be empty")
        return normalized_name

    @field_validator("types")
    def normalize_types(cls, types_value):
        if types_value is None:
            return types_value
        normalized_types = [
            pokemon_type.strip().lower()
            for pokemon_type in types_value
            if pokemon_type.strip()
        ]
        if not normalized_types:
            raise ValueError("types must not be empty")
        return normalized_types


class PokemonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, exclude_none=True)

    id: int
    external_id: int
    name: str
    height: int
    weight: int
    types: list[str]
    sprites: dict[str, str | None] | None = None

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
