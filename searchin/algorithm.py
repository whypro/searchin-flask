# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import datetime
import math


MAX_CITE_NUM = 3000
MAX_CLICK_NUM = 38
YEAR_PARAM = 2.196


# 用于计算论文的排名影响因子
# 线下计算
def calculate_paper_relevancy(year, cite_num, click_num):
    if not year:
        return 0

    # 测试参数YEAR_PARAM的影响范围
    # 测试结果：
    # 结论1： 从每个图的图像坡度看，随着year_para数值的增大，年的衰减变缓。
    # 结论2： 从year_result的最大值看，随着year_para数值的增大，年的贡献变小。
    # 针对目前的排名情况，建议采用如下策略：1.196--》2.196   （已经在上面进行了修改）
    a = 1 / (datetime.date.today().year - year + YEAR_PARAM)
    b = math.log(min(cite_num + 1, MAX_CITE_NUM)) / math.log(MAX_CITE_NUM)
    c = math.log(min(click_num + 1, MAX_CLICK_NUM)) / math.log(MAX_CLICK_NUM)

    # 归一化 防止某一个参数过大，对其他参数形成消弱。
    # sum_abc = a + b + c
    # print a, b, c
    # a = a / sum_abc
    # b = b / sum_abc
    # c = c / sum_abc
    # print a, b, c
    
    paper_relevancy = a * 0.5 + b * 0.3 + c * 0.2

    return paper_relevancy


# 用于计算图书的排名影响因子
# 因为有 query_ratio，必须线上计算
def calculate_book_relevancy(year, query_ratio, click_num):
    if not year or query_ratio < 0:
        return 0

    # 第一步：
    # 元素说明与计算
    # 考虑三个影响因子 ： 出版时间（year）、query占比(query_ratio)、点击量(click_num)

    # 关于出版时间影响的计算：
    year_factor = 1 / (datetime.date.today().year - year + YEAR_PARAM)  # 和论文的出版时间计算一样

    # 关于点击量影响的计算：
    # 首先声明：点击量每次获取必须满足 query_ratio > 0
    click_factor = math.log(min(click_num + 1, MAX_CLICK_NUM)) / math.log(MAX_CLICK_NUM)
    # 引入log是为了缩小点击量之间的落差

    # 第二步：
    # 影响因子归一化，防止某一个参数过大，对其他参数形成消弱
    # sum_factor = query_ratio + year_factor + click_factor
    # query_ratio = query_ratio / sum_factor
    # year_factor = year_factor / sum_factor
    # click_factor = click_factor / sum_factor

    # 第三步：
    # 综合计算相关度
    book_relevancy = query_ratio * 0.5 + year_factor * 0.25 + click_factor * 0.25

    # 第四步：
    # 返回相关度
    return book_relevancy


if __name__ == '__main__':
    print calculate_paper_relevancy(2015, 20, 1)
    print calculate_paper_relevancy(2008, 1, 1)
    print calculate_paper_relevancy(2008, 2000, 1)

    print calculate_book_relevancy(2008, 0.6, 20)
    print calculate_book_relevancy(2008, 0.3, 50)
    print calculate_book_relevancy(2008, 0.1, 1)
