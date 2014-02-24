from datetime import datetime

from flask import json, jsonify, make_response, g, current_app as app
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'

    def __repr__(self):
        return 'Project(%s)' % self.id

    id = db.Column(db.String(), primary_key=True, nullable=False)
    created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    name = db.Column(db.String(200))

