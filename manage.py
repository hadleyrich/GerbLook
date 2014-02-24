#!/usr/bin/env python

import os
import readline, rlcompleter
import logging
from flask.ext.script import Manager, Server

from gerblook import create_app
from gerblook.models import *
from gerblook.utils import *

manager = Manager(create_app)

@manager.shell
def make_shell_context():
    app = manager.app()
    readline.parse_and_bind("tab: complete")
    data = globals()
    data.update(locals())
    return data

manager.add_command('runserver', Server(host='0.0.0.0', port=5000))

if __name__ == '__main__':
    manager.run(default_command='runserver')

