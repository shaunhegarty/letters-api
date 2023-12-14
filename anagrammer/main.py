import logging
from contextlib import asynccontextmanager
from functools import cache
from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy.exc import ProgrammingError
from sqlmodel import Session, SQLModel

from anagrammer.database import engine
from anagrammer.models import WordLadderOptions

from . import dictionary, ladder

logger = logging.getLogger(__name__)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    get_dictionary()
    yield


app = FastAPI(lifespan=lifespan)


@cache
def get_dictionary():
    try:
        d = dictionary.Dictionary()
    except ProgrammingError as e:
        logger.exception(e)
        logger.warning("\n------\nDatabase not set up\n------\n")
    return d


@app.get("/")
async def hello():
    return {"greeting": "hello"}


@app.get("/anagrams/{word}")
def get_anagrams(word: str, session: Session = Depends(get_session)):
    from anagrammer.dictionary import get_anagrams

    return get_anagrams(word, session)


@app.get("/subanagrams/{word}")
def get_sub_anagrams(
    word: str, best_only: bool = False, session: Session = Depends(get_session)
) -> dict[str, Any]:
    from anagrammer.dictionary import get_sub_anagrams

    anagrams: list[str] = get_sub_anagrams(word, session)
    anagrams = sorted(anagrams, key=len, reverse=True)
    max_len = len(anagrams[0])  # longest first so this is the max

    sub_anagrams: dict[int, dict[str, Any]] = {}
    for anagram in anagrams:
        if best_only and len(anagram) != max_len:
            break
        sub: dict[str, Any] = sub_anagrams.get(len(anagram), {})
        sub_words: list[str] = sub.get("words", [])
        sub_words.append(anagram)
        sub["words"] = sub_words
        sub["count"] = len(sub_words)
        sub_anagrams[len(anagram)] = sub
    return {"max": max_len, "words": sub_anagrams}


@app.get("/validate/{word}")
def get_valid(word: str):
    d = get_dictionary()
    return {
        "dictionary": "sowpods",
        "dictionary_size": d.get_dict_size(),
        "valid": d.contains_word(word),
    }


@app.get("/conundrum/{length}")
def get(length: int):
    d = get_dictionary()
    return d.get_conundrums(length)


@app.get("/words/{length}")
def words(length: int):
    d = get_dictionary()
    return d.get_words_by_length(length)


@app.get("/ladders/{word_length:int}")
def word_ladders_by_length(word_length: int, session: Session = Depends(get_session)):
    return ladder.get_easy_ladders_by_word_length(session, word_length)


@app.get("/ladders/{word_pair:str}")
def word_ladder(word_pair: str):
    return ladder.get_word_ladder_for_word_pair(word_pair)


@app.get("/ladders/{difficulty_class}/{word_length}")
def word_ladders_by_difficulty_and_length(
    difficulty_class: int, word_length: int, session: Session = Depends(get_session)
):
    return ladder.get_ladders_by_difficulty_class(
        session=session, word_length=word_length, difficulty_class=[difficulty_class]
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
