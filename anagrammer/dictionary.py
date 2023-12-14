from itertools import combinations
from typing import Sequence

from sqlalchemy import Row, select
from sqlmodel import Session


from anagrammer import models
from anagrammer.database import engine


class Dictionary:

    """This dictionary object will hold all of the words of dictionary in memory and provide some
    useful operations to get the desired word"""

    errorMessage = ""

    def __init__(self):
        self.words = set()
        self.words_by_length = {}
        self.conundrums_by_length = {}  # i.e. words with precisely one valid configuration
        self.words_by_anagram = {}
        self.load_dictionary()

    def load_dictionary(self):
        with Session(engine) as session:
            statement = select(models.Dictionary).where(
                models.Dictionary.dictionary == "sowpods"
            )
            rows: list[models.Dictionary] = session.execute(statement).all()
            for row in rows:
                word = row.Dictionary.word
                self.words.add(word)
                # get lists for words of specific length
                self.store_word_by_length(word)
                self.store_anagram(word)

    def store_anagram(self, word):
        sorted_word = "".join(sorted(word.lower()))
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
            for _, word in enumerate(words_of_length):
                word_anagrams = self.get_anagrams(word)
                if not word_anagrams:
                    conundrums.append(word)
            self.conundrums_by_length[length] = conundrums
        return conundrums

    def get_error_output(self):
        return self.errorMessage

    def get_dict_size(self):
        return len(self.words)

    def contains_word(self, word):
        return word in self.words

    def get_anagrams(self, input_word):
        input_word = input_word.lower()
        sorted_word = "".join(sorted(input_word))
        anagrams = self.words_by_anagram.get(sorted_word, set())
        return [word for word in anagrams if word != input_word]

    def get_sub_anagrams(self, original):
        anagrams = set()
        sorted_word = sorted(original.lower())

        for i in range(2, len(sorted_word) + 1):
            for subset in combinations(sorted_word, i):
                subset_word = "".join(subset)
                subset_anagrams = self.words_by_anagram.get(subset_word, [])
                anagrams.update(subset_anagrams)

        anagrams = sorted(anagrams, key=len, reverse=True)
        return anagrams


def get_anagrams(word: str, session: Session) -> list[str]:
    sorted_word = "".join(sorted(word.lower()))
    rows: Sequence[models.Dictionary] = session.exec(
        select(models.Dictionary)
        .where(models.Dictionary.sorted_word == sorted_word)
        .where(models.Dictionary.dictionary == "sowpods")
    ).all()
    return [row.Dictionary.word for row in rows if row.Dictionary.word != word]


def get_sub_anagrams(word: str, session: Session) -> list[str]:
    sorted_word: list[str] = sorted(word.lower())

    subsets: list[str] = []

    for i in range(2, len(sorted_word) + 1):
        for subset in combinations(sorted_word, i):
            subsets.append("".join(subset))

    rows: Sequence[Row] = session.exec(
        select(models.Dictionary)
        .where(models.Dictionary.sorted_word.in_(subsets))
        .where(models.Dictionary.dictionary == "sowpods")
    ).all()
    sub_anagrams: list[str] = [
        row.Dictionary.word for row in rows if row.Dictionary.word != word
    ]
    return sub_anagrams
