# Define variables
COMPOSE := docker compose -f docker-compose.dev.yml

.PHONY: build run run_dev db_only psql stop logs mypy test check_db

build:
	$(COMPOSE) build

run: build
	$(COMPOSE) up -d

dev: .venv
	./startdev

db_only: 
	$(COMPOSE) up -d db

psql: 
	$(COMPOSE) run --rm db psql

setup: build
	$(COMPOSE) run --rm db dropdb --if-exists 'words'
	$(COMPOSE) run --rm web python -m config.insertdictionary

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f web

test: .venv
	. .venv/bin/activate; python -m pytest test/tests.py

mypy: build
	$(COMPOSE) run --rm web mypy --config-file .mypy.ini .

.venv: .venv/touchfile

.venv/touchfile: requirements/dev.txt requirements/base.txt
	python3.11 -m venv .venv
	.venv/bin/pip install -r requirements/dev.txt
	touch .venv/touchfile

env: .venv


	