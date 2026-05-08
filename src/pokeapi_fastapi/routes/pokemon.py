from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from pokeapi_fastapi.database.connection import get_db
from pokeapi_fastapi.database.models import Pokemon
from pokeapi_fastapi.schemas.pokemon import (
    PokemonCreate,
    PokemonResponse,
    PokemonUpdate,
)

router = APIRouter(prefix="/pokemons", tags=["Pokemons"])


@router.post("/", response_model=PokemonResponse)
def create_pokemon(data: PokemonCreate, db: Session = Depends(get_db)):
    pokemon = Pokemon(name=data.name, type=data.type)

    db.add(pokemon)
    db.commit()
    db.refresh(pokemon)

    return pokemon


@router.get("/", response_model=list[PokemonResponse])
def list_pokemons(db: Session = Depends(get_db)):
    return db.query(Pokemon).all()


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
    data: PokemonUpdate,
    db: Session = Depends(get_db),
):
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()

    if pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pokemon not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
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
