FROM python:3.14

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY . .

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

EXPOSE 8000

CMD ["sh", "-c", "uvicorn pokeapi_fastapi.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
