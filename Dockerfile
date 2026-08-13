# Aegis-LLM API + worker image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/aegis

# System deps for Playwright chromium (heavier than the base image on purpose;
# browser connectors need it). Skip with --build-arg BROWSER=0 for API-only.
ARG BROWSER=1
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
        libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY mock_target ./mock_target
COPY payload_packs ./payload_packs

RUN pip install --upgrade pip \
    && pip install .

RUN if [ "$BROWSER" = "1" ]; then pip install playwright && playwright install chromium --with-deps; fi

EXPOSE 8000

# Default: API. Worker image uses the same Dockerfile with a different command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
