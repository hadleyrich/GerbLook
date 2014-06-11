from flask import Blueprint, request, render_template, flash, \
    url_for, redirect, abort, current_app as app

from flask.ext.login import login_user, logout_user, login_required, current_user
from wtforms import TextField, PasswordField, SubmitField, validators
from flask.ext.wtf import Form

from gerblook.utils import *
from gerblook.models import *

mod = Blueprint('meta', __name__)

class LoginForm(Form):
    user = TextField('Username or Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

class SignupForm(Form):
    username = TextField('Username', [validators.DataRequired(), validators.Length(min=4, max=50),
        validators.Regexp(r'^[A-Za-z0-9-]+$',
        message='Usernames may only contain alphanumeric characters or dashes.')])
    email = TextField('Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=8)])

@mod.route('/signup', methods=('GET', 'POST'))
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        email_dupe = User.query.filter(User.email==form.email.data).first()
        username_dupe = User.query.filter(User.username==form.username.data).first()
        if username_dupe:
            flash("Sorry, that username is either invalid or already in use.", category='error')
        elif email_dupe:
            flash("Sorry, that email is either invalid or already in use.", category='error')
        else:
            user = User()
            user.username = form.username.data
            user.email = form.email.data
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash("Thanks for signing up, you're all signed in and ready to go.", category='success')
            return redirect('/')

    return render_template('signup.html', form=form)

@mod.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter(db.or_(User.email==form.user.data, User.username==form.user.data)).first()
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

    return render_template('login.html', form=form)

@mod.route('/logout')
def logout():
    logout_user()
    return redirect('/')

