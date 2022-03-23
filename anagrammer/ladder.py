from sqlalchemy.orm import Session
from sqlalchemy import func

from anagrammer.database import engine
from anagrammer.models import Ladder


def word_pair_results_to_json(results):
    """Assumes results are for a single word_pair"""
    return {
        "pair": {
            "chain": [r.chain for r in results],
            "minimum_chain": results and max(r.length for r in results),
            "minimum_difficulty": results
            and min(r.hardest_word_score for r in results),
        },
    }


def get_word_ladder_for_word_pair(word_pair: str):
    with Session(engine) as session:
        results = (
            session.query(Ladder)
            .filter(Ladder.pair == word_pair)
            .order_by(Ladder.hardest_word_score)
            .all()
        )
    return word_pair_results_to_json(results)


def get_easy_ladders_by_word_length(word_length):
    with Session(engine) as session:
        results = (
            session.query(Ladder)
            .filter(func.length(Ladder.pair) == word_length * 2 + 1)
            .order_by(Ladder.difficulty, Ladder.hardest_word_score)
            .limit(100)
            .all()
        )
        return {
            f"{word_length}-ladders": {
                r.pair: {"min_length": r.length, "difficulty": r.difficulty}
                for r in results
            }
        }
