import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pokeapi_fastapi.database.connection import get_db
from pokeapi_fastapi.database.models import Base
from pokeapi_fastapi.main import app
from pokeapi_fastapi.routes import pokemon as pokemon_routes

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_external_pokemon(monkeypatch):
    def fake_get_external_pokemon_data(identifier):
        if identifier == "missingno":
            return None

        if identifier in ("pikachu", "25"):
            return {
                "external_id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "types": "electric",
                "front_default": "https://example.com/pikachu-front.png",
                "back_default": "https://example.com/pikachu-back.png",
            }

        return {
            "external_id": 1,
            "name": "bulbasaur",
            "height": 7,
            "weight": 69,
            "types": "grass,poison",
            "front_default": "https://example.com/bulbasaur-front.png",
            "back_default": "https://example.com/bulbasaur-back.png",
        }

    monkeypatch.setattr(
        pokemon_routes,
        "get_external_pokemon_data",
        fake_get_external_pokemon_data,
    )


client = TestClient(app)


def test_create_pokemon():
    response = client.post(
        "/pokemons/",
        json={
            "external_id": 150,
            "name": "Mewtwo",
            "height": 20,
            "weight": 1220,
            "types": ["Psychic"],
            "sprites": {
                "front_default": "https://example.com/mewtwo-front.png",
                "back_default": "https://example.com/mewtwo-back.png",
            },
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "external_id": 150,
        "name": "mewtwo",
        "height": 20,
        "weight": 1220,
        "types": ["psychic"],
        "sprites": {
            "front_default": "https://example.com/mewtwo-front.png",
            "back_default": "https://example.com/mewtwo-back.png",
        },
    }


def test_create_pokemon_conflict(mock_external_pokemon):
    client.post("/pokemons/import/pikachu")

    response = client.post(
        "/pokemons/",
        json={
            "external_id": 25,
            "name": "pikachu-clone",
            "height": 4,
            "weight": 60,
            "types": ["electric"],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Pokemon with this external_id or name already exists"
    }


def test_import_pokemon(mock_external_pokemon):
    response = client.post("/pokemons/import/pikachu")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "external_id": 25,
        "name": "pikachu",
        "height": 4,
        "weight": 60,
        "types": ["electric"],
        "sprites": {
            "front_default": "https://example.com/pikachu-front.png",
            "back_default": "https://example.com/pikachu-back.png",
        },
    }


def test_import_existing_pokemon_returns_cached_record(mock_external_pokemon):
    first_response = client.post("/pokemons/import/pikachu")
    second_response = client.post("/pokemons/import/25")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()


def test_import_pokemon_not_found(mock_external_pokemon):
    response = client.post("/pokemons/import/missingno")

    assert response.status_code == 404
    assert response.json() == {"detail": "Pokemon not found in external API"}


def test_list_pokemons(mock_external_pokemon):
    client.post("/pokemons/import/pikachu")

    response = client.get("/pokemons/")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "id": 1,
                "external_id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "types": ["electric"],
                "sprites": {
                    "front_default": "https://example.com/pikachu-front.png",
                    "back_default": "https://example.com/pikachu-back.png",
                },
            }
        ],
        "pagination": {
            "total": 1,
            "limit": 20,
            "offset": 0,
            "next": None,
            "previous": None,
        },
    }


def test_list_pokemons_pagination(mock_external_pokemon):
    client.post("/pokemons/import/bulbasaur")
    client.post("/pokemons/import/pikachu")

    response = client.get("/pokemons/?limit=1&offset=0")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "id": 1,
                "external_id": 1,
                "name": "bulbasaur",
                "height": 7,
                "weight": 69,
                "types": ["grass", "poison"],
                "sprites": {
                    "front_default": "https://example.com/bulbasaur-front.png",
                    "back_default": "https://example.com/bulbasaur-back.png",
                },
            }
        ],
        "pagination": {
            "total": 2,
            "limit": 1,
            "offset": 0,
            "next": "/pokemons?limit=1&offset=1",
            "previous": None,
        },
    }


def test_get_pokemon_by_id(mock_external_pokemon):
    create_response = client.post("/pokemons/import/pikachu")
    pokemon_id = create_response.json()["id"]

    response = client.get(f"/pokemons/{pokemon_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": pokemon_id,
        "external_id": 25,
        "name": "pikachu",
        "height": 4,
        "weight": 60,
        "types": ["electric"],
        "sprites": {
            "front_default": "https://example.com/pikachu-front.png",
            "back_default": "https://example.com/pikachu-back.png",
        },
    }


def test_update_pokemon(mock_external_pokemon):
    create_response = client.post("/pokemons/import/pikachu")
    pokemon_id = create_response.json()["id"]

    response = client.put(
        f"/pokemons/{pokemon_id}",
        json={
            "name": "raichu",
            "height": 8,
            "weight": 300,
            "types": ["electric"],
            "sprites": {
                "front_default": "https://example.com/raichu-front.png",
                "back_default": "https://example.com/raichu-back.png",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": pokemon_id,
        "external_id": 25,
        "name": "raichu",
        "height": 8,
        "weight": 300,
        "types": ["electric"],
        "sprites": {
            "front_default": "https://example.com/raichu-front.png",
            "back_default": "https://example.com/raichu-back.png",
        },
    }


def test_update_pokemon_partial_sprite_keeps_existing_sprite(mock_external_pokemon):
    create_response = client.post("/pokemons/import/pikachu")
    pokemon_id = create_response.json()["id"]

    response = client.put(
        f"/pokemons/{pokemon_id}",
        json={
            "sprites": {
                "front_default": "https://example.com/pikachu-front-v2.png",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["sprites"] == {
        "front_default": "https://example.com/pikachu-front-v2.png",
        "back_default": "https://example.com/pikachu-back.png",
    }


def test_update_pokemon_conflict(mock_external_pokemon):
    client.post("/pokemons/import/bulbasaur")
    pikachu_response = client.post("/pokemons/import/pikachu")
    pokemon_id = pikachu_response.json()["id"]

    response = client.put(
        f"/pokemons/{pokemon_id}",
        json={"external_id": 1},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Pokemon with this external_id or name already exists"
    }


def test_update_pokemon_not_found():
    response = client.put(
        "/pokemons/999",
        json={"name": "missingno"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Pokemon not found"}


def test_delete_pokemon(mock_external_pokemon):
    create_response = client.post("/pokemons/import/pikachu")
    pokemon_id = create_response.json()["id"]

    delete_response = client.delete(f"/pokemons/{pokemon_id}")
    get_response = client.get(f"/pokemons/{pokemon_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Pokemon not found"}


def test_get_pokemon_not_found():
    response = client.get("/pokemons/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Pokemon not found"}
