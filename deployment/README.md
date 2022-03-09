**Initial Dev Deployment**
> `docker-compose -f docker-compose.dev up --build -d`

**Initial 'Prod' Deployment**
> `docker-compose up --build -d`

**First Time Datebase Setup**
>`docker exec api python config/insertdictionary.py`

