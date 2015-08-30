# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from flask import Blueprint, render_template, g, jsonify, Response, request

from ..extensions import mongo
from ..tasks import crawl_papers, crawl_books


search = Blueprint('search', __name__, url_prefix='/search')


@search.route('/')
def show_search():
    return render_template('search/index.html')


@search.route('/paper/json/<key>/')
def get_paper_search_result_json(key):
    # active celery crawl task
    crawl_papers.delay(key)

    start = int(request.args.get('start', 0))
    count = int(request.args.get('count', 10))

    papers_cursor = load_papers(key, start, count)
    # convert pymongo cursor to dict
    papers_dict = [p for p in papers_cursor]
    result_dict = {'key': key, 'count': len(papers_dict), 'papers': papers_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(papers_dict), books=papers_dict)


@search.route('/book/json/<key>/')
def get_book_search_result_json(key):
    # active celery crawl task
    crawl_books.delay(key)

    start = int(request.args.get('start', 0))
    count = int(request.args.get('count', 10))

    books_cursor = load_books(key, start, count)
    # convert pymongo cursor to dict
    books_dict = [b for b in books_cursor]
    result_dict = {'key': key, 'count': len(books_dict), 'books': books_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(books_dict), books=books_dict)


def load_papers(key, start, count):
    papers = mongo.db.papers.find({'title': {'$regex': key}}, {'_id': False}, skip=start, limit=count)
    # print papers.count()
    return papers


def load_books(key, start, count):
    books = mongo.db.books.find({'title': {'$regex': key}}, {'_id': False}, skip=start, limit=count)
    # print books.count()
    return books
