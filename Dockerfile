FROM python:3.10
WORKDIR /var/www/letters-api/

# Install app requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /var/www/letters-api/

# Run apache server
EXPOSE 80
CMD gunicorn --worker-class gevent --bind 0.0.0.0:80 wsgi:application --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info