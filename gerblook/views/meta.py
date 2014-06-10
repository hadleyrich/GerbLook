from flask import Blueprint, request, render_template, flash, \
    url_for, redirect, abort, current_app as app

from flask.ext.login import login_user, logout_user, login_required, current_user
from wtforms import TextField, PasswordField, SubmitField, validators
from flask.ext.wtf import Form

from gerblook.utils import *
from gerblook.models import *

mod = Blueprint('meta', __name__)

class LoginForm(Form):
    username = TextField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit_button = SubmitField('Login')

@mod.route('/login/', methods=('GET', 'POST'))
def login():
    form = LoginForm()

    data = {}
    if form.validate_on_submit():
        user = User.query.filter(User.email==form.username.data).first()
        if user:
            if user.check_password(form.password.data):
                login_user(user, remember=True)
                flash("Logged you in.", 'success')
                if 'next' in request.args:
                    return redirect(request.args['next'])
                else:
                    return redirect('/')
            else:
                flash("Sorry, we couldn't find your username and password combination.", category='warning')
        else:
            flash("Sorry, we couldn't find your username and password combination.", category='warning')

    return render_template('login.html', form=form, **data)

@mod.route('/logout/')
def logout():
    logout_user()
    return redirect('/')

