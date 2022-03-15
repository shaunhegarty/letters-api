import sys
import psycopg2 as psql
import logging
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
    '''Create dictionary tables and any others that may come up'''
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
        """
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
        dictionary_name = 'sowpods'
        cursor.execute("DELETE FROM DICTIONARY WHERE dictionary = %s", (dictionary_name, ))

        with open('dictionaries/sowpods.txt', 'r') as dictionary:

            cursor.execute(
                "prepare dictplan as "
                "insert into dictionary VALUES ($1, $2, $3)"
            )

            count = 0

            data = []
            for line in dictionary:
                count = count + 1
                word = line.rstrip().lstrip()
                data.append((word, dictionary_name, len(word)))

                if (count % 5000 == 0):
                    execute_batch(cursor, "execute dictplan (%s, %s, %s)", data)
                    data = []
                    logger.info("\rAdded %s, %i words inserted" % (word, count))
        execute_batch(cursor, "execute dictplan (%s, %s, %s)", data)
        data = []
        logger.info("\rAdded %s, %i words inserted" % (word, count))
    connection.commit()

    with connection.cursor() as cursor:
        with open('dictionaries/common.frequency.csv', 'r') as dictionary:
            dictionary_name = 'common'

            cursor.execute("DELETE FROM DICTIONARY WHERE dictionary = %s", (dictionary_name, ))

            count = 0
            data = []
            error_in_previous = False
            for line in dictionary:
                if error_in_previous:
                    logger.info("Couldn't Split line before %s", line)
                    error_in_previous = False
                count = count + 1
                try:
                    word = line.split()[0].rstrip().lstrip()
                    data.append((word, dictionary_name, len(word)))

                    if (count % 5000 == 0):
                        execute_batch(cursor, "execute dictplan (%s, %s, %s)", data)
                        data = []
                        logger.info("\rAdded %s, %i words inserted" % (word, count))
                except IndexError:
                    error_in_previous = True
                    logger.info("Couldn't Split %s", line)
        execute_batch(cursor, "execute dictplan (%s, %s, %s)", data)
        logger.info("\rAdded %s, %i words inserted" % (word, count))
    connection.commit()


with psql.connect(CONN_STRING) as conn:
    create_tables(conn)
    setup_dictionary(conn)
