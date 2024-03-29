from __future__ import annotations

import random
from typing import Any, Sequence

from sqlmodel import Session, col, func, or_, select

from letters.anagrammer.models import Ladder, WordLadderOptions, WordScore


def word_pair_results_to_json(
    results: Sequence[Ladder], original_pair: str
) -> dict[str, Any]:
    """Assumes results are for a single word_pair."""
    reverse_ladder = False

    if word_pair := results and results[0].pair:
        reverse_ladder = results[0].pair != original_pair
        word_pair = original_pair

    def process_chain(chain: str) -> str:
        if reverse_ladder:
            return ",".join(reversed(chain.split(",")))
        return chain

    return {
        "ladder": {
            "pair": word_pair,
            "chain": [process_chain(r.chain) for r in results],
            "minimum_chain": results and max(r.length for r in results),
            "minimum_difficulty": results
            and min(r.hardest_word_score for r in results),  # mypy: type: ignore
        },
    }


LadderJSON = dict[str, list[dict[str, Any]]]


def ladders_to_json(results: Sequence[Ladder]) -> LadderJSON:
    pair_set = set()
    ladders = []
    for row in results:
        if row.pair not in pair_set:
            ladders.append(
                {
                    "pair": row.pair,
                    "min_length": row.length,
                    "difficulty": row.difficulty,
                    "solutions": row.variations,
                }
            )
            pair_set.add(row.pair)

    return {"ladders": ladders}


def _flip_word_pair(word_pair: str) -> str:
    return "-".join(reversed(word_pair.split("-")))


def get_word_ladder_for_word_pair(word_pair: str, session: Session) -> dict[str, Any]:
    flipped_word_pair: str = _flip_word_pair(word_pair)

    results: Sequence[Ladder] = session.exec(
        select(Ladder)
        .where(or_(Ladder.pair == word_pair, Ladder.pair == flipped_word_pair))
        .order_by(col(Ladder.hardest_word_score))
    ).all()
    return word_pair_results_to_json(results, original_pair=word_pair)


def get_ladders_by_length_and_difficulty(
    session: Session, word_length: int, upper_bound: int, lower_bound: int = 0
) -> Sequence[Ladder]:
    results: Sequence[Ladder] = session.exec(
        select(Ladder)
        .where(func.length(Ladder.pair) == word_length * 2 + 1)
        .where(col(Ladder.difficulty) < upper_bound)
        .where(col(Ladder.difficulty) > lower_bound)
        .order_by(col(Ladder.difficulty), col(Ladder.hardest_word_score), Ladder.pair)
    ).all()
    return results


def difficulty_class_to_range(difficulty_class: list[int]) -> tuple[int, int]:
    difficulty_class = [int(c) for c in difficulty_class]
    upper, lower = max(difficulty_class) * 10000, (min(difficulty_class) - 1) * 10000
    return upper, lower


def search_ladders(options: WordLadderOptions, session: Session) -> LadderJSON:
    pair_lengths = (int(length) * 2 + 1 for length in options.length)

    query = select(Ladder)

    if options.difficulty:
        upper, lower = difficulty_class_to_range(difficulty_class=options.difficulty)
        query = query.filter(col(Ladder.difficulty) < upper).filter(
            col(Ladder.difficulty) > lower
        )
    if options.length:
        query = query.filter(
            or_(False, *[func.length(Ladder.pair) == p for p in pair_lengths])  # noqa: FBT003
        )
    if options.ladder_filter:
        query = query.filter(col(Ladder.pair).contains(options.ladder_filter))
    results = session.exec(
        query.order_by(col(Ladder.difficulty), col(Ladder.hardest_word_score)).limit(
            options.page_size
        )
    ).all()
    return ladders_to_json(results)


def get_ladders_by_difficulty_class(
    session: Session, word_length: int, difficulty_class: list[int]
) -> LadderJSON:
    upper, lower = difficulty_class_to_range(difficulty_class=difficulty_class)
    results = get_ladders_by_length_and_difficulty(
        session=session, word_length=word_length, upper_bound=upper, lower_bound=lower
    )
    return ladders_to_json(results)


def get_easy_ladders_by_word_length(session: Session, word_length: int) -> LadderJSON:
    max_ladder_difficulty = 10000
    results = session.exec(
        select(Ladder)
        .filter(func.length(Ladder.pair) == word_length * 2 + 1)
        .filter(col(Ladder.difficulty) < max_ladder_difficulty)
        .filter(col(Ladder.difficulty) > 0)
        .order_by(col(Ladder.difficulty), col(Ladder.hardest_word_score))
    ).all()
    return ladders_to_json(results)


def get_words_and_scores(
    word_dictionary: str, word_length: int, session: Session
) -> dict[str, int]:
    results = session.exec(
        select(WordScore)
        .filter(func.length(WordScore.word) == word_length)
        .filter(col(WordScore.dictionary) == word_dictionary)
        .order_by(WordScore.word)
    ).all()
    return {word_score.word: word_score.score for word_score in results}


def get_random_ladder_in_difficulty_range(
    session: Session, word_length: int, upper_bound: int, lower_bound: int = 0
) -> dict[str, Any]:
    results: Sequence[Ladder] = get_ladders_by_length_and_difficulty(
        session=session,
        word_length=word_length,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
    )
    rand = random.SystemRandom().randint(0, len(results))
    random_ladder: Ladder = results[rand]
    return word_pair_results_to_json([random_ladder], original_pair=random_ladder.pair)
