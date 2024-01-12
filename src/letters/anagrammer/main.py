from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from random import randint
from typing import Any, Generator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlmodel import Session, SQLModel

from letters.anagrammer.database import engine
from letters.anagrammer.models import (
    Anagrams,
    SubAnagrams,
    ValidatedWord,
    WordLadderOptions,
)

from . import dictionary, ladder

logger = logging.getLogger(__name__)


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:  # noqa: ARG001
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def hello() -> dict[str, str]:
    return {"greeting": "hello"}


@app.get("/anagrams/{word}")
def get_anagrams(word: str, session: Session = Depends(get_session)) -> list[str]:
    return dictionary.get_anagrams(word, session)


@app.get("/subanagrams/{word}")
def get_sub_anagrams(
    word: str,
    best_only: bool = False,  # noqa: FBT001, FBT002
    session: Session = Depends(get_session),
) -> SubAnagrams:
    anagrams: list[str] = dictionary.get_sub_anagrams(word, session)
    anagrams = sorted(anagrams, key=len, reverse=True)
    max_len = len(anagrams[0])  # longest first so this is the max

    sub_anagrams: dict[int, Anagrams] = {}
    for anagram in anagrams:
        if best_only and len(anagram) != max_len:
            break
        sub: Anagrams = sub_anagrams.get(len(anagram), Anagrams())
        sub.words.append(anagram)
        sub.count = len(sub.words)
        sub_anagrams[len(anagram)] = sub
    return SubAnagrams(max=max_len, words=sub_anagrams)


@app.get("/validate/{word}")
def get_valid(word: str, session: Session = Depends(get_session)) -> ValidatedWord:
    dict_name = "sowpods"
    return ValidatedWord(
        word=word,
        dictionary=dict_name,
        dictionary_size=dictionary.get_dict_size(dict_name, session),
        valid=dictionary.contains_word(word, session),
    )


@app.get("/conundrum/{length}")
def get_conundrums(length: int, session: Session = Depends(get_session)) -> list[str]:
    return dictionary.get_conundrums(length, session)


@app.get("/conundrum/{length}/random")
def get_random_conundrum(length: int, session: Session = Depends(get_session)) -> str:
    conundra = dictionary.get_conundrums(length, session)
    index = randint(0, len(conundra) - 1)  # noqa: S311
    return conundra[index]


@app.get("/words/{length}")
def words(length: int, session: Session = Depends(get_session)) -> list[str]:
    return dictionary.get_words_by_length(length, session)


@app.get("/ladders/{word_length:int}")
def word_ladders_by_length(
    word_length: int, session: Session = Depends(get_session)
) -> ladder.LadderJSON:
    return ladder.get_easy_ladders_by_word_length(session, word_length)


@app.get("/ladders/{word_pair:str}")
def word_ladder(
    word_pair: str, session: Session = Depends(get_session)
) -> dict[str, Any]:
    return ladder.get_word_ladder_for_word_pair(word_pair, session)


@app.get("/ladders/{difficulty_class}/{word_length}")
def word_ladders_by_difficulty_and_length(
    difficulty_class: int, word_length: int, session: Session = Depends(get_session)
) -> ladder.LadderJSON:
    return ladder.get_ladders_by_difficulty_class(
        session=session, word_length=word_length, difficulty_class=[difficulty_class]
    )


@app.post("/ladders/search/")
def word_ladder_from_options(
    options: WordLadderOptions, session: Session = Depends(get_session)
) -> ladder.LadderJSON:
    return ladder.search_ladders(options, session)


@app.get("/ladders/words/{word_dictionary}/{length}")
def word_scores(
    word_dictionary: str, length: int, session: Session = Depends(get_session)
) -> dict[str, int]:
    return ladder.get_words_and_scores(
        word_dictionary, word_length=length, session=session
    )


@app.get("/ladders/random/{difficulty_class}/{length}")
def random_ladder(
    difficulty_class: int, length: int, session: Session = Depends(get_session)
) -> dict[str, Any]:
    upper, lower = difficulty_class * 10000, (difficulty_class - 1) * 10000
    return ladder.get_random_ladder_in_difficulty_range(
        session=session, word_length=length, upper_bound=upper, lower_bound=lower
    )
