from fastapi.testclient import TestClient

from pokeapi_fastapi.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Pokedex API Online"}
