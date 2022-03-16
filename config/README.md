## Deployment
Initial Dev Deployment
> `docker-compose -f docker-compose.dev up --build -d`

Initial 'Prod' Deployment
> `docker-compose up --build -d`

First Time Datebase Setup
>`docker exec api python -m config.insertdictionary`


## Postgres Cheat Sheet
Connect with psql
> `docker exec -it letters_db psql -d words psql -U api`

List databases
>`\l`

Connect to database
>`\c database_name`

Quit
> `\q`

