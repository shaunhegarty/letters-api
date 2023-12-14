from functools import cache
from itertools import combinations
from typing import Sequence

from sqlalchemy import Row, select
from sqlmodel import Session, func

from anagrammer.models import Dictionary


@cache
def get_dict_size(dictionary: str, session: Session) -> int:
    row: Sequence[Dictionary] = session.exec(
        select(func.count(Dictionary.word).label("size")).where(
            Dictionary.dictionary == dictionary
        )
    ).first()
    return row.size


@cache
def contains_word(word: str, session: Session) -> bool:
    row: Sequence[Dictionary] = session.exec(
        select(Dictionary)
        .where(Dictionary.word == word)
        .where(Dictionary.dictionary == "sowpods")
    ).first()
    return bool(row)


@cache
def get_anagrams(word: str, session: Session) -> list[str]:
    sorted_word = "".join(sorted(word.lower()))
    rows: Sequence[Dictionary] = session.exec(
        select(Dictionary)
        .where(Dictionary.sorted_word == sorted_word)
        .where(Dictionary.dictionary == "sowpods")
    ).all()
    return [row.Dictionary.word for row in rows if row.Dictionary.word != word]


@cache
def get_sub_anagrams(word: str, session: Session) -> list[str]:
    sorted_word: list[str] = sorted(word.lower())

    subsets: list[str] = []

    for i in range(2, len(sorted_word) + 1):
        for subset in combinations(sorted_word, i):
            subsets.append("".join(subset))

    rows: Sequence[Row] = session.exec(
        select(Dictionary)
        .where(Dictionary.sorted_word.in_(subsets))
        .where(Dictionary.dictionary == "sowpods")
    ).all()
    sub_anagrams: list[str] = [
        row.Dictionary.word for row in rows if row.Dictionary.word != word
    ]
    return sub_anagrams


@cache
def get_conundrums(length: int, session: Session) -> list[str]:
    rows: Sequence[Row] = session.exec(
        select(func.string_agg(Dictionary.word, ",").label("word"))
        .where(Dictionary.word_length == length)
        .where(Dictionary.dictionary == "sowpods")
        .group_by(Dictionary.sorted_word)
        .having(func.count(Dictionary.sorted_word) == 1)
    ).all()
    return [row.word for row in rows]


@cache
def get_words_by_length(length: int, session: Session):
    rows: Sequence[Dictionary] = session.exec(
        select(Dictionary)
        .where(Dictionary.word_length == length)
        .where(Dictionary.dictionary == "sowpods")
    ).all()
    return [row.Dictionary.word for row in rows]
