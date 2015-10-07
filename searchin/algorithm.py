# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import datetime
import math

#用于计算论文的排名影响因子  注意后缀 "_paper" 的区别
def calculate_paper_relevancy(year, cite_num, click_num):
    if not year:
        return 0

    MAX_CITE_NUM = 3000   
    MAX_CLICK_NUM = 38      
    YEAR_PARAM = 2.196    
    
    #测试参数YEAR_PARAM的影响范围  
    #测试结果：
    #结论1： 从每个图的图像坡度看，随着year_para数值的增大，年的衰减变缓。
    #结论2： 从year_result的最大值看，随着year_para数值的增大，年的贡献变小。
    #针对目前的排名情况，建议采用如下策略：1.196--》2.196   （已经在上面进行了修改）
    a = 1 / (datetime.date.today().year - year + YEAR_PARAM)
    b = math.log(min(cite_num + 1, MAX_CITE_NUM)) / math.log(MAX_CITE_NUM)
    c = math.log(min(click_num + 1, MAX_CLICK_NUM)) / math.log(MAX_CLICK_NUM)

    #归一化 防止某一个参数过大，对其他参数形成消弱。
    # sum_abc = a + b + c
    # print a, b, c
    # a = a / sum_abc
    # b = b / sum_abc
    # c = c / sum_abc
    # print a, b, c
    
    relevancy_paper = a * 0.5 + b * 0.3 + c * 0.2

    return relevancy_paper


if __name__ == '__main__':
    print calculate_paper_relevancy(2015, 20, 1)
    print calculate_paper_relevancy(2008, 1, 1)
    print calculate_paper_relevancy(2008, 2000, 1)
