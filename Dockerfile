FROM python:3.10-slim as builder

RUN apt update && apt install -y gcc g++ libpq-dev python3-dev -y

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# copy files
COPY pyproject.toml pdm.lock README.md /project/
COPY src/ /project/src

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


# run stage
FROM python:3.10-slim

# retrieve packages from build stage
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.10/lib /project/pkgs

# retrieve executables
COPY --from=builder /project/__pypackages__/3.10/bin/* /bin/

COPY src/ /project/src
COPY dictionaries/ /project/src/dictionaries

WORKDIR /project/src

# Run apache server
EXPOSE 80