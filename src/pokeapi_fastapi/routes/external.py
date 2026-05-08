import requests
from fastapi import APIRouter
from requests import Response

router = APIRouter(prefix="/external", tags=["External"])


@router.get("/")
def external_status():
    return {"message": "External route working"}


@router.get("/pokemon/{name}")
def get_external_pokemon(name: str):
    response: Response = requests.get(
        f"https://pokeapi.co/api/v2/pokemon/{name}",
        timeout=10,
    )

    if response.status_code == 404:
        return {"detail": "Pokemon not found in external API"}

    response.raise_for_status()

    return response.json()
