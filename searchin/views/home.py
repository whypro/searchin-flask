# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort, current_app

# from ..extensions import db
# from ..models import Manufacturer, Product

home = Blueprint('home', __name__)


@home.route('/')
def index():
    return 'string'
