from contextlib import asynccontextmanager

from fastapi import FastAPI

from pokeapi_fastapi.database.connection import engine
from pokeapi_fastapi.database.models import Base
from pokeapi_fastapi.routes.external import router as external_router
from pokeapi_fastapi.routes.pokemon import router as pokemon_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Pokedex API", lifespan=lifespan)


@app.get("/")
def home():
    return {"message": "Pokedex API Online"}


app.include_router(external_router)
app.include_router(pokemon_router)
