from sqlalchemy import Column, String, Integer
from .database import Base


class Dictionary(Base):
    __tablename__ = "dictionary"

    word = Column(String(30), primary_key=True)
    dictionary = Column(String(30), primary_key=True)
    word_length = Column(Integer)
    frequency = Column(Integer, nullable=True)
    source = Column(String(60), nullable=True)

    def __str__(self):
        return f"{self.word}"
