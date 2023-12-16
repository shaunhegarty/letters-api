import json
from sqlmodel import Session

from letters.config.insertdictionary import (
    insert_word_ladder,
    get_word_scores,
    insert_word_scores,
    load_common,
)


def setup_ladders(session: Session):
    data: dict[str, list[list[str]]] = json.load(
        open("tests/ladders.json", "r", encoding="utf-8")
    )

    # get all the words
    words = set()
    for _, ladders in data.items():
        for lad in ladders:
            for word in lad:
                words.add(word)

    # build up a dummy word_scores dict
    word_scores: dict[str, int] = {word: 1 for word in words}

    # insert the test data
    insert_word_ladder(data=data, word_scores=word_scores, session=session)


def setup_word_scores(session: Session):
    # Only common dataset has word scores
    load_common(session, limit=1000)

    # Rank the words by frequency
    word_scores = get_word_scores(session=session)

    # Add to db
    insert_word_scores(session=session, word_scores=word_scores)
