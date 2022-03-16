import sys
import logging

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
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


setup_dictionaries()
