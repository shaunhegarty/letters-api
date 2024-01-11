# ruff: noqa: S101
from __future__ import annotations

import os

import pytest
from letters.anagrammer import dictionary, ladder
from letters.anagrammer.dictionary import get_anagrams, get_conundrums, get_sub_anagrams
from letters.anagrammer.ladder import (
    get_easy_ladders_by_word_length,
    get_ladders_by_length_and_difficulty,
)
from letters.anagrammer.models import Dictionary, Ladder, WordScore
from letters.config import insertdictionary
from letters.config.insertdictionary import load_common, load_sowpods
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, create_engine, select

from tests.utils import setup_ladders, setup_ladders_new

POSTGRES_HOSTNAME = os.environ.get("POSTGRES_HOSTNAME", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://api:letters@{POSTGRES_HOSTNAME}/"

# Set up test DB
engine = create_engine(
    f"{SQLALCHEMY_DATABASE_URL}/api_test_db",
)

if not database_exists(engine.url):
    create_database(engine.url)


@pytest.fixture(name="session")
def session_fixture() -> None:
    engine = create_engine(
        f"{SQLALCHEMY_DATABASE_URL}/api_test_db",
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


def test_create_word(session: Session) -> None:
    load_sowpods(session, limit=10)
    row = session.exec(
        select(Dictionary)
        .where(Dictionary.word == "aardvark")
        .where(Dictionary.dictionary == "sowpods")
    ).first()
    assert row is not None
    assert row.word == "aardvark"

    load_common(session, limit=10)
    row = session.exec(
        select(Dictionary)
        .where(Dictionary.word == "the")
        .where(Dictionary.dictionary == "common")
    ).first()
    assert row is not None
    assert row.word == "the"


def test_get_anagrams(session: Session) -> None:
    load_sowpods(session, limit=1000)
    anagrams = get_anagrams(word="aboard", session=session)
    assert "abroad" in anagrams


def test_get_sub_anagrams(session: Session) -> None:
    load_sowpods(session, limit=1000)
    anagrams = get_sub_anagrams(word="aboard", session=session)
    assert "abroad" in anagrams
    assert "abord" in anagrams
    assert "aa" in anagrams


def test_get_conundrums(session: Session) -> None:
    load_sowpods(session, limit=1000)
    conundrums = get_conundrums(length=6, session=session)
    assert "abacus" in conundrums


def test_dict_size(session: Session) -> None:
    score = 1000
    load_sowpods(session, limit=score)
    assert dictionary.get_dict_size(dictionary="sowpods", session=session) == score


def test_contains_word(session: Session) -> None:
    load_sowpods(session, limit=1000)
    assert True is dictionary.contains_word(word="aboard", session=session)


def test_get_words_by_length(session: Session) -> None:
    load_sowpods(session, limit=1000)
    words_of_length = dictionary.get_words_by_length(length=6, session=session)
    assert "aboard" in words_of_length


def test_create_ladder(session: Session) -> None:
    setup_ladders(session)
    # go looking for it

    results = get_ladders_by_length_and_difficulty(
        word_length=4, upper_bound=1000, lower_bound=0, session=session,
    )
    ladder1: Ladder = results[0]
    assert ladder1.pair == "came-will"

    results_2 = get_easy_ladders_by_word_length(word_length=4, session=session)
    assert True is any(r["pair"] == "like-went" for r in results_2["ladders"])


def test_create_ladder_new_style(session: Session) -> None:
    setup_ladders_new(session)
    # go looking for it

    results = get_ladders_by_length_and_difficulty(
        word_length=5, upper_bound=1000, lower_bound=0, session=session,
    )
    ladder1: Ladder = results[0]
    assert ladder1.pair == "onion-anion"

    results_2 = get_easy_ladders_by_word_length(word_length=5, session=session)
    assert True is any(r["pair"] == "onion-ancon" for r in results_2["ladders"])


def test_get_ladder(session: Session) -> None:
    setup_ladders(session)
    pair_ladder = ladder.get_word_ladder_for_word_pair(
        word_pair="came-will", session=session,
    )
    assert pair_ladder["ladder"]["chain"][0] == "came,wame,wale,wall,will"

    pair_ladder = ladder.get_word_ladder_for_word_pair(
        word_pair="will-came", session=session,
    )
    assert pair_ladder["ladder"]["chain"][0] == "will,wall,wale,wame,came"


def test_search_ladders(session: Session) -> None:
    setup_ladders(session)
    options = ladder.WordLadderOptions(
        difficulty=[1, 2], length=[4], ladder_filter="wil",
    )
    results = ladder.search_ladders(options=options, session=session)
    assert True is any(r["pair"] == "came-will" for r in results["ladders"])


def test_word_scores(session: Session) -> None:
    score = 1000
    load_common(session, limit=score)
    word_scores = insertdictionary.get_word_scores(session=session)
    assert word_scores["wing"] == score


def test_populate_word_scores(session: Session) -> None:
    score = 1000
    load_common(session, limit=score)
    word_scores = insertdictionary.get_word_scores(session=session)
    insertdictionary.insert_word_scores(session=session, word_scores=word_scores)

    word_score: WordScore | None = session.exec(
        select(WordScore)
        .where(WordScore.score == score)
        .where(WordScore.dictionary == "common"),
    ).first()
    assert word_score is not None
    assert word_score.word == "wing"
