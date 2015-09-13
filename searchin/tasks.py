# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from lxml import etree
import json
from StringIO import StringIO
from urlparse import urljoin
import datetime
import pytz
import re

import requests
from celery import Celery
from celery.contrib.methods import task
from pymongo import MongoClient
# from flask import current_app

from .config import Config
from .models import Paper, Book
from .algorithm import calculate_relevancy


celery = Celery('searchin', backend=Config.CELERY_RESULT_BACKEND, broker=Config.CELERY_BROKER_URL)


@celery.task
def crawl_papers(key):
    # if not _is_need_crawl(key, 'paper'):
    #     return []

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
    areas = tree.xpath('//a[@data-key="sc_c0"]')
    for area in areas:
        area_title = area.xpath('@title')[0].strip()
        href = area.xpath('@href')[0]
        yield area_title, href


def _fetch_papers(url, area, page=1):
    print url
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
        year = int(_year[0]) if _year else None
        key_words = item.xpath('div[@class="sc_content"]/div[@class="c_abstract"]/p/span/a')
        _cite_num = item.xpath('div[@class="sc_ext"]/div[@class="sc_cite"]//span[@class="sc_cite_num c-gray"]/text()')[0]
        if '万' in _cite_num:
            cite_num = int(float(_cite_num.strip('万')) * 10000)
        else:
            cite_num = int(_cite_num)

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
        paper.relevancy = calculate_relevancy(year=year, cite_num=cite_num, click_num=0)

        yield paper


@celery.task
def crawl_books(key):
    # if not _is_need_crawl(key, 'book'):
    #     return []

    _set_crawled(key, 'book')

    url_template = 'http://61.150.69.38:8080/opac/openlink.php?strSearchType=title&match_flag=forward&historyCount=1&strText={key}&doctype=ALL&with_ebook=on&displaypg=10&showmode=table&sort=CATA_DATE&orderby=desc&dept=ALL'
    
    books = _fetch_books(url_template.format(key=key))

    return books


def _fetch_books(url, page=1):
    print url
    response = requests.get(url)
    response.encoding = 'utf-8'
    books = []

    for href in _parse_book_list(response.text):
        book_url = urljoin(response.url, href)
        r = requests.get(book_url)
        r.encoding = 'utf-8'
        book = _parse_book(r.text, book_url)
        if book:
            books.append(book)

    # 保存
    # print books
    save_books(books)
       
    if page < Config.MAX_CRAWL_PAGE:
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(response.text), parser)
        _next_page = tree.xpath('//div[@class="numstyle"]/a[text()="下一页"]/@href')
        # print _next_page
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
    print url
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(text), parser)

    # picture = tree.xpath('//img[@id="book_img"]/@src')[0]

    book_dict = dict()
    items = tree.xpath('//div[@id="item_detail"]/dl[@class="booklist"]')
    for item in items:
        _dt = item.xpath('dt/text()')
        # print _dt
        if not _dt:
            continue
        dt = _dt[0].rstrip(':')
        dd = item.xpath('dd')[0].xpath('string(.)')
        # print dt, dd
        if dt not in book_dict:
            book_dict[dt] = dd
    # print book_dict

    book = Book()
    # book.image = picture
    book.click_num = 0
    book.url = url
    if '题名/责任者' in book_dict:
        match = re.search(r'([^\/]*)(\/([^\/]*))?', book_dict['题名/责任者'])
        book.title = match.group(1)
        book.authors = match.group(3)
        # book.title, book.authors = book_dict['题名/责任者'].split('/')
    if '出版发行项' in book_dict:
        book.publisher = book_dict['出版发行项'].split(',')[0].split(':')
        try:
            book.year = book_dict['出版发行项'].split(',')[1]
        except IndexError:
            book.year = None

    if 'ISBN及定价' in book_dict:
        book.isbn = book_dict['ISBN及定价'].split('/')[0].split(' ')[0]
        try: 
            book.price = book_dict['ISBN及定价'].split('/')[1]
        except IndexError:
            book.price = None
    else:
        return None

    if '中图法分类号' in book_dict:
        book.category_number = book_dict['中图法分类号']
    else:
        return None

    if '提要文摘附注' in book_dict:
        book.summary = book_dict['提要文摘附注']
    if '豆瓣简介' in book_dict:
        book.douban_summary = book_dict['豆瓣简介']

    return book


def save_papers(papers):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    for paper in papers:
        paper_dict = paper.__dict__
        #paper_dict.pop('relevancy', 0)
        db.papers.update({'url': paper.url}, {'$set': paper_dict}, upsert=True)
    client.close()


def save_books(books):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    for book in books:
        book_dict = book.__dict__
        db.books.update({'url': book.url}, {'$set': book_dict}, upsert=True)
    client.close()


def _book_exists(book_url):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]

    if db.books.find({'url': book_url}).count():
        ret = True
    else:
        ret = False

    client.close()
    return ret


def _set_crawled(key, query_type):
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    tz = pytz.timezone('Asia/Shanghai')
    db.queries.update({'key': key}, {'$set': {'last_crawl.'+query_type: datetime.datetime.now(tz)}}, upsert=True)
    client.close()


@celery.task
def refresh_all_relevancy():
    client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
    db = client[Config.MONGO_DBNAME]
    papers = db.papers.find({})
    for paper in papers:
        relevancy = calculate_relevancy(paper['year'], paper['cite_num'], paper['click_num'])
        db.papers.update({'url': paper['url']}, {'$set': {'relevancy': relevancy}})
    client.close()


@celery.task
def auto_crawl_books(start_cls='A'):
    spider = OPACSpider()
    spider.auto_crawl(start_cls=start_cls)


class OPACSpider(object):
    """"""
    cls_view_url_template = 'http://61.150.69.38:8080/browse/cls_browsing_book.php?s_doctype=all&cls={cls}&page={page}'

    def __init__(self):
        self.parser = etree.HTMLParser()
        self.client = MongoClient(host=Config.MONGO_HOST, port=Config.MONGO_PORT, tz_aware=True)
        self.db = self.client[Config.MONGO_DBNAME]

    def __del__(self):
        self.client.close()

    @task(ignore_result=True)
    def auto_crawl(self, start_cls='A'):
        cls_list = map(lambda x: chr(x), range(ord(start_cls), ord('Z')+1)) # 生成字母分类号 
        for cls in cls_list:
            max_page = self.parse_cls_view_max_page(cls)
            print '{cls}: {max_page}'.format(cls=cls, max_page=max_page)
            for page in range(1, max_page+1):
                self.parse_cls_view_list(cls, page)

    def parse_cls_view_max_page(self, cls='A'):
        cls_view_url = self.cls_view_url_template.format(cls=cls, page=1)
        response = requests.get(cls_view_url)
        tree = etree.parse(StringIO(response.text), self.parser)
        _max_page = tree.xpath('//div[@class="numstyle"]/b/font[@color="black"]/text()')[0]
        max_page = int(_max_page) if _max_page else 1
        return max_page

    @task(ignore_result=True)
    def parse_cls_view_list(self, cls='A', page=1):
        """
        解析 url 为 http://61.150.69.38:8080/browse/cls_browsing_book.php?s_doctype=all&cls=A&page=1 的图书列表
        其中 cls = [A-Z], page = \d*
        """
        cls_view_url = self.cls_view_url_template.format(cls=cls, page=page)
        print cls_view_url
        response = requests.get(cls_view_url)
        response.encoding = 'utf-8'

        tree = etree.parse(StringIO(response.text), self.parser)
        book_items = tree.xpath('//div[@class="list_books"]')
        for book_item in book_items:
            href = book_item.xpath('h3/strong/a/@href')[0]
            book_url = urljoin(response.url, href)

            if self.is_book_exists(book_url):
                continue

            self.parse_book_detail(book_url)

    @task()
    def parse_book_detail(self, url):
        print url
        response = requests.get(url)
        response.encoding = 'utf-8'
        tree = etree.parse(StringIO(response.text), self.parser)

        # picture = tree.xpath('//img[@id="book_img"]/@src')[0]

        book_dict = dict()
        items = tree.xpath('//div[@id="item_detail"]/dl[@class="booklist"]')
        for item in items:
            _dt = item.xpath('dt/text()')
            # print _dt
            if not _dt:
                continue
            dt = _dt[0].rstrip(':')
            dd = item.xpath('dd')[0].xpath('string(.)')
            # print dt, dd
            if dt not in book_dict:
                book_dict[dt] = dd
        # print book_dict

        book = Book()
        # book.image = picture
        book.click_num = 0
        book.url = url
        if '题名/责任者' in book_dict:
            match = re.search(r'([^\/]*)(\/([^\/]*))?', book_dict['题名/责任者'])
            book.title = match.group(1)
            book.authors = match.group(3)
            # book.title, book.authors = book_dict['题名/责任者'].split('/')
        if '出版发行项' in book_dict:
            book.publisher = book_dict['出版发行项'].split(',')[0].split(':')
            try:
                book.year = book_dict['出版发行项'].split(',')[1]
            except IndexError:
                book.year = None

        if 'ISBN及定价' in book_dict:
            book.isbn = book_dict['ISBN及定价'].split('/')[0].split(' ')[0]
            try: 
                book.price = book_dict['ISBN及定价'].split('/')[1]
            except IndexError:
                book.price = None
        else:
            return None

        if '中图法分类号' in book_dict:
            book.category_number = book_dict['中图法分类号']
        else:
            return None

        if '提要文摘附注' in book_dict:
            book.summary = book_dict['提要文摘附注']
        if '豆瓣简介' in book_dict:
            book.douban_summary = book_dict['豆瓣简介']

        self.save_books([book])
        return book

    def is_book_exists(self, url):
        """检查 url 对应的图书是否存在于数据库中"""
        if self.db.books.find({'url': url}).count():
            return True
        else:
            return False

    def save_books(self, books):
        for book in books:
            book_dict = book.__dict__
            self.db.books.update({'url': book.url}, {'$set': book_dict}, upsert=True)

    def set_cls_crawled(self, cls):
        pass

    def is_cls_crawled(self, cls):
        pass
