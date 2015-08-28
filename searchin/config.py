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

