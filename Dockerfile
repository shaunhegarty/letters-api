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

EXPOSE 5000
CMD ["uvicorn", "anagrammer.main:app", "--host", "0.0.0.0", "--port", "5000"]