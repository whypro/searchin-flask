# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os


class Config(object):
    SECRET_KEY = 'xaailab'
    # JSON_SORT_KEY = False
    # JSONIFY_PRETTYPRINT_REGULAR = False

    # 数据库配置
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_DBNAME = 'searchin'

    # Celery
    CELERY_BROKER_URL = 'mongodb://localhost:27017/searchin-celery'
    CELERY_RESULT_BACKEND = 'mongodb://localhost:27017/searchin-celery'

    MAX_CRAWL_PAGE = 3
