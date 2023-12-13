# Define variables
COMPOSE := docker-compose -f docker-compose.dev.yml

.PHONY: build run run_dev db_only psql stop logs

build:
	$(COMPOSE) build

run: build
	$(COMPOSE) up -d

run_dev:
	./startdev

db_only: 
	$(COMPOSE) up -d db

psql: 
	$(COMPOSE) run --rm db psql

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f web

test: build
	$(COMPOSE) run --rm web python -m pytest test/tests.py