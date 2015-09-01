from __future__ import unicode_literals, division
import datetime
import math


def calculate_relevancy(year, cite_num, click_num):
    if not year:
        return 0

    MAX_CITE_NUM = 3000
    MAX_CLICK_NUM = 38
    YEAR_PARAM = 1.196

    a = 1 / (datetime.date.today().year - year + YEAR_PARAM)
    b = math.log(min(cite_num + 1, MAX_CITE_NUM)) / math.log(MAX_CITE_NUM)
    c = math.log(min(click_num + 1, MAX_CLICK_NUM)) / math.log(MAX_CLICK_NUM)

    relevancy = a * 0.5 + b * 0.3 + c * 0.2

    return relevancy
