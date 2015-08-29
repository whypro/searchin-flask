# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
from lxml import etree
# from flask import current_app
from celery import Celery

from .config import Config
from .models import Paper

celery = Celery('searchin', backend=Config.CELERY_RESULT_BACKEND, broker=Config.CELERY_BROKER_URL)


@celery.task
def crawl_papers(key):
    url_template = 'http://xueshu.baidu.com/s?wd={key}&rsv_bp=0&tn=SE_baiduxueshu_c1gjeupa&ie=utf-8'
    resp = requests.get(url_template.format(key=key))
    papers = _parse_paper_areas(resp.text)
    return papers


def _parse_paper_areas(text):
    parser = etree.HTMLParser()
    tree = etree.parse(text, parser)

    papers = []

    areas = tree.xpath('//div[@class="leftnav_list leftnav_list_show"]/div/a')
    for area in areas:
        area_title = area.xpath('@title')[0].strip()
        href = area.xpath('@href')[0]
        resp = requests.get(urljoin('http://xueshu.baidu.com/', href))
        papers += _parse_papers(resp.text, area_title)

    return papers


def _parse_papers(text, area, page=1):
    parser = etree.HTMLParser()
    tree = etree.parse(text, parser)

    papers = []

    items = tree.xpath('//div[@class="result xpath-log"]')
    for item in items:
        # 标题 和 URL
        _title = item.xpath('div[@class="sc_content"]/h3/a')
        if not _title:
            continue
        title = _title[0].xpath('string(.)')
        url = item.xpath('div[@class="sc_content"]/h3/a/@href')[0]

        authors = item.xpath('div[@class="sc_content"]/div[@class="sc_info"]/span[1]/a/text()')
        journal = item.xpath('div[@class="sc_content"]/div[@class="sc_info"]/a[1]/@title')[0].strip('《').strip('》')
        _year = item.xpath('div[@class="sc_content"]/div[@class="sc_info"]/span[@class="sc_time"]/text()')
        year = _year[0] if _year else ''
        key_words = item.xpath('div[@class="sc_content"]/div[@class="c_abstract"]/p/span/a/text()')
        cite_num = item.xpath('div[@class="sc_ext"]/div[@class="sc_cite"]//span[@class="sc_cite_num c-gray"]/text()')[0]

        paper = Paper()
        paper.title = title
        paper.url = url
        paper.authors = authors
        paper.journal = journal
        paper.year = year
        paper.key_words = key_words
        paper.cite_num = cite_num
        paper.click_num = 0
        paper.area = area

        papers.append(paper)

        # print 'title', title
        # print 'url', url
        # print 'authors', authors
        # print 'journal', journal
        # print 'year', year
        # print 'key_words', key_words

    if page < Config.MAX_CRAWL_PAGE:
        page += 1
        next_page = tree.xpath('//p[@id="page"]/a[last()]/@href')[0]
        url = urljoin(response.effective_url, next_page)
        resp = requests.get(url)
        yield _parse_papers(resp.text)
    else:
        yield papers





@celery.task
def add(a, b):
    return a + b
