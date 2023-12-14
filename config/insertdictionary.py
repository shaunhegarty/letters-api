import json
import logging
import sys

import requests
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, col, select

from anagrammer import models
from anagrammer.database import engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def load_common(session: Session, limit: int = 0) -> None:
    with open("dictionaries/common.frequency.csv", "r", encoding="utf-8") as dictionary:
        source = "wikipedia-word-frequency-list-2019"
        values = []
        count = 0
        for line in dictionary:
            word, frequency = line.split()
            word = word.strip()
            values.append(
                {
                    "word": word,
                    "frequency": int(frequency),
                    "word_length": len(word),
                    "dictionary": "common",
                    "source": source,
                    "sorted_word": "".join(sorted(word.lower())),
                }
            )
            count += 1
            if limit != 0 and count >= limit:
                break
        statement = insert(models.Dictionary).values(values).on_conflict_do_nothing()
        logger.info("Inserting Common Words (with frequencies) into database.")
        session.exec(statement)  # type: ignore
        session.commit()


def load_sowpods(session: Session, limit: int = 0) -> None:
    with open("dictionaries/sowpods.txt", "r", encoding="utf-8") as dictionary:
        values = []
        count = 0
        for word in dictionary:
            word = word.strip()
            values.append(
                {
                    "word": word,
                    "word_length": len(word),
                    "dictionary": "sowpods",
                    "sorted_word": "".join(sorted(word.lower())),
                }
            )
            count += 1
            if limit != 0 and count >= limit:
                break

        logger.info("Inserting SOWPODS Words into database.")
        statement = insert(models.Dictionary).values(values).on_conflict_do_nothing()
        session.exec(statement)  # type: ignore
        session.commit()


def setup_dictionaries() -> None:
    with Session(engine) as session:
        logger.info("Reading Common Words (with frequencies)")
        load_common(session=session)
        logger.info("Done.")

        logger.info("Reading SOWPODS dictionary")
        load_sowpods(session=session)
        logger.info("Done.")


Ladder = list[str]
LadderSet = list[Ladder]


def get_ladder_json(word_length) -> dict[str, LadderSet]:
    assert 3 <= word_length <= 6

    response = requests.get(
        f"https://raw.githubusercontent.com/shaunhegarty/word-ladder/master/wordladder/resources/ladder-common-{word_length}.json"
    )
    data = json.loads(response.content.decode("utf-8"))
    return data


def sort_word_pair(pair) -> str:
    return "-".join(sorted(pair.split("-")))


def ladder_difficulty(ladder: Ladder, word_scores: dict[str, int]) -> int:
    word_score = 0
    for word in ladder:
        word_score += word_scores[word]
    return word_score


def get_hardest_word(ladder: Ladder, word_scores: dict[str, int]) -> tuple[str, int]:
    hardest_word_score: int = 0
    hardest_word: str = ""
    for word in ladder:
        word_score = word_scores.get(word, 0)
        if word_score > hardest_word_score:
            hardest_word_score = word_score
            hardest_word = word
    return hardest_word, hardest_word_score


def get_word_scores(session: Session) -> dict[str, int]:
    results = session.exec(
        select(
            models.Dictionary,
            func.rank().over(order_by=col(models.Dictionary.frequency).desc()),
        ).where(models.Dictionary.dictionary == "common")
    ).all()
    word_scores = {word.word: rank for word, rank in results}
    return word_scores


def insert_word_scores(session: Session, word_scores: dict[str, int]) -> None:
    # Populate Word Score
    values = []
    for word, word_score in word_scores.items():
        values.append({"word": word, "dictionary": "common", "score": word_score})
    statement = insert(models.WordScore).values(values).on_conflict_do_nothing()
    session.exec(statement)  # type: ignore
    session.commit()


def insert_word_ladder(
    data: dict[str, LadderSet], word_scores: dict[str, int], session: Session
) -> None:
    unique_ladder_keys: set[str] = {sort_word_pair(pair) for pair in data.keys()}

    logger.debug("%s ladder keys", len(unique_ladder_keys))
    values: list[dict] = []
    for key in unique_ladder_keys:
        ladder_list: LadderSet = data[key]
        for index, ladder in enumerate(ladder_list):
            hardest_word, hardest_word_score = get_hardest_word(ladder, word_scores)
            values.append(
                {
                    "pair": key,
                    "dictionary": "common",
                    "chain": ",".join(ladder),
                    "length": len(ladder),
                    "difficulty": ladder_difficulty(ladder, word_scores),
                    "hardest_word": hardest_word,
                    "hardest_word_score": hardest_word_score,
                    "variations": len(ladder_list),
                    "variant": index + 1,
                }
            )
    statement = insert(models.Ladder).values(values).on_conflict_do_nothing()
    session.exec(statement)  # type: ignore
    session.commit()


def insert_word_ladders(session: Session, word_scores: dict[str, int]) -> None:
    for word_length in range(3, 7):
        logger.info("Adding %s-letter word ladders", word_length)
        data: dict[str, LadderSet] = get_ladder_json(word_length=word_length)
        insert_word_ladder(data=data, word_scores=word_scores, session=session)
    logger.info("Done.")


def setup_ladders() -> None:
    with Session(engine) as session:
        word_scores: dict[str, int] = get_word_scores(session=session)
        insert_word_scores(session=session, word_scores=word_scores)
        insert_word_ladders(session=session, word_scores=word_scores)


if __name__ == "__main__":
    if not database_exists(engine.url):
        create_database(engine.url)
        SQLModel.metadata.create_all(engine)
    setup_dictionaries()
    setup_ladders()
