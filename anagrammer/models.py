from sqlalchemy import Column, String, Integer
from .database import Base


class Dictionary(Base):
    __tablename__ = "dictionary"

    word = Column(String(30), primary_key=True)
    dictionary = Column(String(30), primary_key=True)
    word_length = Column(Integer)
    frequency = Column(Integer, nullable=True)
    source = Column(String(60), nullable=True)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.word}"


class WordScore(Base):
    __tablename__ = "wordscore"

    word = Column(String(30), primary_key=True)
    dictionary = Column(String(30), primary_key=True)
    score = Column(Integer)

    def __str__(self):
        return f"{self.word}: Score: {self.score}"


class Ladder(Base):
    __tablename__ = "ladder"

    pair = Column(String(30), primary_key=True)
    dictionary = Column(String(30), primary_key=True)
    chain = Column(String(300))
    length = Column(Integer)
    difficulty = Column(Integer, nullable=True)
    hardest_word_score = Column(Integer, nullable=True)
    hardest_word = Column(String(30), nullable=True)
    variations = Column(Integer)
    variant = Column(Integer, primary_key=True)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        variations_string = f"{self.variant} of {self.variations}."
        difficulty_string = f"Difficulty: {self.difficulty}."
        return f"{self.pair}: [{self.chain}]. {variations_string} {difficulty_string}"
