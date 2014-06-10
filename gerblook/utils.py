import subprocess
from datetime import datetime, timedelta

from flask import json, jsonify, make_response, g, current_app as app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def localtime(dt, tz=None):
    """
    Returns the time with tzinfo tz even if the datetime
    passed (dt) is a primitive type.
    """
    try:
        dt = pytz.utc.localize(dt)
        if tz:
            return dt.astimezone(tz)
        else:
            return dt.astimezone(app.tz)
    except Exception, e:
        return dt

def strftime(dt, format):
    try:
        return dt.strftime(str(format))
    except:
        return dt

def call(command='', args=[]):
    if command:
        args = command.split(' ')
    #print 'Calling: ', ' '.join(args)
    return subprocess.check_output(args, stderr=subprocess.STDOUT)

def base36encode(number):
    assert number >= 0, 'Positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))

def base36decode(number):
    return int(number, 36)

def rgb2hex(rgbcolor):
    """Convert a tuple of (r, g, b) to the hex equivilent."""
    return '#%02x%02x%02x' % rgbcolor

def hex2rgb(hexcolor):
    """Convert a hex color to a (r, g, b) tuple equivilent."""
    hexcolor = hexcolor.strip('\n\r #')
    if len(hexcolor) != 6:
        raise ValueError('Input #%s not in #rrggbb format' % hexcolor)
    r, g, b = hexcolor[:2], hexcolor[2:4], hexcolor[4:]
    return [int(n, 16) for n in (r, g, b)]

def adjustrgb(rgbcolor, percent):
    """
    Shift a color to a darker or lighter shade.
    
    This is a hack and will break on edge cases. Could be done more
    effectively by converting to HSL, adjusting, and converting back.
    """
    percent = 1 + (float(percent) / 100)
    return tuple(int(x * percent) for x in rgbcolor)

