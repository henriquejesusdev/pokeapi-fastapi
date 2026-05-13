from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from pokeapi_fastapi.database.connection import get_db
from pokeapi_fastapi.database.models import Pokemon
from pokeapi_fastapi.schemas.pokemon import (
    PokemonCreate,
    PokemonListResponse,
    PokemonResponse,
    PokemonUpdate,
)
from pokeapi_fastapi.services.pokeapi import get_external_pokemon_data

router = APIRouter(prefix="/pokemons", tags=["Pokemons"])


def _pokemon_payload_to_model_data(pokemon_payload: PokemonCreate | PokemonUpdate):
    data = pokemon_payload.model_dump(exclude_unset=True)
    sprites = data.pop("sprites", None)

    if "types" in data:
        data["types"] = ",".join(data["types"])

    if sprites is not None:
        if "front_default" in sprites:
            data["front_default"] = sprites["front_default"]
        if "back_default" in sprites:
            data["back_default"] = sprites["back_default"]

    return data


def _raise_if_pokemon_conflicts(
    db: Session,
    *,
    external_id: int | None = None,
    name: str | None = None,
    pokemon_id: int | None = None,
):
    filters = []

    if external_id is not None:
        filters.append(Pokemon.external_id == external_id)

    if name is not None:
        filters.append(Pokemon.name == name)

    if not filters:
        return

    query = db.query(Pokemon).filter(or_(*filters))

    if pokemon_id is not None:
        query = query.filter(Pokemon.id != pokemon_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pokemon with this external_id or name already exists",
        )


@router.post("/", response_model=PokemonResponse, status_code=status.HTTP_201_CREATED)
def create_pokemon(pokemon_payload: PokemonCreate, db: Session = Depends(get_db)):
    _raise_if_pokemon_conflicts(
        db,
        external_id=pokemon_payload.external_id,
        name=pokemon_payload.name,
    )

    pokemon = Pokemon(**_pokemon_payload_to_model_data(pokemon_payload))

    db.add(pokemon)
    db.commit()
    db.refresh(pokemon)

    return pokemon


@router.post("/import/{identifier}", response_model=PokemonResponse)
def import_pokemon(identifier: str, db: Session = Depends(get_db)):
    external_pokemon = get_external_pokemon_data(identifier)

    if external_pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pokemon not found in external API",
        )

    pokemon = (
        db.query(Pokemon)
        .filter(Pokemon.external_id == external_pokemon["external_id"])
        .first()
    )

    if pokemon is not None:
        return pokemon

    pokemon = Pokemon(**external_pokemon)

    db.add(pokemon)
    db.commit()
    db.refresh(pokemon)

    return pokemon


@router.get("/", response_model=PokemonListResponse)
def list_pokemons(
    request: Request,
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    page: int | None = Query(None, ge=1),
    size: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    if page is not None or size is not None:
        if page is None or size is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both page and size must be provided together.",
            )

        offset = (page - 1) * size
        limit = size

    total = db.query(func.count(Pokemon.id)).scalar() or 0
    pokemons = db.query(Pokemon).offset(offset).limit(limit).all()
    base_path = request.url.path.rstrip("/") or "/"

    next_offset = offset + limit
    next_url = f"{base_path}?limit={limit}&offset={next_offset}" if next_offset < total else None
    previous_url = (
        f"{base_path}?limit={limit}&offset={max(offset - limit, 0)}"
        if offset > 0
        else None
    )

    return {
        "data": pokemons,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "next": next_url,
            "previous": previous_url,
        },
    }


@router.get("/{pokemon_id}", response_model=PokemonResponse)
def get_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()

    if pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pokemon not found",
        )

    return pokemon


@router.put("/{pokemon_id}", response_model=PokemonResponse)
def update_pokemon(
    pokemon_id: int,
    pokemon_payload: PokemonUpdate,
    db: Session = Depends(get_db),
):
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()

    if pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pokemon not found",
        )

    _raise_if_pokemon_conflicts(
        db,
        external_id=pokemon_payload.external_id,
        name=pokemon_payload.name,
        pokemon_id=pokemon_id,
    )

    for field, value in _pokemon_payload_to_model_data(pokemon_payload).items():
        setattr(pokemon, field, value)

    db.commit()
    db.refresh(pokemon)

    return pokemon


@router.delete("/{pokemon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()

    if pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pokemon not found",
        )

    db.delete(pokemon)
    db.commit()
