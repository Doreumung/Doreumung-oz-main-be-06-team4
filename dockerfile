FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Poetry 설치
RUN pip install "poetry==$POETRY_VERSION"
ENV PATH="$POETRY_HOME/bin:$PATH"

# 의존성 파일 복사 및 설치
COPY pyproject.toml poetry.lock alembic.ini ./
RUN poetry install --no-root --no-dev

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
