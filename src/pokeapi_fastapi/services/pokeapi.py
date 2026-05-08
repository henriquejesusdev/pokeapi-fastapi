import requests

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"


def get_external_pokemon_data(identifier: str):
    response = requests.get(
        f"{POKEAPI_BASE_URL}/pokemon/{identifier}",
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    data = response.json()

    return {
        "external_id": data["id"],
        "name": data["name"],
        "height": data["height"],
        "weight": data["weight"],
        "types": ",".join(
            pokemon_type["type"]["name"] for pokemon_type in data["types"]
        ),
        "front_default": data["sprites"]["front_default"],
        "back_default": data["sprites"]["back_default"],
    }
