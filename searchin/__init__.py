# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import Flask, flash, redirect, url_for
import logging

from . import views
from .extensions import mongo


def create_app(config=None):
    app = Flask(__name__)

    # config
    app.config.from_object(config)

    # blueprint
    app.register_blueprint(views.home)
    app.register_blueprint(views.search)
    # app.register_blueprint(views.member)
    # app.register_blueprint(views.admin)

    # database & migrate
    mongo.init_app(app)
    # db.init_app(app)
    # migrate.init_app(app, db)

    # logger
    init_app_logger(app)

    return app


def init_app_logger(app):
    # logging

    file_handler = logging.FileHandler('flask.log')

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)

