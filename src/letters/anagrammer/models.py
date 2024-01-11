from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


class Dictionary(SQLModel, table=True):
    word: str = Field(primary_key=True)
    dictionary: str = Field(primary_key=True)
    sorted_word: str = Field(index=True)
    word_length: int
    frequency: Optional[int]
    source: Optional[str]

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.word}"


class WordScore(SQLModel, table=True):
    word: str = Field(primary_key=True)
    dictionary: str = Field(primary_key=True)
    score: int

    def __str__(self) -> str:
        return f"{self.word}: Score: {self.score}"


class Ladder(SQLModel, table=True):
    pair: str = Field(primary_key=True)
    dictionary: str = Field(primary_key=True)
    variant: int = Field(primary_key=True)
    chain: str
    length: int
    difficulty: Optional[int]
    hardest_word_score: Optional[int]
    hardest_word: Optional[str]
    variations: Optional[int]

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        variations_string = f"{self.variant} of {self.variations}."
        difficulty_string = f"Difficulty: {self.difficulty}."
        return f"{self.pair}: [{self.chain}]. {variations_string} {difficulty_string}"


class WordLadderOptions(SQLModel):
    ladder_filter: Optional[str]
    difficulty: list[int] = Field(default=[1])
    length: list[int] = Field(default=[3])
    page_size: int = 200


class ValidatedWord(SQLModel):
    word: str
    dictionary: str
    dictionary_size: int
    valid: bool


class Anagrams(SQLModel):
    words: list[str] = Field(default=[])
    count: int = 0


class SubAnagrams(SQLModel):
    max: int  # noqa: A003
    words: dict[int, Anagrams]
