import psycopg2 as psql
from anagrammer import letters
from config.config import CONN_STRING


def binary_search(search_list, target):
    word = target.lower()
    minimum = 0
    maximum = len(search_list) - 1
    while minimum <= maximum:
        current_index = (minimum + maximum) // 2
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
        self.words_by_length = {}
        self.conundrums_by_length = {} # i.e. words with precisely one valid configuration
        self.words_by_anagram = {}
        self.load_dictionary()

    def load_dictionary(self):
        with psql.connect(CONN_STRING).cursor() as cursor:            
            cursor.execute("SELECT WORD FROM DICTIONARY")
            rows = cursor.fetchall()
            for row in rows:
                word = row[0]
                self.words.append(word)
                # get lists for words of specific length
                self.store_word_by_length(word)
                self.store_anagram(word)

    def store_anagram(self, word):
        sorted_word = ''.join(sorted(word.lower()))
        anagram_list = self.words_by_anagram.get(sorted_word, [])
        anagram_list.append(word)
        self.words_by_anagram[sorted_word] = anagram_list

    def store_word_by_length(self, word):
        len_words = self.words_by_length.get(len(word), [])
        len_words.append(word)
        self.words_by_length[len(word)] = len_words
    
    def get_words_by_length(self, length):
        return self.words_by_length.get(length, [])

    def get_conundrums(self, length):
        conundrums = self.conundrums_by_length.get(length, [])
        if len(conundrums) == 0:
            words_of_length = self.words_by_length.get(length, [])
            for index, word in enumerate(words_of_length):
                word_anagrams = self.get_anagrams(word)
                if not len(word_anagrams):
                    conundrums.append(word)
            self.conundrums_by_length[length] = conundrums
        return conundrums

    def get_error_output(self):
        return self.errorMessage

    def get_dict_size(self):
        return len(self.words)

    def contains_word(self, word):
        return binary_search(self.words, word)

    def get_anagrams(self, input_word):
        input_word = input_word.lower()
        sorted_word = ''.join(sorted(input_word))
        anagrams = self.words_by_anagram.get(sorted_word, [])
        return [word for word in anagrams if word != input_word]

    def get_sub_anagrams(self, original):
        anagrams = []
        for word in self.words:
            if (word != original) and letters.is_sub_anagram(word, original):
                anagrams.append(word)

        anagrams = sorted(anagrams, key=len, reverse=True)
        return anagrams




