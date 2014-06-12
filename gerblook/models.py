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
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    enabled = db.Column(db.Boolean(), default=True, nullable=False)

    projects = db.relationship('Project', order_by=db.desc('projects.created'), backref='user')

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
    public = db.Column(db.Boolean(), default=True, nullable=False)
    expires = db.Column(db.DateTime())
    rendered = db.Column(db.Boolean(), default=False, nullable=False)
    store_gerbers = db.Column(db.Boolean(), default=True, nullable=False)
    width = db.Column(db.Float())
    height = db.Column(db.Float())
    layer_info = db.Column(db.Text())
    color_backgorund = db.Column(db.String(20))
    color_copper = db.Column(db.String(20))
    color_silkscreen = db.Column(db.String(20))

    user_id = db.Column(db.Integer(),
        db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'))

