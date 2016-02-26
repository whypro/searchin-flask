# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import json
import pytz
import datetime
import re
import urllib

from flask import Blueprint, render_template, g, jsonify, Response, request, current_app, abort
import pymongo
from elasticsearch import Elasticsearch

from ..extensions import mongo
from ..tasks import crawl_papers, crawl_books
from ..algorithm import calculate_paper_relevancy
from ..book_searcher import get_book_searcher


search = Blueprint('search', __name__, url_prefix='/search')


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


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

    papers, total = load_papers(key, start, count)

    result_dict = {'key': key, 'total': total, 'start': start, 'count': len(papers), 'papers': papers}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8', cls=CJsonEncoder)
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(papers_list), books=papers_list)


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

    books, total = load_books(key, start, count)
    result_dict = {'key': key, 'total': total, 'start': start, 'count': len(books), 'books': books}
    result_json = json.dumps(result_dict, ensure_ascii=False, encoding='utf-8')
    return Response(result_json,  mimetype='application/json; charset=utf-8')
    # return jsonify(key=key, count=len(books_dict), books=books_dict)


def load_papers(key, start, count):
    if False:
        return search_papers_from_mongodb(key, start, count)
    else:
        return search_papers_from_baiduxueshu(key)


def search_papers_from_mongodb(key, start, count):
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

    # convert pymongo cursor to list
    papers_list = []
    for p in papers:
        p['quoted_url'] = urllib.quote(p['url'])
        papers_list.append(p)
    return papers_list, papers.count()


import requests
def search_papers_from_baiduxueshu(key):
    params = {
        'ctx_ver': 'Z39.88-2004',
        'ctx_enc': 'info:ofi/enc:UTF-8',
        'rft_genre': 'article',
        'query': key,
        'callback': 'cb',
        'school': current_app.config['BAIDUXS_SCHOOL'],
        'api_key': current_app.config['BAIDUXS_API_KEY'],
        'secret_key': current_app.config['BAIDUXS_SECRET_KEY']
    }
    r = requests.get(current_app.config['BAIDUXS_URL'], params=params)
    json_str = r.text[3:-1]
    data = json.loads(json_str)
    if data['status']:
        return [], 0
    else:
        return data['data'], len(data['data'])


def load_books(key, start, count):
    if False:
        return search_books_from_mongodb(key, start, count)
    else:
        return search_books_from_es(key, start, count)


def search_books_from_mongodb(key, start, count):
    search_conditions = []
    for k in key.split('&'):
        search_conditions.append({
            'title': {'$regex': k, '$options': '$i'}
        })

    books = mongo.db.books.find({'$and': search_conditions}, {'_id': False, 'update_time': False}, skip=start, limit=count)
    if start == 0:
        mongo.db.queries.update({'key': key}, {'$inc': {'count.book': 1}}, upsert=True)
    # print books.count()
    return [b for b in books], books.count()


def search_books_from_es(key, start, count):
    es = Elasticsearch()
    dsl_query = {"query": {"match": {"_all": {"query": key, "operator": "and"}}}}
    res = es.search(index='searchin', doc_type=['books'], body=dsl_query, from_=start, size=count)
    total = res['hits']['total']
    books = [hit['_source'] for hit in res['hits']['hits']]
    return books, total


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
    elif 'last_crawl' not in query:
        need_crawl = True
    elif query_type not in query['last_crawl']:
        need_crawl = True
    elif datetime.datetime.now(tz) - query['last_crawl'][query_type] > current_app.config['CRAWL_TIME_DELTA']:
        need_crawl = True
    else:
        need_crawl = False

    return need_crawl


def format_key(key):
    # 将一些分割字符转义
    safe_str = re.sub(r'(\*|\.|\?|\+|\$|\^|\[|\]|\(|\)|\{|\}|\||\\|/)', r'\\\1', key)
    valid_keys = filter(lambda x: x, re.split(' ', safe_str))
    #print valid_keys
    key = '&'.join(valid_keys)
    #print key
    return key


@search.route('/book/test/page/<int:page>/', methods=['GET'])
@search.route('/book/test/', methods=['GET'], defaults={'page': 1})
@search.route('/book/test/', methods=['POST'])
def search_books_test(page=None):
    if request.method == 'POST':
        query_string = request.form['query_string']
        if not hasattr(current_app, 'book_searcher'):
            current_app.book_searcher = get_book_searcher()
        bs = current_app.book_searcher
        result_list = bs.split_count_calculate_collect(query_string)
        books = []
        begin, end = 0, 100
        for oid in result_list[begin:end]:
            book = mongo.db.books.find_one({'_id': oid})
            books.append(book)
        # books = mongo.db.find({'_id': {'$in': result_list}})
        return render_template('search/book_test.html', books=books)

    return render_template('search/book_test.html')

