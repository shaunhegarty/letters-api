#!flask/bin/python
import time
from flask import jsonify, request, g
from anagrammer import dictionary
from anagrammer import app

d = dictionary.Dictionary()


@app.before_request
def before_request():
    g.start = time.time()


@app.after_request
def after_request(response):
    diff = time.time() - g.start
    app.logger.info(f"Request Time {diff * 1000:.3f} ms")

    header = response.headers
    header["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/anagrams/<word>")
def get_anagrams(word):
    anagrams = d.get_anagrams(word)
    return respond(anagrams)


@app.route("/subanagrams/<word>")
def get_sub_anagrams(word):
    best_only = str(request.args.get("best")) == "true"
    anagrams = d.get_sub_anagrams(word)
    max = len(anagrams[0])  # longest first so this is the max

    sub_anagrams = {}
    for word in anagrams:
        if best_only and len(word) != max:
            break
        sub = sub_anagrams.get(len(word), {})
        sub_words = sub.get("words", [])
        sub_words.append(word)
        sub["words"] = sub_words
        sub["count"] = len(sub_words)
        sub_anagrams[len(word)] = sub
    return respond({"max": max, "words": sub_anagrams})


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


def respond(data):
    response = jsonify(data)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
