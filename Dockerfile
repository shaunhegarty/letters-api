FROM python:3.10-slim

RUN apt update && apt install -y gcc g++ libpq-dev python3-dev -y

# install PDM
RUN pip install uv

# copy files
COPY requirements/base.txt README.md /project/
COPY src/ /project/src

# install dependencies and project into the local packages directory
WORKDIR /project
RUN uv pip install --system -r /project/base.txt

COPY dictionaries/ /project/src/dictionaries

WORKDIR /project/src

# Run apache server
EXPOSE 80