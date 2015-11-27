from flask import Blueprint, request, render_template, flash, \
  url_for, redirect, abort, current_app as app
from flask.ext.login import login_user, logout_user, login_required, current_user

from gerblook.utils import *
from gerblook.models import *

mod = Blueprint('user', __name__)

@mod.route('/<username>', methods=('GET',))
@login_required
def home(username):
  return render_template('home.html')

@mod.route('/<username>/projects', methods=('GET',))
@login_required
def projects(username):
  return render_template('projects.html')

