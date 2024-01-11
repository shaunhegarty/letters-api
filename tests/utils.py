from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from letters.config.insertdictionary import (
    get_word_scores,
    insert_word_ladder,
    insert_word_scores,
    load_common,
)

if TYPE_CHECKING:
    from sqlmodel import Session


def setup_ladders(session: Session) -> None:
    with Path("tests/ladders.json").open(encoding="utf-8") as file:
        data: dict[str, list[list[str]]] = json.load(file)

    # get all the words
    words = {word for ladders in data.values() for lad in ladders for word in lad}

    # build up a dummy word_scores dict
    word_scores: dict[str, int] = {word: 1 for word in words}

    # insert the test data
    insert_word_ladder(data=data, word_scores=word_scores, session=session)


def setup_ladders_new(session: Session) -> None:
    with Path("tests/onionladders.json").open(encoding="utf-8") as file:
        data: dict[str, list[list[str]]] = json.load(file)

    # get all the words
    words = {
        word for ladders in data.values() for lad in ladders for word in lad["path"]
    }

    # build up a dummy word_scores dict
    word_scores: dict[str, int] = {word: 1 for word in words}

    # insert the test data
    insert_word_ladder(data=data, word_scores=word_scores, session=session)


def setup_word_scores(session: Session) -> None:
    # Only common dataset has word scores
    load_common(session, limit=1000)

    # Rank the words by frequency
    word_scores = get_word_scores(session=session)

    # Add to db
    insert_word_scores(session=session, word_scores=word_scores)
