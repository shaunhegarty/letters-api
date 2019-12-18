#!flask/bin/python
from flask import Flask
from flask import jsonify
from flask import request
import sys
from anagrammer import dictionary
from anagrammer import app

d = dictionary.Dictionary()

# @application.route('/<username>')
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

@app.route('/anagrams/<word>')
def get_anagrams(word):
    anagrams = d.get_anagrams(word)
    return respond(anagrams)

@app.route('/subanagrams/<word>')
def get_sub_anagrams(word):
    best_only = str(request.args.get('best')) == 'true'
    anagrams = d.get_sub_anagrams(word)
    max = len(anagrams[0]) # longest first so this is the max

    sub_anagrams = {}
    for word in anagrams:
        if best_only and len(word) != max:
            break
        sub = sub_anagrams.get(len(word), {})
        sub_words = sub.get('words', [])
        sub_words.append(word)
        sub['words'] = sub_words
        sub['count'] = len(sub_words)
        sub_anagrams[len(word)] = sub
    return respond({"max":max, "words":sub_anagrams})

@app.route('/validate/<word>')
def get_valid(word):
    return respond({
        'dictionary': 'sowpods',
        'dictionary_size': d.get_dict_size(),
        'valid': d.contains_word(word)
        })

@app.route('/')
def hello():
    return respond({'greeting': 'hello'})

def respond(input):
    response = jsonify(input)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response