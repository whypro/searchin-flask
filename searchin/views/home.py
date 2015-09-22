# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort, current_app

from ..extensions import mongo
from ..algorithm import calculate_relevancy
from ..tasks import refresh_all_relevancy, auto_crawl_books


home = Blueprint('home', __name__)


@home.route('/')
def index():
    return redirect(url_for('search.show_search'))


@home.route('/redirect/')
def click_redirect():
    url = request.args.get('url')
    redirect_type = request.args.get('type')

    invalid = True

    if redirect_type == 'paper':
        paper = mongo.db.papers.find_and_modify({'url': url}, {'$inc': {'click_num': 1}})
        if paper:
            # print paper
            relevancy = calculate_relevancy(paper['year'], paper['cite_num'], paper['click_num'])
            mongo.db.papers.update({'url': url}, {'$set': {'relevancy': relevancy}})
            invalid = False
    elif redirect_type == 'book':
        book = mongo.db.books.find_and_modify({'url': url}, {'$inc': {'click_num': 1}})
        if book:
            invalid = False

    if invalid:
        abort(400)

    return redirect(url)

@home.route('/refresh/')
def refresh():
    refresh_all_relevancy.delay()
    return redirect(url_for('home.index'))


@home.route('/crawl/')
def crawl():
    start_cls = request.args.get('start_cls', 'A')
    start_cls = int(request.args.get('start_page', '1'))
    auto_crawl_books.delay(start_cls=start_cls, start_page=start_page)
    return redirect(url_for('home.index'))
