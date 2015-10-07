# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import json
import pytz
import datetime
import re

from flask import Blueprint, render_template, g, jsonify, Response, request, current_app, abort
import pymongo

from ..extensions import mongo
from ..tasks import crawl_papers, crawl_books
from ..algorithm import calculate_paper_relevancy


search = Blueprint('search', __name__, url_prefix='/search')


@search.route('/')
def show_search():
    return render_template('search/index.html')


@search.route('/hot/')
def show_hot_keys():
    hot_keys = mongo.db.queries.find({}).sort([('count.paper', pymongo.DESCENDING), ('count.book', pymongo.DESCENDING)]).limit(10)
    return render_template('search/hot-keys.html', hot_keys=hot_keys)


@search.route('/paper/json/<raw_key>/')
def get_paper_search_result_json(raw_key):
    key = format_key(raw_key)
    if is_need_crawl(key, 'paper'):
        # active celery crawl task
        crawl_papers.delay(raw_key)

    start = int(request.args.get('start', 0))
    count = int(request.args.get('count', 10))

    if count > current_app.config['MAX_COUNT_PER_REQ']:
        abort(400)

    papers_cursor = load_papers(key, start, count)
    # convert pymongo cursor to dict
    papers_dict = [p for p in papers_cursor]
    result_dict = {'key': key, 'start': start, 'count': len(papers_dict), 'papers': papers_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(papers_dict), books=papers_dict)


@search.route('/book/json/<raw_key>/')
def get_book_search_result_json(raw_key):
    key = format_key(raw_key)
    if is_need_crawl(key, 'book'):
        # active celery crawl task
        crawl_books.delay(raw_key)

    start = int(request.args.get('start', 0))
    count = int(request.args.get('count', 10))

    if count > current_app.config['MAX_COUNT_PER_REQ']:
        abort(400)

    books_cursor = load_books(key, start, count)
    # convert pymongo cursor to dict
    books_dict = [b for b in books_cursor]
    result_dict = {'key': key, 'start': start, 'count': len(books_dict), 'books': books_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(books_dict), books=books_dict)


def load_papers(key, start, count):
    # TODO: 先排序后分页
    search_conditions = []
    for k in key.split('&'):
        search_conditions.append({
            'title': {'$regex': k, '$options': '$i'}
        })

    papers = mongo.db.papers.find({'$and': search_conditions}, {'_id': False}).sort([('relevancy', pymongo.DESCENDING)]).skip(start).limit(count)
    if start == 0:
        mongo.db.queries.update({'key': key}, {'$inc': {'count.paper': 1}}, upsert=True)

    #papers.skip(start).limit(count)
    # print papers.count()
    return papers


def load_books(key, start, count):
    search_conditions = []
    for k in key.split('&'):
        search_conditions.append({
            'title': {'$regex': k, '$options': '$i'}
        })

    books = mongo.db.books.find({'$and': search_conditions}, {'_id': False, 'update_time': False}, skip=start, limit=count)
    if start == 0:
        mongo.db.queries.update({'key': key}, {'$inc': {'count.book': 1}}, upsert=True)
    # print books.count()
    return books



def is_need_crawl(key, query_type):
    if query_type == 'book' and not current_app.config['CRAWL_BOOKS_ONLINE']:
        return False
    if query_type == 'paper' and not current_app.config['CRAWL_PAPERS_ONLINE']:
        return False

    query = mongo.db.queries.find_one({'key': key}, {'last_crawl.'+query_type: 1})
    tz = pytz.timezone('Asia/Shanghai')
    # print datetime.datetime.now(tz), query['last_crawl']
    if not query:
        need_crawl = True
    elif not 'last_crawl' in query:
        need_crawl = True
    elif not query_type in query['last_crawl']:
        need_crawl = True
    elif datetime.datetime.now(tz) - query['last_crawl'][query_type] > current_app.config['CRAWL_TIME_DELTA']:
        need_crawl = True
    else:
        need_crawl = False

    return need_crawl


def format_key(key):
    # 将一些分割字符转义
    safe_str = re.sub(r'(\*|\.|\?|\+|\$|\^|\[|\]|\(|\)|\{|\}|\||\\|\/)', r'\\\1', key)
    valid_keys = filter(lambda x: x, re.split(' ', safe_str))
    #print valid_keys
    key = '&'.join(valid_keys)
    #print key
    return key
