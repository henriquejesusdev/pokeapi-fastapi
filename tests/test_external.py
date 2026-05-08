import requests
from fastapi.testclient import TestClient

from pokeapi_fastapi.main import app

client = TestClient(app)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()


def test_external_status():
    response = client.get("/external/")

    assert response.status_code == 200
    assert response.json() == {"message": "External route working"}


def test_get_external_pokemon(monkeypatch):
    def fake_get(url, timeout):
        assert url == "https://pokeapi.co/api/v2/pokemon/pikachu"
        assert timeout == 10
        return FakeResponse(
            200,
            {
                "id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "types": [{"type": {"name": "electric"}}],
            },
        )

    monkeypatch.setattr(requests, "get", fake_get)

    response = client.get("/external/pokemon/pikachu")

    assert response.status_code == 200
    assert response.json() == {
        "external_id": 25,
        "name": "pikachu",
        "height": 4,
        "weight": 60,
        "types": "electric",
    }


def test_get_external_pokemon_not_found(monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse(404, {"detail": "Not found"})

    monkeypatch.setattr(requests, "get", fake_get)

    response = client.get("/external/pokemon/missingno")

    assert response.status_code == 404
    assert response.json() == {"detail": "Pokemon not found in external API"}
