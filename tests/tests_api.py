# ruff: noqa: S101, ANN201, PLR2004
import http
import os
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from letters.anagrammer.main import app, get_session
from letters.config.insertdictionary import load_sowpods
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, create_engine

from tests.utils import setup_ladders, setup_word_scores

POSTGRES_HOSTNAME = os.environ.get("POSTGRES_HOSTNAME", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://api:letters@{POSTGRES_HOSTNAME}/"

# Set up test DB
engine = create_engine(
    f"{SQLALCHEMY_DATABASE_URL}/api_test_db",
)

if not database_exists(engine.url):
    create_database(engine.url)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, Any, None]:
    engine = create_engine(
        f"{SQLALCHEMY_DATABASE_URL}/api_test_db",
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, Any, None]:
    def get_session_override() -> Session:
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_hello(client: TestClient):
    response = client.get("/")
    assert response.status_code == http.HTTPStatus.OK
    assert response.json() == {"greeting": "hello"}


def test_validate_word(client: TestClient, session: Session):
    load_sowpods(session, limit=10)
    response = client.get("/validate/aardvark")
    assert response.json()["valid"] is True


def test_get_anagrams(client: TestClient, session: Session):
    load_sowpods(session, limit=1000)
    response = client.get("/anagrams/abroad")
    anagrams = response.json()
    assert "aboard" in anagrams


def test_get_sub_anagrams(client: TestClient, session: Session):
    load_sowpods(session, limit=1000)
    response = client.get("/subanagrams/abroad")
    sub_anagrams_5 = response.json()["words"]["5"]["words"]
    sub_anagrams_2 = response.json()["words"]["2"]["words"]
    assert "abord" in sub_anagrams_5
    assert "aa" in sub_anagrams_2

    response = client.get("/subanagrams/abroad?best_only=true")
    sub_anagrams_6 = response.json()["words"]["6"]["words"]
    assert "aboard" in sub_anagrams_6


def test_get_conundrums(client: TestClient, session: Session):
    load_sowpods(session, limit=1000)
    response = client.get("/conundrum/3")
    conundra = response.json()
    assert "aah" in conundra


def test_get_words_by_length(client: TestClient, session: Session):
    load_sowpods(session, limit=1000)
    response = client.get("/words/3")
    words = response.json()
    assert "aah" in words


def test_get_ladder(client: TestClient, session: Session):
    setup_ladders(session)
    response = client.get("/ladders/came-will")
    ladder = response.json()
    assert ladder["ladder"]["pair"] == "came-will"
    assert ladder["ladder"]["minimum_chain"] == 5

    response = client.get("/ladders/will-came")
    ladder = response.json()
    assert ladder["ladder"]["pair"] == "will-came"
    assert ladder["ladder"]["minimum_chain"] == 5


def test_get_ladder_by_length(client: TestClient, session: Session):
    setup_ladders(session)
    response = client.get("/ladders/4")
    ladders = response.json()["ladders"]
    assert len(ladders) == 3
    assert sorted(ladders, key=lambda x: x["pair"])[0]["pair"] == "came-will"


def test_get_ladder_by_difficulty(client: TestClient, session: Session):
    setup_ladders(session)
    response = client.get("/ladders/1/4")
    ladders = response.json()
    assert len(ladders["ladders"]) == 3
    assert ladders["ladders"][0]["pair"] == "came-will"


def test_ladder_search(client: TestClient, session: Session):
    setup_ladders(session)
    response = client.post(
        "/ladders/search/", json={"ladder_filter": "lik", "length": [4]}
    )
    ladders = response.json()
    assert len(ladders["ladders"]) == 1
    assert ladders["ladders"][0]["pair"] == "like-went"


def test_word_scores(client: TestClient, session: Session):
    setup_word_scores(session)
    response = client.get("/ladders/words/common/4")
    words = response.json()
    assert "able" in words
    assert words["able"] == 488
