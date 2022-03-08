**Initial Dev Deployment**
> `docker-compose -f docker-compose.dev up --build -d`

**Initial 'Prod' Deployment**
> `docker-compose up --build -d`

**First Time Datebase Setup**
>`docker exec api python config/insertdictionary.py`

**Apache Setup**

Install apache on the host
>`sudo apt update && sudo apt install apache2`

Add server config
>`sudo cp deployment/external-apache.conf /etc/apache2/sites-available/letters-api.conf`

Enable Site
>`a2ensite letters-api`

Enable reverse proxy
>`a2enmod proxy_http`

>`a2enmode proxy`

Restart Apache
>`sudo service apache2 restart`

[Visit Site](http://api.shaunhegarty.com)


