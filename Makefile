# Define variables
COMPOSE := docker compose -f docker-compose.dev.yml
COMPOSE_PROD := docker compose

.PHONY: build run dev db_only psql stop logs mypy test check_db

build:
	$(COMPOSE) build

run: build
	$(COMPOSE) up -d

run_prod: build
	$(COMPOSE_PROD) up -d

dev: .venv
	./startdev

db_only: 
	$(COMPOSE) up -d db

psql: 
	$(COMPOSE) run --rm db psql

setup: build db_only
	$(COMPOSE) run --rm db dropdb --if-exists 'words'
	$(COMPOSE) run --rm web python -m src.letters.config.insertdictionary

setup_prod: build
	$(COMPOSE_PROD) up -d db
	$(COMPOSE_PROD) run --rm db dropdb --if-exists 'words'
	$(COMPOSE_PROD) run --rm web python -m config.insertdictionary

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f web

test: .venv
	. .venv/bin/activate; python -m pytest tests/*.py

mypy: .venv
	. .venv/bin/activate; mypy --config-file .mypy.ini .

.venv: .venv/touchfile

.venv/touchfile: pyproject.toml
	pdm install
	touch .venv/touchfile

env: .venv


	