import logging

from fastapi import FastAPI
from sqlalchemy.exc import ProgrammingError

from anagrammer.models import WordLadderOptions

from . import dictionary, ladder

logger = logging.getLogger(__name__)


try:
    d = dictionary.Dictionary()
except ProgrammingError:
    logger.warning("Database not set up")


app = FastAPI()


@app.get("/")
async def hello():
    return {"greeting": "hello"}


@app.get("/anagrams/{word}")
def get_anagrams(word):
    anagrams = d.get_anagrams(word)
    return anagrams


@app.get("/subanagrams/{word}")
def get_sub_anagrams(word: str, best_only: bool = False):
    anagrams = d.get_sub_anagrams(word)
    max_len = len(anagrams[0])  # longest first so this is the max

    sub_anagrams = {}
    for anagram in anagrams:
        if best_only and len(anagram) != max_len:
            break
        sub = sub_anagrams.get(len(anagram), {})
        sub_words = sub.get("words", [])
        sub_words.append(anagram)
        sub["words"] = sub_words
        sub["count"] = len(sub_words)
        sub_anagrams[len(anagram)] = sub
    return {"max": max_len, "words": sub_anagrams}


@app.get("/validate/{word}")
def get_valid(word: str):
    return {
        "dictionary": "sowpods",
        "dictionary_size": d.get_dict_size(),
        "valid": d.contains_word(word),
    }


@app.get("/conundrum/{length}")
def get(length: int):
    return d.get_conundrums(length)


@app.get("/words/{length}")
def words(length: int):
    return d.get_words_by_length(length)


@app.get("/ladders/{word_pair}")
def word_ladder(word_pair: str):
    return ladder.get_word_ladder_for_word_pair(word_pair)


@app.get("/ladders/{word_length}")
def word_ladders_by_length(word_length: int):
    return ladder.get_easy_ladders_by_word_length(word_length)


@app.get("/ladders/{difficulty_class}/{word_length}")
def word_ladders_by_difficulty_and_length(difficulty_class: int, word_length: int):
    return ladder.get_ladders_by_difficulty_class(
        word_length=word_length, difficulty_class=difficulty_class
    )


@app.post("/ladders/search/")
def word_ladder_from_options(options: WordLadderOptions):
    return ladder.search_ladders(options)


@app.get("/ladders/words/{word_dictionary}/{length}")
def word_scores(word_dictionary, length):
    return ladder.get_words_and_scores(word_dictionary, word_length=length)


@app.get("/ladders/random/{difficulty_class}/{length}")
def random_ladder(difficulty_class: int, length: int):
    upper, lower = difficulty_class * 10000, (difficulty_class - 1) * 10000
    return ladder.get_random_ladder_in_difficulty_range(
        word_length=length, upper_bound=upper, lower_bound=lower
    )