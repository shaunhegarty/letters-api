import sys
import logging
import psycopg2 as psql
from psycopg2.extras import execute_batch
from config import CONN_STRING

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def create_tables(connection=None):
    if connection is None:
        logger.error("No connection")
        return

    # Create dictionary tables and any others that may come up
    commands = (
        """
        CREATE TABLE if not exists dictionary (
            word varchar(30) NOT NULL,
            dictionary varchar(30) NOT NULL,
            word_length int,
            PRIMARY KEY(word, dictionary)
        )
        """,
        """
        CREATE INDEX if not exists wordindex
        ON dictionary (word)
        """,
        """
        CREATE TABLE if not exists word_frequency (
            word varchar(30) NOT NULL,
            frequency int,
            source varchar(60) NOT NULL,
            PRIMARY KEY(word, frequency)
        )
        """,
        """
        CREATE INDEX if not exists wordfreq_index
        ON word_frequency (word)
        """,
    )

    with connection.cursor() as CURSOR:
        for command in commands:
            CURSOR.execute(command)
    connection.commit()


def setup_dictionary(connection=None):
    if connection is None:
        logger.error("No connection")
        return

    with connection.cursor() as cursor:
        add_dictionary(
            cursor, "dictionaries/sowpods.txt", "sowpods", word_func=lambda x: x
        )

    with connection.cursor() as cursor:
        add_dictionary(
            cursor,
            "dictionaries/common.frequency.csv",
            "common",
            word_func=lambda x: x.split()[0],
        )

    with connection.cursor() as cursor:
        logger.info("\r------ Adding word frequencies -------")
        with open(
            "dictionaries/common.frequency.csv", "r", encoding="utf-8"
        ) as dictionary:

            cursor.execute(
                "prepare dictplan as "
                "insert into word_frequency VALUES ($1, $2, $3) ON CONFLICT DO NOTHING"
            )

            count = 0
            data = []
            for line in dictionary:
                count = count + 1
                word, frequency = line.split()
                word = word.rstrip().lstrip()
                frequency = int(frequency)
                data.append((word, frequency, "wikipedia-word-frequency-list-2019"))

                if count % 5000 == 0:
                    execute_batch(cursor, "execute dictplan (%s, %s, %s)", data)
                    data = []
                    logger.info("\rAdded %s, %i words inserted", word, count)
        execute_batch(cursor, "execute dictplan (%s, %s, %s)", data)
        logger.info("\rAdded %s, %i words inserted", word, count)
    connection.commit()


def add_dictionary(cursor, file_loc, dict_name, word_func):
    dictionary_name = dict_name
    logger.info("\r------ Adding dictionary: %s -------", dict_name)

    with open(file_loc, "r", encoding="utf-8") as dictionary:
        plan = f"{dictionary_name}plan"
        cursor.execute(
            f"prepare {plan} as "
            "insert into dictionary VALUES ($1, $2, $3) ON CONFLICT DO NOTHING"
        )

        count = 0

        data = []
        for line in dictionary:
            count = count + 1
            word = word_func(line).rstrip().lstrip()
            data.append((word, dictionary_name, len(word)))

            if count % 10000 == 0:
                execute_batch(cursor, f"execute {plan} (%s, %s, %s)", data)
                data = []
                logger.info("\rAdded %s, %i words inserted", word, count)
    execute_batch(cursor, f"execute {plan} (%s, %s, %s)", data)
    logger.info("\rAdded %s, %i words inserted", word, count)


with psql.connect(CONN_STRING) as conn:
    create_tables(conn)
    setup_dictionary(conn)
