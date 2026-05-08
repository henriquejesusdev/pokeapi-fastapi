import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pokeapi_fastapi.database.connection import get_db
from pokeapi_fastapi.database.models import Base
from pokeapi_fastapi.main import app

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


client = TestClient(app)


def test_create_pokemon():
    response = client.post(
        "/pokemons/",
        json={"name": "Pikachu", "type": "Electric"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Pikachu",
        "type": "Electric",
    }


def test_list_pokemons():
    client.post("/pokemons/", json={"name": "Pikachu", "type": "Electric"})
    client.post("/pokemons/", json={"name": "Charmander", "type": "Fire"})

    response = client.get("/pokemons/")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Pikachu", "type": "Electric"},
        {"id": 2, "name": "Charmander", "type": "Fire"},
    ]


def test_get_pokemon_by_id():
    create_response = client.post(
        "/pokemons/",
        json={"name": "Squirtle", "type": "Water"},
    )
    pokemon_id = create_response.json()["id"]

    response = client.get(f"/pokemons/{pokemon_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": pokemon_id,
        "name": "Squirtle",
        "type": "Water",
    }


def test_update_pokemon():
    create_response = client.post(
        "/pokemons/",
        json={"name": "Bulbasaur", "type": "Grass"},
    )
    pokemon_id = create_response.json()["id"]

    response = client.put(
        f"/pokemons/{pokemon_id}",
        json={"type": "Grass/Poison"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": pokemon_id,
        "name": "Bulbasaur",
        "type": "Grass/Poison",
    }


def test_delete_pokemon():
    create_response = client.post(
        "/pokemons/",
        json={"name": "Mew", "type": "Psychic"},
    )
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
