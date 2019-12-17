FROM python:3.8-slim-buster
WORKDIR /code
ENV FLASK_APP application.py
ENV FLASK_RUN_HOST 0.0.0.0
# RUN apk add --no-cache gcc musl-dev linux-headers | alpine specific? Maybe can replace with apt?
# RUN apt-get update && apt-get install -y libpq-dev
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run"]