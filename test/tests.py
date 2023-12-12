import json
import os

import pytest
from sqlalchemy import select
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, create_engine

from anagrammer.ladder import (
    get_easy_ladders_by_word_length,
    get_ladders_by_length_and_difficulty,
)
from anagrammer.models import Dictionary, Ladder
from config.insertdictionary import insert_word_ladder, load_common, load_sowpods

POSTGRES_HOSTNAME = os.environ.get("POSTGRES_HOSTNAME", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://api:letters@{POSTGRES_HOSTNAME}/"

# Set up test DB
engine = create_engine(
    f"{SQLALCHEMY_DATABASE_URL}/api_test_db",
)

if not database_exists(engine.url):
    create_database(engine.url)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        f"{SQLALCHEMY_DATABASE_URL}/api_test_db",
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


def test_create_word(session: Session):
    load_sowpods(session, limit=10)
    row = session.exec(
        select(Dictionary)
        .where(Dictionary.word == "aardvark")
        .where(Dictionary.dictionary == "sowpods")
    ).first()
    assert row.Dictionary.word == "aardvark"

    load_common(session, limit=10)
    row = session.exec(
        select(Dictionary)
        .where(Dictionary.word == "the")
        .where(Dictionary.dictionary == "common")
    ).first()
    assert row.Dictionary.word == "the"


def test_create_ladder(session: Session):
    data: dict[str, list[list[str]]] = json.load(
        open("test/ladders.json", "r", encoding="utf-8")
    )

    # get all the words
    words = set()
    for _, ladders in data.items():
        for ladder in ladders:
            for word in ladder:
                words.add(word)

    # build up a dummy word_scores dict
    word_scores: dict[str, int] = {word: 1 for word in words}


    # insert the test data
    insert_word_ladder(data=data, word_scores=word_scores, session=session)

    # go looking for it

    results = get_ladders_by_length_and_difficulty(
        word_length=4, upper_bound=1000, lower_bound=0, session=session
    )
    ladder1: Ladder = results[0]
    assert ladder1.pair == "came-will"
    
    results = get_easy_ladders_by_word_length(word_length=4, session=session)
    print(results)
    assert False


# class TestLadderSearch(unittest.TestCase):
#     def test_working(self):
#         with app.test_client() as test_client:
#             response = test_client.post(
#                 "/ladders/search/",
#                 json={"length": [4], "difficulty": [1, 2], "ladder_filter": "hi"},
#             )
#             parsed_data = {
#                 d["pair"]: d for d in json.loads(response.data).get("ladders", [])
#             }
#             self.assertTrue(parsed_data.get("born-this")["difficulty"] == 17448)

#     def test_page_size(self):
#         with app.test_client() as test_client:
#             response = test_client.post(
#                 "/ladders/search/",
#                 json={"length": [3], "difficulty": [1, 2], "page_size": 23},
#             )
#             parsed_data = {
#                 d["pair"]: d for d in json.loads(response.data).get("ladders", [])
#             }
#             self.assertTrue(len(parsed_data.keys()) == 23)


# if __name__ == "__main__":
#     unittest.main()
