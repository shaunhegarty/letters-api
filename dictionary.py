import psycopg2 as psql
import sys
import letters
from config import CONN_STRING


def binary_search(search_list, target):
    word = target.lower()
    minimum = 0
    maximum = len(search_list) - 1
    while minimum <= maximum:
        current_index = (minimum + maximum) / 2
        if search_list[current_index] < word:
            minimum = current_index + 1
        elif search_list[current_index] > word:
            maximum = current_index - 1
        else:
            return True

    return False


class Dictionary(object):

    """ This dictionary object will hold all of the words of dictionary in memory and provide some useful operations
    to get the desired word """
    errorMessage = ""

    def __init__(self):
        self.words = []
        self.load_dictionary()

    def load_dictionary(self):
        with psql.connect(CONN_STRING).cursor() as cursor:            
            cursor.execute("SELECT WORD FROM DICTIONARY")
            rows = cursor.fetchall()
            for row in rows:
                self.words.append(row[0])    

    def get_error_output(self):
        return self.errorMessage

    def get_dict_size(self):
        return len(self.words)

    def contains_word(self, word):
        return binary_search(self.words, word)

    def get_anagrams(self, original):
        anagrams = []
        for word in self.words:
            if (word != original) and letters.is_anagram(word, original):
                anagrams.append(word)

        return anagrams

    def get_sub_anagrams(self, original):
        anagrams = []
        for word in self.words:
            if (word != original) and letters.is_sub_anagram(word, original):
                anagrams.append(word)

        anagrams = sorted(anagrams, key=len, reverse=True)
        return anagrams
