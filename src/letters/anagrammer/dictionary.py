from __future__ import annotations

from functools import cache
from itertools import combinations
from typing import Sequence

from sqlmodel import Session, func, select

from letters.anagrammer.models import Dictionary


@cache
def get_dict_size(dictionary: str, session: Session) -> int:
    size: int | None = session.exec(
        select(func.count(Dictionary.word).label("size")).where(
            Dictionary.dictionary == dictionary
        )
    ).first()
    return size or 0


@cache
def contains_word(word: str, session: Session) -> bool:
    row: Dictionary | None = session.exec(
        select(Dictionary)
        .where(Dictionary.word == word.lower())
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
    return [row.word for row in rows if row.word != word]


@cache
def get_sub_anagrams(word: str, session: Session) -> list[str]:
    sorted_word: list[str] = sorted(word.lower())

    subsets: list[str] = []

    subsets = [
        "".join(subset)
        for i in range(2, len(sorted_word) + 1)
        for subset in combinations(sorted_word, i)
    ]

    rows: Sequence[Dictionary] = session.exec(
        select(Dictionary)
        .where(Dictionary.sorted_word.in_(subsets))  # mypy: type: ignore
        .where(Dictionary.dictionary == "sowpods")
    ).all()
    sub_anagrams: list[str] = [row.word for row in rows if row.word != word]
    return sub_anagrams


@cache
def get_conundrums(length: int, session: Session) -> list[str]:
    rows: Sequence[str] = session.exec(
        select(func.string_agg(Dictionary.word, ",").label("word"))
        .where(Dictionary.word_length == length)
        .where(Dictionary.dictionary == "sowpods")
        .group_by(Dictionary.sorted_word)
        .having(func.count(Dictionary.sorted_word) == 1)
    ).all()
    return list(rows)


@cache
def get_words_by_length(length: int, session: Session) -> list[str]:
    rows: Sequence[Dictionary] = session.exec(
        select(Dictionary)
        .where(Dictionary.word_length == length)
        .where(Dictionary.dictionary == "sowpods")
    ).all()
    return [row.word for row in rows]
