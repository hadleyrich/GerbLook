from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask import json, jsonify, make_response, g, current_app as app
from flask.ext.sqlalchemy import SQLAlchemy

from utils import *

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    name = db.Column(db.String(100))
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    enabled = db.Column(db.Boolean(), default=True, nullable=False)

    projects = db.relationship('Project', backref='user')

    def __str__(self):
        return self.name or self.email

    def __repr__(self):
        return 'User(%s)' % self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256:1000')

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Project(db.Model):
    __tablename__ = 'projects'

    def __repr__(self):
        return 'Project(%s)' % self.id

    id = db.Column(db.String(), primary_key=True, nullable=False)
    created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    name = db.Column(db.String(100))
    slug = db.Column(db.String(50), unique=True)
    public = db.Column(db.Boolean(), default=True, nullable=False)

    user_id = db.Column(db.Integer(),
        db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)

