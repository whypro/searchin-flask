# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from sqlalchemy.ext.associationproxy import association_proxy

from ..extensions import db


class Manufacturer(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(20), nullable=False)    # 品牌名称
    alias = db.Column(db.Unicode(20))   # 品牌别名
    logo = db.Column(db.Unicode(200))   # 品牌 LOGO



class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturer.id', ondelete='SET NULL'))  # 制造商 ID
    manufacturer = db.relationship('Manufacturer', backref='products')
    model = db.Column(db.Unicode(20))           # 型号
    version = db.Column(db.Unicode(20))         # 版本
    price = db.Column(db.Numeric(10, 2))        # 基准价格
    photo = db.Column(db.Unicode(200))          # 图片路径

    questions = association_proxy('product_questions', 'question')


class Album(object):

    id = ''
    product_id = ''
    photo = ''


class Question(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Unicode(60), nullable=False)            # 问题，如“成色”，“是否进水”


class Answer(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id', ondelete='CASCADE'))        # 问题 ID
    question = db.relationship('Question', backref='answers')
    content = db.Column(db.Unicode(60), nullable=False)            # 回答内容
    description = db.Column(db.Unicode(100))        # 描述


class ProductQuestion(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'))            # 物品 ID
    product = db.relationship('Product', backref='product_questions')
    question_id = db.Column(db.Integer, db.ForeignKey('question.id', ondelete='CASCADE'))        # 问题 ID
    question = db.relationship('Question')
    order = db.Column(db.Integer, autoincrement=True)              # 排序


class ProductAnswer(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'))     # 物品 ID
    product = db.relationship('Product', backref='product_answers')
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete='CASCADE'))          # 回答 ID
    answer = db.relationship('Answer')
    discount = db.Column(db.Numeric(10, 2))           # 相应折扣
