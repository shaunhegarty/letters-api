FROM python:3.7-slim
WORKDIR /var/www/letters-api/

# Set up Apache ENVs
ENV APACHE_RUN_DIR /var/run/apache2/
ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_PID_FILE /var/run/apache2/apache2.pid
ENV APACHE_LOCK_DIR /var/lock/apache2
RUN mkdir -p $APACHE_RUN_DIR
RUN mkdir -p $APACHE_LOCK_DIR
RUN mkdir -p $APACHE_LOG_DIR

# Install and enable mod_wsgi
RUN apt-get update && apt-get install -y apache2 libapache2-mod-wsgi-py3 python3-dev && apt-get clean
RUN a2enmod wsgi

# Copy apache conf and set permissions
COPY letters-api.conf /etc/apache2/sites-available/letters-api.conf
RUN chown -R www-data:www-data /var/www/letters-api/
RUN chown www-data:www-data /etc/apache2/sites-available/letters-api.conf

# Install app requirements
COPY . /var/www/letters-api/
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Enable site
RUN a2ensite letters-api

# Run apache server
EXPOSE 80
CMD ["/usr/sbin/apache2", "-D", "FOREGROUND"]