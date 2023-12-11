#!flask/bin/python
import time
from flask import jsonify, request, g
from flask.logging import create_logger
from sqlalchemy.exc import ProgrammingError
from anagrammer import app  # pylint: disable=cyclic-import
from . import dictionary, ladder

# Initialize the app
logger = create_logger(app)

try:
    d = dictionary.Dictionary()
except ProgrammingError:
    logger.warning("Database not set up")


@app.before_request
def before_request():
    g.start = time.time()


@app.after_request
def after_request(response):
    diff = time.time() - g.start
    logger.info("Request Time %s ms", f"{diff * 1000:.3f}")

    header = response.headers
    header["Access-Control-Allow-Origin"] = "*"
    header["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/anagrams/<word>")
def get_anagrams(word):
    anagrams = d.get_anagrams(word)
    return respond(anagrams)


@app.route("/subanagrams/<word>")
def get_sub_anagrams(word):
    best_only = str(request.args.get("best")) == "true"
    anagrams = d.get_sub_anagrams(word)
    max_len = len(anagrams[0])  # longest first so this is the max

    sub_anagrams = {}
    for anagram in anagrams:
        if best_only and len(anagram) != max_len:
            break
        sub = sub_anagrams.get(len(anagram), {})
        sub_words = sub.get("words", [])
        sub_words.append(anagram)
        sub["words"] = sub_words
        sub["count"] = len(sub_words)
        sub_anagrams[len(anagram)] = sub
    return respond({"max": max_len, "words": sub_anagrams})


@app.route("/validate/<word>")
def get_valid(word):
    return respond(
        {
            "dictionary": "sowpods",
            "dictionary_size": d.get_dict_size(),
            "valid": d.contains_word(word),
        }
    )


@app.route("/")
def hello():
    return respond({"greeting": "hello"})


@app.route("/conundrum/<int:length>")
def conundrum(length):
    return respond(d.get_conundrums(length))


@app.route("/words/<int:length>")
def words(length):
    return respond(d.get_words_by_length(length))


@app.route("/ladders/<word_pair>")
def word_ladder(word_pair):
    return respond(ladder.get_word_ladder_for_word_pair(word_pair))


@app.route("/ladders/<int:word_length>")
def word_ladders_by_length(word_length):
    return respond(ladder.get_easy_ladders_by_word_length(word_length))


@app.route("/ladders/<int:difficulty_class>/<int:word_length>")
def word_ladders_by_difficulty_and_length(difficulty_class, word_length):
    return respond(
        ladder.get_ladders_by_difficulty_class(
            word_length=word_length, difficulty_class=difficulty_class
        )
    )


@app.route("/ladders/search/", methods=["POST"])
def word_ladder_from_options():
    data = request.get_json()
    ladder_filter = data.get("ladder_filter", None)
    difficulty = data.get("difficulty", [1])
    word_length = data.get("length", [3])
    page_size = data.get("page_size", 200)
    return respond(
        ladder.search_ladders(word_length, difficulty, ladder_filter, page_size)
    )


@app.route("/ladders/words/<word_dictionary>/<int:length>")
def word_scores(word_dictionary, length):
    return respond(ladder.get_words_and_scores(word_dictionary, word_length=length))


@app.route("/ladders/random/<int:difficulty_class>/<int:length>")
def random_ladder(difficulty_class, length):
    upper, lower = difficulty_class * 10000, (difficulty_class - 1) * 10000
    return respond(
        ladder.get_random_ladder_in_difficulty_range(
            word_length=length, upper_bound=upper, lower_bound=lower
        )
    )


def respond(data):
    response = jsonify(data)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
