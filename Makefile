# Define variables
COMPOSE := docker-compose -f docker-compose.dev.yml

.PHONY: build run run_dev db_only psql stop

build:
	$(COMPOSE) build

run:
	$(COMPOSE) up -d

run_dev:
	. .venv/bin/activate && uvicorn anagrammer.main:app --reload

db_only: 
	$(COMPOSE) up -d db

psql: 
	$(COMPOSE) run --rm db psql

stop:
	$(COMPOSE) down
