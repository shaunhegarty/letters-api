''' DB testing'''
import sys 
import psycopg2 as psql
import logging
from psycopg2.extras import execute_batch
from config import CONN_STRING

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

def create_tables(connection = None):
    if(connection == None):
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

def setup_dictionary(connection = None):
    if(connection == None):
        logger.error("No connection")
        return
    

    with connection.cursor() as CURSOR:
        CURSOR.execute("DELETE FROM DICTIONARY")

        with open('sowpods.txt', 'r') as SOWPODS:
            DICTIONARY_NAME = 'sowpods'

            CURSOR.execute(
                "prepare dictplan as "
                "insert into dictionary VALUES ($1, $2, $3)"
            )

            count = 0

            data = []        
            for line in SOWPODS:
                count = count + 1
                word = line.rstrip().lstrip()
                data.append((word, DICTIONARY_NAME, len(word)))

                if (count % 5000 == 0):
                    execute_batch(CURSOR, "execute dictplan (%s, %s, %s)", data)
                    data = []
                    logger.info("\rAdded %s, %i words inserted" % (word, count))
        execute_batch(CURSOR, "execute dictplan (%s, %s, %s)", data)
        data = []
        logger.info("\rAdded %s, %i words inserted" % (word, count))        
    connection.commit()


with psql.connect(CONN_STRING) as conn:
    create_tables(conn)
    setup_dictionary(conn)