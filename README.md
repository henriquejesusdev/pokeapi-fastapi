# Pokedex API

API em FastAPI para cadastro de usuarios, login, consulta externa na PokeAPI e cache local de pokemons no PostgreSQL.

## Tecnologias

- Python 3.14
- FastAPI
- SQLAlchemy
- PostgreSQL
- Poetry
- Docker Compose
- Pytest

## Subir com Docker

Na raiz do projeto, rode:

```powershell
docker compose up --build
```

A API ficara disponivel em:

```text
http://localhost:8000
```

Documentacao Swagger:

```text
http://localhost:8000/docs
```

Para rodar em segundo plano:

```powershell
docker compose up --build -d
```

Para ver os logs:

```powershell
docker compose logs -f
```

Para parar os containers:

```powershell
docker compose down
```

## Rodar localmente

Suba apenas o banco com Docker:

```powershell
docker compose up -d postgres
```

Depois rode a API local com Poetry:

```powershell
poetry run uvicorn pokeapi_fastapi.main:app --reload
```

## Banco de dados

O Docker Compose cria um PostgreSQL com:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pokedex
```

Dentro do Docker, a API usa:

```text
postgresql+psycopg2://postgres:postgres@postgres:5432/pokedex
```

Rodando localmente, o padrao e:

```text
postgresql+psycopg2://postgres:postgres@localhost:5432/pokedex
```

As tabelas sao criadas automaticamente quando a API inicia.

## Endpoints

### Home

```text
GET /
```

### Auth

```text
POST /auth/register
POST /auth/login
```

Exemplo de cadastro:

```json
{
  "username": "ash",
  "email": "ash@example.com",
  "password": "pikachu123"
}
```

Exemplo de login:

```json
{
  "email": "ash@example.com",
  "password": "pikachu123"
}
```

### Pokemons salvos no banco

```text
POST   /pokemons/import/{identifier}
GET    /pokemons/
GET    /pokemons/{pokemon_id}
DELETE /pokemons/{pokemon_id}
```

O `identifier` pode ser o nome ou numero do pokemon na Pokedex:

```text
POST /pokemons/import/pikachu
POST /pokemons/import/25
```

Ao importar, a API consulta a PokeAPI externa, normaliza os dados e salva no banco local. Se o pokemon ja existir, a API retorna o registro salvo sem duplicar.

### API externa

```text
GET /external/
GET /external/pokemon/{name}
```

Exemplo:

```text
GET /external/pokemon/pikachu
```

## Testes

Para rodar os testes:

```powershell
poetry run pytest
```

Os testes usam SQLite em memoria para nao depender do PostgreSQL.
