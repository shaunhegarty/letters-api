import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
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
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def hello():
    return {"greeting": "hello"}


@app.get("/anagrams/{word}")
def get_anagrams(word: str, session: Session = Depends(get_session)):
    return dictionary.get_anagrams(word, session)


@app.get("/subanagrams/{word}")
def get_sub_anagrams(
    word: str, best_only: bool = False, session: Session = Depends(get_session)
) -> dict[str, Any]:
    anagrams: list[str] = dictionary.get_sub_anagrams(word, session)
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
def get_valid(word: str, session: Session = Depends(get_session)):
    dict_name = "sowpods"
    return {
        "dictionary": dict_name,
        "dictionary_size": dictionary.get_dict_size(dict_name, session),
        "valid": dictionary.contains_word(word, session),
    }


@app.get("/conundrum/{length}")
def get(length: int, session: Session = Depends(get_session)):
    return dictionary.get_conundrums(length, session)


@app.get("/words/{length}")
def words(length: int, session: Session = Depends(get_session)):
    return dictionary.get_words_by_length(length, session)


@app.get("/ladders/{word_length:int}")
def word_ladders_by_length(word_length: int, session: Session = Depends(get_session)):
    return ladder.get_easy_ladders_by_word_length(session, word_length)


@app.get("/ladders/{word_pair:str}")
def word_ladder(word_pair: str, session: Session = Depends(get_session)):
    return ladder.get_word_ladder_for_word_pair(word_pair, session)


@app.get("/ladders/{difficulty_class}/{word_length}")
def word_ladders_by_difficulty_and_length(
    difficulty_class: int, word_length: int, session: Session = Depends(get_session)
):
    return ladder.get_ladders_by_difficulty_class(
        session=session, word_length=word_length, difficulty_class=[difficulty_class]
    )


@app.post("/ladders/search/")
def word_ladder_from_options(
    options: WordLadderOptions, session: Session = Depends(get_session)
):
    return ladder.search_ladders(options, session)


@app.get("/ladders/words/{word_dictionary}/{length}")
def word_scores(
    word_dictionary: str, length: int, session: Session = Depends(get_session)
):
    return ladder.get_words_and_scores(
        word_dictionary, word_length=length, session=session
    )


@app.get("/ladders/random/{difficulty_class}/{length}")
def random_ladder(
    difficulty_class: int, length: int, session: Session = Depends(get_session)
):
    upper, lower = difficulty_class * 10000, (difficulty_class - 1) * 10000
    return ladder.get_random_ladder_in_difficulty_range(
        session=session, word_length=length, upper_bound=upper, lower_bound=lower
    )
