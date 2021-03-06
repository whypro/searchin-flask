# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import urllib
import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort, current_app
import requests

from ..extensions import mongo
from ..algorithm import calculate_paper_relevancy
from ..tasks import refresh_all_relevancy, auto_crawl_books
from ..helpers import get_client_ip


home = Blueprint('home', __name__)


@home.route('/')
def index():
    return redirect(url_for('search.show_search'))


@home.route('/redirect/')
def click_redirect():
    url = request.args.get('url')
    redirect_type = request.args.get('type')

    invalid = True

    ip = get_client_ip()
    
    if redirect_type == 'paper':
        if url.startswith('http') and 'xueshu.baidu.com' in url:
            invalid = False
        #paper = mongo.db.papers.find_and_modify({'url': url}, {'$inc': {'click_num': 1}, '$push': {'click_info': {'ip': ip, 'click_time': datetime.datetime.utcnow()}}})
        #if paper:
        #    # print paper
        #    relevancy = calculate_paper_relevancy(paper['year'], paper['cite_num'], paper['click_num'])
        #    mongo.db.papers.update({'url': url}, {'$set': {'relevancy': relevancy}})
        #    invalid = False
    elif redirect_type == 'book':
        book = mongo.db.books.find_and_modify({'url': url}, {'$inc': {'click_num': 1}, '$push': {'click_info': {'ip': ip, 'click_time': datetime.datetime.utcnow()}}})
        if book:
            invalid = False

    if invalid:
        abort(400)

    return redirect(url)

@home.route('/relevancy/refresh/')
def refresh_relevancy():
    refresh_all_relevancy.delay()
    return redirect(url_for('home.index'))


@home.route('/crawl/')
def crawl():
    start_cls = request.args.get('start_cls', 'A')
    start_page = int(request.args.get('start_page', '1'))
    auto_crawl_books.delay(start_cls=start_cls, start_page=start_page)
    return redirect(url_for('home.index'))


@home.route('/image/<isbn>/')
def douban_image(isbn):
    # print isbn
    resp = requests.get('https://api.douban.com/v2/book/isbn/{isbn}'.format(isbn=isbn))
    data = resp.json()
    try:
        url = data['images']['small']
    except KeyError:
        url = 'http://61.150.69.38:8080/tpl/images/nobook.jpg'
    return jsonify(isbn=isbn, url=url)

