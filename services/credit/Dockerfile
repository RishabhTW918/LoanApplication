FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install poetry

COPY credit/pyproject.toml credit/poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY credit/app ./app
COPY common ./services/common
COPY __init__.py ./services/__init__.py

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the consumer
CMD ["python", "-m", "app.main"]