from fastapi import APIRouter, HTTPException, status

from pokeapi_fastapi.services.pokeapi import get_external_pokemon_data

router = APIRouter(prefix="/external", tags=["External"])


@router.get("/")
def external_status():
    return {"message": "External route working"}


@router.get("/pokemon/{name}")
def get_external_pokemon(name: str):
    pokemon = get_external_pokemon_data(name)

    if pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pokemon not found in external API",
        )

    return pokemon
