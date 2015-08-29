# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from flask import Blueprint, render_template, g, jsonify, Response

from ..extensions import mongo


search = Blueprint('search', __name__, url_prefix='/search')


@search.route('/paper/')
def show_paper_search():
    return render_template('search/index.html')


@search.route('/paper/json/<key>/')
def get_paper_search_result_json(key):
    papers_cursor = load_papers(key)
    # convert pymongo cursor to dict
    papers_dict = [p for p in papers_cursor]
    result_dict = {'key': key, 'count': len(papers_dict), 'papers': papers_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(papers_dict), books=papers_dict)


@search.route('/book/')
def show_book_search():
    return render_template('search/index.html')


@search.route('/book/json/<key>/')
def get_book_search_result_json(key):
    books_cursor = load_books(key)
    # convert pymongo cursor to dict
    books_dict = [b for b in books_cursor]
    result_dict = {'key': key, 'count': len(books_dict), 'books': books_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(books_dict), books=books_dict)


from ..tasks import add

@search.route('/task/')
def test_task():
    result = add.delay(1, 1)
    return str(result)


def load_papers(key):
    papers = mongo.db.papers.find({'title': {'$regex': key}}, {'_id': False})
    print papers.count()
    return papers


def load_books(key):
    books = mongo.db.books.find({'title': {'$regex': key}}, {'_id': False})
    print books.count()
    return books
