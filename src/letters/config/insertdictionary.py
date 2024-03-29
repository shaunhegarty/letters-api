from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import requests
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, col, select
from tqdm import tqdm

from letters.anagrammer import models
from letters.anagrammer.database import engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def load_common(session: Session, limit: int = 0) -> None:
    with Path("dictionaries/common.frequency.csv").open(encoding="utf-8") as dictionary:
        source = "wikipedia-word-frequency-list-2019"
        values = []
        count = 0
        for line in dictionary:
            word, frequency = line.split()
            word = word.strip()
            values.append(
                {
                    "word": word,
                    "frequency": int(frequency),
                    "word_length": len(word),
                    "dictionary": "common",
                    "source": source,
                    "sorted_word": "".join(sorted(word.lower())),
                },
            )
            count += 1
            if limit != 0 and count >= limit:
                break
        statement = insert(models.Dictionary).values(values).on_conflict_do_nothing()
        logger.info("Inserting Common Words (with frequencies) into database.")
        session.exec(statement)  # mypy: type: ignore
        session.commit()


def load_sowpods(session: Session, limit: int = 0) -> None:
    with Path("dictionaries/sowpods.txt").open(encoding="utf-8") as dictionary:
        values = []
        count = 0
        for word in dictionary:
            trimmed_word = word.strip()
            values.append(
                {
                    "word": trimmed_word,
                    "word_length": len(trimmed_word),
                    "dictionary": "sowpods",
                    "sorted_word": "".join(sorted(trimmed_word.lower())),
                },
            )
            count += 1
            if limit != 0 and count >= limit:
                break

        logger.info("Inserting SOWPODS Words into database.")
        statement = insert(models.Dictionary).values(values).on_conflict_do_nothing()
        session.exec(statement)  # mypy: type: ignore
        session.commit()


def setup_dictionaries() -> None:
    with Session(engine) as session:
        logger.info("Reading Common Words (with frequencies)")
        load_common(session=session)
        logger.info("Done.")

        logger.info("Reading SOWPODS dictionary")
        load_sowpods(session=session)
        logger.info("Done.")


Ladder = list[str]
LadderSet = list[Ladder]

MIN_WORD_LENGTH = 3
MAX_WORD_LENGTH = 6


def get_ladder_json(word_length: int) -> dict[str, LadderSet]:
    if MIN_WORD_LENGTH <= word_length <= MAX_WORD_LENGTH:
        msg = "Word length must be between 3 and 6"
        raise ValueError(msg)

    response = requests.get(
        f"https://raw.githubusercontent.com/shaunhegarty/word-ladder/master/wordladder/resources/ladder-common-{word_length}.json",
        timeout=10,
    )
    return json.loads(response.content.decode("utf-8"))


def get_ladder_json_from_file(filename: Path) -> dict[str, LadderSet]:
    with Path(filename).open(encoding="utf-8") as f:
        return json.load(f)


def sort_word_pair(pair: str) -> str:
    return "-".join(sorted(pair.split("-")))


def ladder_difficulty(ladder: Ladder, word_scores: dict[str, int]) -> int:
    word_score = 0
    for word in ladder:
        word_score += word_scores[word]
    return word_score


def get_hardest_word(ladder: Ladder, word_scores: dict[str, int]) -> tuple[str, int]:
    hardest_word_score: int = 0
    hardest_word: str = ""
    for word in ladder:
        word_score = word_scores.get(word, 0)
        if word_score > hardest_word_score:
            hardest_word_score = word_score
            hardest_word = word
    return hardest_word, hardest_word_score


def get_word_scores(session: Session) -> dict[str, int]:
    """Rank the words by frequency and assign it as a score."""
    results = session.exec(
        select(
            models.Dictionary,
            func.rank().over(order_by=col(models.Dictionary.frequency).desc()),
        ).where(models.Dictionary.dictionary == "common"),
    ).all()
    return {word.word: rank for word, rank in results}


def insert_word_scores(session: Session, word_scores: dict[str, int]) -> None:
    # Populate Word Score
    values = []
    for word, word_score in word_scores.items():
        values.append({"word": word, "dictionary": "common", "score": word_score})
    statement = insert(models.WordScore).values(values).on_conflict_do_nothing()
    session.exec(statement)  # mypy: type: ignore
    session.commit()


class LadderAdder:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.word_scores = get_word_scores(session=session)
        self.values: list[dict] = []
        self.insert_count = 0
        self.progress_bar = None
        self.files_to_move = []

    def insert_from_files(self, load_path: Path) -> None:
        if load_path.is_dir():
            file_list = [
                file for file in load_path.iterdir() if "ladders.json" in file.name
            ]
            batch_size = 10000
            self.progress_bar = tqdm(
                file_list, desc="Loading Ladders", total=len(file_list)
            )
            for file in file_list:
                self.gather_from_file(file)
                self.progress_bar.update(1)
                self.progress_bar.set_description(f"Processing {file.name}")
                self.files_to_move.append(file)
                if len(self.values) > batch_size:
                    self.progress_bar.set_description(
                        f"Inserting {len(self.values)} rows"
                    )
                    self.insert_values()
                    self.move_processed_files()
        else:
            with load_path.open(encoding="utf-8") as file:
                data = json.load(file)
                self.gather_values(data=data)
                self.insert_values()

    def move_processed_files(self) -> None:
        for file in self.files_to_move:
            processed_path = file.parent / "processed"
            processed_path.mkdir(exist_ok=True)
            file.rename(processed_path / file.name)
        self.files_to_move = []

    def insert_values(self) -> None:
        count = len(self.values)
        statement = insert(models.Ladder).values(self.values).on_conflict_do_nothing()
        self.session.exec(statement)
        self.session.commit()
        self.values = []
        self.insert_count += count
        self.progress_bar.write(f"Inserted {self.insert_count} Ladders")

    def gather_from_file(self, path: Path) -> None:
        with Path(path).open(encoding="utf-8") as file:
            data: dict[str, list[list[str]]] = json.load(file)
            self.gather_values(data=data)

    def gather_values(self, data: dict[str, LadderSet]) -> None:
        if len(data) == 0:
            return

        if isinstance(next(iter(data.values()))[0], dict):
            self.gather_values_new(data)
        else:
            self.gather_values_old(data)

    def gather_values_old(self, data: dict[str, LadderSet]) -> None:
        unique_ladder_keys: set[str] = {sort_word_pair(pair) for pair in data}

        logger.debug("%s ladder keys", len(unique_ladder_keys))
        values: list[dict] = []
        for key in unique_ladder_keys:
            ladder_list: LadderSet = data[key]
            for index, ladder in enumerate(ladder_list):
                hardest_word, hardest_word_score = get_hardest_word(
                    ladder, self.word_scores
                )
                values.append(
                    {
                        "pair": key,
                        "dictionary": "common",
                        "chain": ",".join(ladder),
                        "length": len(ladder),
                        "difficulty": ladder_difficulty(ladder, self.word_scores),
                        "hardest_word": hardest_word,
                        "hardest_word_score": hardest_word_score,
                        "variations": len(ladder_list),
                        "variant": index + 1,
                    },
                )

    def gather_values_new(self, data: dict[str, LadderSet]) -> None:
        for key, ladder_list in data.items():
            for index, ladder_dict in enumerate(ladder_list):
                ladder = ladder_dict["path"]
                hardest_word, hardest_word_score = get_hardest_word(
                    ladder, self.word_scores
                )
                self.values.append(
                    {
                        "pair": key,
                        "dictionary": "common",
                        "chain": ",".join(ladder),
                        "length": len(ladder),
                        "difficulty": ladder_difficulty(ladder, self.word_scores),
                        "hardest_word": hardest_word,
                        "hardest_word_score": hardest_word_score,
                        "variations": len(ladder_list),
                        "variant": index + 1,
                    },
                )


def insert_word_ladder(
    data: dict[str, LadderSet],
    word_scores: dict[str, int],
    session: Session,
) -> None:
    if len(data) == 0:
        return

    if isinstance(next(iter(data.values()))[0], dict):
        insert_word_ladder_new(session=session, data=data, word_scores=word_scores)
    else:
        insert_word_ladder_old(session=session, data=data, word_scores=word_scores)


def insert_word_ladder_new(
    session: Session, data: dict[str, LadderSet], word_scores: dict[str, int]
) -> None:
    values: list[dict] = []
    for key, ladder_list in data.items():
        for index, ladder_dict in enumerate(ladder_list):
            ladder = ladder_dict["path"]
            hardest_word, hardest_word_score = get_hardest_word(ladder, word_scores)
            values.append(
                {
                    "pair": key,
                    "dictionary": "common",
                    "chain": ",".join(ladder),
                    "length": len(ladder),
                    "difficulty": ladder_difficulty(ladder, word_scores),
                    "hardest_word": hardest_word,
                    "hardest_word_score": hardest_word_score,
                    "variations": len(ladder_list),
                    "variant": index + 1,
                },
            )
    statement = insert(models.Ladder).values(values).on_conflict_do_nothing()
    session.exec(statement)
    session.commit()


def insert_word_ladder_old(
    session: Session, data: dict[str, LadderSet], word_scores: dict[str, int]
) -> None:
    unique_ladder_keys: set[str] = {sort_word_pair(pair) for pair in data}

    logger.debug("%s ladder keys", len(unique_ladder_keys))
    values: list[dict] = []
    for key in unique_ladder_keys:
        ladder_list: LadderSet = data[key]
        for index, ladder in enumerate(ladder_list):
            hardest_word, hardest_word_score = get_hardest_word(ladder, word_scores)
            values.append(
                {
                    "pair": key,
                    "dictionary": "common",
                    "chain": ",".join(ladder),
                    "length": len(ladder),
                    "difficulty": ladder_difficulty(ladder, word_scores),
                    "hardest_word": hardest_word,
                    "hardest_word_score": hardest_word_score,
                    "variations": len(ladder_list),
                    "variant": index + 1,
                },
            )
    statement = insert(models.Ladder).values(values).on_conflict_do_nothing()
    session.exec(statement)
    session.commit()

# TODO(shaun): Remove duplicated functionality  # noqa: TD003, FIX002

def insert_word_ladders(session: Session, word_scores: dict[str, int]) -> None:
    for word_length in range(3, 7):
        logger.info("Adding %s-letter word ladders", word_length)
        data: dict[str, LadderSet] = get_ladder_json(word_length=word_length)
        insert_word_ladder(data=data, word_scores=word_scores, session=session)
    logger.info("Done.")


def setup_ladders() -> None:
    with Session(engine) as session:
        word_scores: dict[str, int] = get_word_scores(session=session)
        insert_word_scores(session=session, word_scores=word_scores)
        insert_word_ladders(session=session, word_scores=word_scores)


def main() -> None:
    if not database_exists(engine.url):
        create_database(engine.url)
        SQLModel.metadata.create_all(engine)
    setup_dictionaries()
    setup_ladders()


if __name__ == "__main__":
    main()
