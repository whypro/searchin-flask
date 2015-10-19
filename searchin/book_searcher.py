# coding: utf-8
# 进行关键词搜索和计算
# 采用 倒排列表 算法
# 算法流程：
# 训练阶段：读入训练样本-->建立正排与倒排列表
# 测试阶段：输入汉字-->返回搜索结果及相关度
from __future__ import unicode_literals, division
import sys
import json
import time
from collections import defaultdict

from .extensions import mongo


class BookSearcher(object):

    def __init__(self):
        self.train_data_dict = dict()
        self.inverted_train_data_dict = dict()


    def load_from_file(self, filename='books.json'):
        """
           读入训练数据集：
           训练数据集存储格式为：JSON
           每一行表示一个样本
           输出格式为:
           dict={key1:{"title_len":0,"query_ratio":0,"title":..},key2:...}
        """
        train_data_dict = defaultdict(dict)
        line_num = 0
        null_title_num = 0

        with open(filename, 'r') as f:
            for line in f:
                line_num += 1
                row = json.loads(line)
                key = row['_id']['$oid']
                train_data_dict[key]['query_ratio'] = 0

                try: 
                    train_data_dict[key]['title'] = row['title']
                except KeyError:
                    null_title_num += 1
                    del train_data_dict[key]
                    continue

                train_data_dict[key]['title_len'] = len(row['title'])

        # print "作者为空个数 = ", nullAuthorsNum
        print "标题为空个数 = ", null_title_num
        # print "关键词为空个数 = ", nullKeyNum
        print "输入样本行数 = ", line_num
        print "训练样本总数 = ", len(train_data_dict)

        self.train_data_dict = train_data_dict

    def load_from_db(self):
        train_data_dict = defaultdict(dict)
        null_title_num = 0

        books = mongo.db.books.find({}, {'title': True})
        line_num = books.count()
        for book in books:
            key = book['_id']
            train_data_dict[key]['query_ratio'] = 0

            try: 
                train_data_dict[key]['title'] = book['title']
            except KeyError:
                null_title_num += 1
                del train_data_dict[key]
                continue

            train_data_dict[key]['title_len'] = len(book['title'])

        # print "作者为空个数 = ", nullAuthorsNum
        print "标题为空个数 = ", null_title_num
        # print "关键词为空个数 = ", nullKeyNum
        print "输入样本行数 = ", line_num
        print "训练样本总数 = ", len(train_data_dict)

        self.train_data_dict = train_data_dict

    def generate_inverted_dict(self):
        """
            生成倒排列表
            原始形式：
            dict={key1:{"title_len":0,"query_ratio":0,"title":..},key2:...}
            返回形式：
            dict = {word1:{key1:{"title_len":0,"query_ratio":0,"title":..},key2:...}, word2:... }
            该字典有三层结构
        """

        inverted_train_data_dict = defaultdict(dict)

        for key, item_dict in self.train_data_dict.items():
            for word in item_dict['title']:
                inverted_train_data_dict[word][key] = dict()
                inverted_train_data_dict[word][key]['title_len'] = item_dict['title_len']
                inverted_train_data_dict[word][key]['query_ratio'] = item_dict['query_ratio']

        # print len(inverted_train_data_dict)
        self.inverted_train_data_dict = inverted_train_data_dict

    def split_count_calculate_collect(self, query_string):
        '''
            1、分割查询字符串 并 统计击中次数
            2、计算query_ratio 并收集查询结果

            inverted_train_data_dict的形式如下：
            dict = {word1:{key1:{"title_len":0,"query_ratio":0,"title":..},key2:...}, word2:... }
            该字典有三层结构
            query_string = u"算法"  （例如）
        '''

        result_dict = defaultdict(dict) #dict = {key1:{"query_ratio":float, "title_len":int},key2:..., }
        query_len = len(query_string)  #计算查询字符串的长度

        # 初始化返回字典
        # 提取 题目命中数目(query_ratio) 和 题目长度（title_len）
        for word in query_string:
            for key, item_dict in self.inverted_train_data_dict[word].items():
                if 'query_ratio' in result_dict[key]:
                    result_dict[key]['query_ratio'] += 1    #统计题目命中字数
                else:
                    result_dict[key]['query_ratio'] = 1
                result_dict[key]['title_len'] = item_dict['title_len']

        #计算query_ratio 并 收集查询结果
        for key, item_dict in result_dict.items():
            temp_query_hit = item_dict['query_ratio']
            temp_precision_ratio = temp_query_hit / item_dict['title_len']  #precision
            temp_recall_ratio = temp_query_hit / query_len   #recall
            item_dict['query_ratio'] = (2 * temp_precision_ratio * temp_recall_ratio) / (temp_precision_ratio + temp_recall_ratio)

        result_list = [key for key, item_dict in sorted(result_dict.items(), key=lambda d: d[1]['query_ratio'], reverse=True)]
        return result_list


def get_book_searcher():
    #print g.book_searcher
    bs = BookSearcher()
    # bs.load_from_file('data/books.json')
    bs.load_from_db()
    bs.generate_inverted_dict()
    print 'init book searcher done.'
    return bs
        

if __name__ == '__main__':
    bs = BookSearcher()
    bs.load_from_file(filename='books.json')
    bs.generate_inverted_dict()
    # before_search = time.time() * 1000
    result_list = bs.split_count_calculate_collect(query_string='经济')
    # after_search = time.time() * 1000
    # print after_search - before_search, 'ms'
    print result_list
