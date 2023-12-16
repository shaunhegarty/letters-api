## Deployment Cheat Sheet
Initial Dev Deployment
> `docker-compose -f docker-compose.dev up --build -d`

Initial 'Prod' Deployment
> `docker-compose up --build -d`

First Time Datebase Setup
>`docker exec api python -m config.insertdictionary`

### **Manual run (Dev)**
> `flask run --host=0.0.0.0 --port 5001`

### **Manual run (Prod)**
> `gunicorn --worker-class gevent --bind 0.0.0.0:80 wsgi:application --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info`

## Postgres Cheat Sheet
Connect with psql
> `docker exec -it letters_db psql -d words psql -U api`

List databases
>`\l`

List tables
>`\dt`

Connect to database
>`\c database_name`

Quit
> `\q`

