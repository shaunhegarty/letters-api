include .env

# Define variables
COMPOSE := docker compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml

.PHONY: build run dev db_only psql stop logs mypy test check_db

build:
	$(COMPOSE) build

run: build
	$(COMPOSE) up -d

dev: .venv
	./startdev

db_only: 
	$(COMPOSE) up -d db

lab: build
	uv run jupyter-lab

psql: 
	$(COMPOSE) run --rm db psql

setup: build db_only
	$(COMPOSE) run --rm db dropdb --if-exists 'words'
	$(COMPOSE) run --rm web python -m letters.config.insertdictionary

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f web

test: .venv
	uv run pytest tests/*.py

mypy: .venv
	uv run mypy --config-file .mypy.ini .

.venv: .venv/touchfile

.venv/touchfile: pyproject.toml
	uv sync
	touch .venv/touchfile

env: .venv


	