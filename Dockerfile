FROM python:3.11-alpine
WORKDIR /var/www/letters-api/

# Install app requirements
COPY requirements/ requirements/
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev python3-dev linux-headers && \
 python3 -m pip install -r requirements/base.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY . /var/www/letters-api/

# Run apache server
EXPOSE 80
CMD gunicorn --worker-class gevent --bind 0.0.0.0:80 wsgi:application --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info