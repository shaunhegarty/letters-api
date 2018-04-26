''' DB testing'''
import psycopg2 as psql
from psycopg2.extras import execute_batch
import sys
import connfig        

def create_tables(connection = None):
    if(connection == None):
        sys.stdout.write("No connection")
        return
    '''Create dictionary tables and any others that may come up'''
    commands = (
        """
        CREATE TABLE dictionary (
            word varchar(30) NOT NULL,
            dictionary varchar(30) NOT NULL,
            word_length int,
            PRIMARY KEY(word, dictionary)
        )
        """,
        """
        CREATE INDEX wordindex
        ON dictionary (word)
        """
    )

    try:
        CURSOR = connection.cursor()
        for command in commands:
            CURSOR.execute(command)
        CURSOR.close()
        connection.commit()
    except (Exception, psql.DatabaseError) as error:
        sys.stdout.write(str(error))

def setup_dictionary(connection = None):
    if(connection == None):
        sys.stdout.write("No connection")
        return
    
    try:
        CURSOR = connection.cursor()
        CURSOR.execute("DELETE FROM DICTIONARY")

        SOWPODS = open('sowpods.txt', 'r')
        DICTIONARY_NAME = 'sowpods'

        CURSOR.execute(
            "prepare dictplan as "
            "insert into dictionary VALUES ($1, $2, $3)"
        )

        count = 0
        # for line in SOWPODS:
        #     count = count + 1
        #     word = line.rstrip().lstrip()
        #     CURSOR.execute("execute dictplan (%s, %s, %s)",
        #                 (word, DICTIONARY_NAME, len(word)))
        #     if (count % 1000 == 0):
        #         sys.stdout.write("\rAdded %s, %i words inserted" % (word, count))
        #         sys.stdout.flush()

        data = []
        # insert__query = 'insert into dictionary (word, dictionary, word_length) values %s'
        for line in SOWPODS:
            count = count + 1
            word = line.rstrip().lstrip()
            data.append((word, DICTIONARY_NAME, len(word)))

            if (count % 5000 == 0):
                execute_batch(CURSOR, "execute dictplan (%s, %s, %s)", data)
                data = []
                sys.stdout.write("\rAdded %s, %i words inserted" % (word, count))
                sys.stdout.flush()
        execute_batch(CURSOR, "execute dictplan (%s, %s, %s)", data)
        data = []
        sys.stdout.write("\rAdded %s, %i words inserted" % (word, count))
        sys.stdout.flush()



        CURSOR.close()
        connection.commit()
    except (Exception, psql.DatabaseError) as error:
        sys.stdout.write(str(error))

try:
    CONN = psql.connect(connfig.conn_string)
    # create_tables(CONN)
    setup_dictionary(CONN)
# except (Exception) as error:
    # sys.stdout.write(str(error))
finally:
    if CONN is not None:
        CONN.close()