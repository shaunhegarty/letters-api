import random

from sqlalchemy.orm import Session
from sqlalchemy import func

from anagrammer.database import engine
from anagrammer.models import Ladder, WordScore


def word_pair_results_to_json(results):
    """Assumes results are for a single word_pair"""
    return {
        "ladder": {
            "pair": results and results[0].pair,
            "chain": [r.chain for r in results],
            "minimum_chain": results and max(r.length for r in results),
            "minimum_difficulty": results
            and min(r.hardest_word_score for r in results),
        },
    }


def ladders_to_json(results):
    pair_set = set()
    ladders = []
    for r in results:
        if r.pair not in pair_set:
            ladders.append(
                {
                    "pair": r.pair,
                    "min_length": r.length,
                    "difficulty": r.difficulty,
                    "solutions": r.variations,
                }
            )
            pair_set.add(r.pair)

    return {"ladders": ladders}


def get_word_ladder_for_word_pair(word_pair: str):
    with Session(engine) as session:
        results = (
            session.query(Ladder)
            .filter(Ladder.pair == word_pair)
            .order_by(Ladder.hardest_word_score)
            .all()
        )
    return word_pair_results_to_json(results)


def get_ladders_by_length_and_difficulty(word_length, upper_bound, lower_bound=0):
    with Session(engine) as session:
        results = (
            session.query(Ladder)
            .filter(func.length(Ladder.pair) == word_length * 2 + 1)
            .filter(Ladder.difficulty < upper_bound)
            .filter(Ladder.difficulty > lower_bound)
            .order_by(Ladder.difficulty, Ladder.hardest_word_score)
            .all()
        )
    return results


def difficulty_class_to_range(difficulty_class):
    upper, lower = difficulty_class * 10000, (difficulty_class - 1) * 10000
    return upper, lower


def get_ladders_by_difficulty_class(word_length: int, difficulty_class: int):
    upper, lower = difficulty_class_to_range(difficulty_class=difficulty_class)
    results = get_ladders_by_length_and_difficulty(
        word_length=word_length, upper_bound=upper, lower_bound=lower
    )
    return ladders_to_json(results)


def get_easy_ladders_by_word_length(word_length):
    with Session(engine) as session:
        results = (
            session.query(Ladder)
            .filter(func.length(Ladder.pair) == word_length * 2 + 1)
            .order_by(Ladder.difficulty, Ladder.hardest_word_score)
            .limit(100)
            .all()
        )
        return ladders_to_json(results)


def get_words_and_scores(word_dictionary, word_length):
    with Session(engine) as session:
        results = (
            session.query(WordScore)
            .filter(func.length(WordScore.word) == word_length)
            .filter(WordScore.dictionary == word_dictionary)
            .order_by(WordScore.word)
            .all()
        )
        return {word_score.word: word_score.score for word_score in results}


def get_random_ladder_in_difficulty_range(word_length, upper_bound, lower_bound=0):
    results = get_ladders_by_length_and_difficulty(
        word_length=word_length, upper_bound=upper_bound, lower_bound=lower_bound
    )
    rand = random.SystemRandom().randint(0, len(results))
    return word_pair_results_to_json([list(results)[rand]])
