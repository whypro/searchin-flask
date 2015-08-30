# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from lxml import etree
import json
from StringIO import StringIO
from urlparse import urljoin
import datetime
import time

import requests
from celery import Celery
from pymongo import MongoClient
# from flask import current_app

from .config import Config
from .models import Paper, Book


celery = Celery('searchin', backend=Config.CELERY_RESULT_BACKEND, broker=Config.CELERY_BROKER_URL)


@celery.task
def crawl_papers(key):
    if not _is_need_crawl(key, 'paper'):
        return []

    _set_crawled(key, 'paper')

    url_template = 'http://xueshu.baidu.com/s?wd={key}&rsv_bp=0&tn=SE_baiduxueshu_c1gjeupa&ie=utf-8'
    response = requests.get(url_template.format(key=key))

    papers = []

    for area_title, href in _parse_paper_areas(response.text):
        url = urljoin(response.url, href)
        papers += _fetch_papers(url, area_title)
        # papers += new_papers
        # save_papers(new_papers)

    return papers


def _parse_paper_areas(text):
    """解析【领域】"""
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(text), parser)
    areas = tree.xpath('//div[@class="leftnav_list leftnav_list_show"]/div/a')
    for area in areas:
        area_title = area.xpath('@title')[0].strip()
        href = area.xpath('@href')[0]
        yield area_title, href


def _fetch_papers(url, area, page=1):
    response = requests.get(url)

    papers = list(_parse_papers(response.text, area))

    save_papers(papers)
       
    if page < Config.MAX_CRAWL_PAGE:
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(response.text), parser)
        _next_page = tree.xpath('//p[@id="page"]/a[last()]/@href')
        if _next_page:
            next_page = _next_page[0]
            next_url = urljoin(url, next_page)
            return papers + list(_fetch_papers(next_url, area, page+1))
        else:
            return papers
    else:
        return papers


def _parse_papers(text, area):
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(text), parser)

    items = tree.xpath('//div[@class="result xpath-log"]')
    for item in items:
        # 标题 和 URL
        _title = item.xpath('div[@class="sc_content"]/h3/a')
        if not _title:
            continue
        title = _title[0].xpath('string(.)')
        url = item.xpath('div[@class="sc_content"]/h3/a/@href')[0]

        authors = item.xpath('div[@class="sc_content"]/div[@class="sc_info"]/span[1]/a')
        journal = item.xpath('div[@class="sc_content"]/div[@class="sc_info"]/a[1]/@title')[0].strip('《').strip('》')
        _year = item.xpath('div[@class="sc_content"]/div[@class="sc_info"]/span[@class="sc_time"]/@data-year')
        year = _year[0] if _year else ''
        key_words = item.xpath('div[@class="sc_content"]/div[@class="c_abstract"]/p/span/a')
        cite_num = item.xpath('div[@class="sc_ext"]/div[@class="sc_cite"]//span[@class="sc_cite_num c-gray"]/text()')[0]

        paper = Paper()
        paper.title = title
        paper.url = url
        paper.authors = [a.xpath('string(.)') for a in authors]
        paper.journal = journal
        paper.year = year
        paper.key_words = [k.xpath('string(.)') for k in key_words]
        paper.cite_num = cite_num
        paper.click_num = 0
        paper.area = area

        yield paper


@celery.task
def crawl_books(key):
    if not _is_need_crawl(key, 'book'):
        return []

    _set_crawled(key, 'book')

    url_template = 'http://61.150.69.38:8080/opac/openlink.php?strSearchType=title&match_flag=forward&historyCount=1&strText={key}&doctype=ALL&with_ebook=on&displaypg=100&showmode=table&sort=CATA_DATE&orderby=desc&dept=ALL'
    
    books = _fetch_books(url_template.format(key=key))

    return books


def _fetch_books(url, page=1):
    response = requests.get(url)

    books = []

    for href in _parse_book_list(response.text):
        book_url = urljoin(response.url, href)
        response = requests.get(book_url)
        book = _parse_book(response.text, book_url)
        books.append(book)

    # 保存
    save_books(books)
       
    if page < Config.MAX_CRAWL_PAGE:
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(response.text), parser)
        _next_page = tree.xpath('//div[@class="numstyle"]/a[text()="下一页"]/@href')
        if _next_page:
            next_page = _next_page[0]
            next_url = urljoin(url, next_page)
            return books + list(_fetch_books(next_url, page+1))
        else:
            return books
    else:
        return books


def _parse_book_list(text):
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(text), parser)
    items = tree.xpath('//table[@id="result_content"]/tr[@bgcolor="#FFFFFF"]')
    for item in items:
        href = item.xpath('td[2]/a/@href')[0]
        yield href


def _parse_book(text, url):
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(text), parser)

    isbn = tree.xpath('//div[@id="item_detail"]/dl[3]/dd/text()')[0].split('/')[0].split(' ')[0]

    url_template = 'https://api.douban.com/v2/book/isbn/{isbn}'
    response = requests.get(url_template.format(isbn=isbn))
    time.sleep(1)

    book_dict = json.loads(response.text, encoding='utf-8')
    book_dict['douban_id'] = book_dict.pop('id', '')
    book_dict['douban_api_url'] = book_dict.pop('url', '')
    book_dict['isbn'] = isbn
    book_dict['url'] = url
    book_dict['click_num'] = 0

    return Book(**book_dict)


def save_papers(papers):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    for paper in papers:
        db.papers.update({'url': paper.url}, {'$set': paper.__dict__}, upsert=True)
    client.close()


def save_books(books):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    for book in books:
        db.books.update({'douban_id': book.douban_id}, {'$set': book.__dict__}, upsert=True)
    client.close()

import pytz

def _is_need_crawl(key, query_type):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    query = db.queries.find_one({'key': key, 'type': query_type}, {'last_crawl': 1})
    tz = pytz.timezone('Asia/Shanghai')
    # print datetime.datetime.now(tz), query['last_crawl']
    if not query:
        need_crawl = True
    elif not 'last_crawl' in query:
        need_crawl = True
    elif datetime.datetime.now(tz) - query['last_crawl'] > Config.CRAWL_TIME_DELTA:
        need_crawl = True
    else:
        need_crawl = False

    client.close()
    return need_crawl


def _set_crawled(key, query_type):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    tz = pytz.timezone('Asia/Shanghai')
    db.queries.update({'key': key, 'type': query_type}, {'$set': {'last_crawl': datetime.datetime.now(tz)}, '$inc': {'count': 1}}, upsert=True)
    client.close()
