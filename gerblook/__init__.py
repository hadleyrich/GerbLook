#TODO
# Database
# Pretty template
# AJAX Upload

import os
import sys

import redis
from flask import Flask, request, g

from models import *

SECRET_KEY = 'FIXME PLEASE!'
DEBUG = True
DATA_DIR = '/tmp/gerblook/'
#IMAGE_SIZE = '500x500'
SOLDERMASK_COLORS = {
    'Green': '#225533',
    'Red': '#cc0000',
    'Blue': '#00284a',
    'Yellow': '#edd400',
    'Black': '#2d2d2d',
    'White': '#e6e6e6',
}
SILKSCREEN_COLORS = {
    'Black': '#1d1d1dff',
    'White': '#eeeeeeff',
}
COPPER_COLORS = {
    'Silver': '#a0a0a0ff',
    'Gold': '#e3bd91ff',
}
def create_app():
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.config.from_envvar('GERBLOOK_SETTINGS', silent=True)
    app.r = redis.StrictRedis()

    if not os.path.isdir(app.config['DATA_DIR']):
        try:
            os.mkdir(app.config['DATA_DIR'])
        except OSError:
            sys.stderr.write('Unable to create DATA_DIR\n')
            sys.exit(2)

    db.init_app(app)
    @app.before_first_request
    def setup():
        db.create_all()

    from gerblook.views.main import mod
    app.register_blueprint(mod)
    return app

