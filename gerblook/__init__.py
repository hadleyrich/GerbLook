import os
import sys
import pytz
import redis
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask import Flask, request, g
from flask.ext.login import current_user

from utils import *
from models import *

SECRET_KEY = 'FIXME PLEASE!'
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

  log_file = app.config.get('LOG_FILE', None)
  if log_file:
    handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=99)
    handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s '
      '[in %(pathname)s:%(lineno)d]'))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

  app.r = redis.StrictRedis()

  login_manager.setup_app(app)
  login_manager.login_view = 'meta.login'

  if not os.path.isdir(app.config['DATA_DIR']):
    try:
      os.mkdir(app.config['DATA_DIR'])
    except OSError:
      sys.stderr.write('Unable to create DATA_DIR\n')
      sys.exit(2)

  app.tz = pytz.utc
  if 'TIMEZONE' in app.config:
    app.tz = pytz.timezone(app.config['TIMEZONE'])

  app.jinja_env.filters['strftime'] = strftime
  app.jinja_env.filters['localtime'] = localtime

  db.init_app(app)
  @app.before_first_request
  def setup():
    db.create_all()

  from gerblook.views.main import mod
  app.register_blueprint(mod)
  from gerblook.views.user import mod
  app.register_blueprint(mod)
  from gerblook.views.meta import mod
  app.register_blueprint(mod)
  return app

