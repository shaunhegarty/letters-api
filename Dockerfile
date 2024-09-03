FROM python:3.10-slim

RUN apt update && apt install -y gcc g++ libpq-dev python3-dev -y

# install PDM
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# copy files
COPY pyproject.toml uv.lock README.md /project/
COPY src/ /project/src

# install dependencies and project into the local packages directory
WORKDIR /project
RUN uv sync --no-dev

COPY dictionaries/ /project/src/dictionaries

WORKDIR /project/src

ENV PATH="/project/.venv/bin:$PATH"

# Run apache server
EXPOSE 80