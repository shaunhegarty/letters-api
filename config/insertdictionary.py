import sys
import logging
import json
import requests

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from anagrammer import models
from anagrammer.database import engine

# Build database based on schema defined in models
models.Base.metadata.create_all(bind=engine)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def setup_dictionaries():
    with Session(engine) as session:
        logger.info("Reading Common Words (with frequencies)")
        with open(
            "dictionaries/common.frequency.csv", "r", encoding="utf-8"
        ) as dictionary:
            source = "wikipedia-word-frequency-list-2019"
            values = []
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
                    }
                )
            statement = (
                insert(models.Dictionary).values(values).on_conflict_do_nothing()
            )
            logger.info("Inserting Common Words (with frequencies) into database.")
            session.execute(statement)
            session.commit()
            logger.info("Done.")

        logger.info("Reading SOWPODS dictionary")
        with open("dictionaries/sowpods.txt", "r", encoding="utf-8") as dictionary:
            values = []
            for word in dictionary:
                word = word.strip()
                values.append(
                    {
                        "word": word,
                        "word_length": len(word),
                        "dictionary": "sowpods",
                    }
                )
            statement = (
                insert(models.Dictionary).values(values).on_conflict_do_nothing()
            )
            logger.info("Inserting SOWPODS Words into database.")
            session.execute(statement)
            session.commit()
            logger.info("Done.")


def get_ladder_json(word_length):
    assert 3 <= word_length <= 6

    response = requests.get(
        f"https://raw.githubusercontent.com/shaunhegarty/word-ladder/master/wordladder/resources/ladder-common-{word_length}.json"
    )
    data = json.loads(response.content.decode("utf-8"))
    return data


def sort_word_pair(pair):
    return "-".join(sorted(pair.split("-")))


def ladder_difficulty(ladder, word_scores):
    word_score = 0
    for word in ladder:
        word_score += word_scores.get(word)
    return word_score


def get_word_scores():

    with Session(engine) as session:
        results = (
            session.query(
                models.Dictionary,
                func.rank().over(order_by=models.Dictionary.frequency.desc()),
            )
            .filter(models.Dictionary.dictionary == "common")
            .all()
        )
        word_scores = {word.word: rank for word, rank in results}
    return word_scores


def insert_word_scores(word_scores):
    with Session(engine) as session:
        # Populate Word Score
        values = []
        for word, word_score in word_scores.items():
            values.append({"word": word, "dictionary": "common", "score": word_score})
        statement = insert(models.WordScore).values(values).on_conflict_do_nothing()
        session.execute(statement)
        session.commit()


def insert_word_ladders(word_scores):
    for word_length in range(3, 7):
        logger.info("Adding %s-letter word ladders", word_length)
        data = get_ladder_json(word_length=word_length)
        unique_ladder_keys = {sort_word_pair(pair) for pair in data.keys()}

        logger.debug("%s ladder keys", len(unique_ladder_keys))
        values = []
        for key in unique_ladder_keys:
            ladder_list = data.get(key)
            for index, ladder in enumerate(ladder_list):
                values.append(
                    {
                        "pair": key,
                        "dictionary": "common",
                        "chain": ",".join(ladder),
                        "difficulty": ladder_difficulty(ladder, word_scores),
                        "variations": len(ladder_list),
                        "variant": index,
                    }
                )
        logger.debug("Updating Database with %s records", len(values))
        with Session(engine) as session:
            statement = insert(models.Ladder).values(values).on_conflict_do_nothing()
            session.execute(statement)
            session.commit()
    logger.info("Done.")     


def setup_ladders():
    word_scores = get_word_scores()
    insert_word_scores(word_scores=word_scores)
    insert_word_ladders(word_scores=word_scores)


setup_dictionaries()
setup_ladders()
