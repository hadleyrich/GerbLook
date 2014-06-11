import subprocess
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, make_msgid, parseaddr
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
    app.logger.debug('Calling: %s' % ' '.join(args))
    try:
        result = subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        app.logger.exception('Call failed: %s' % ' '.join(args))
    return result

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

def send_email(msg_to, msg_subject, msg_body, msg_from=None,
                smtp_server='localhost', envelope_from=None,
                headers={}):

    if not msg_from:
        msg_from = app.config['EMAIL_FROM']

    if not envelope_from:
        envelope_from = parseaddr(msg_from)[1]

    msg = MIMEText(msg_body)

    msg['Subject'] = Header(msg_subject)
    msg['From'] = msg_from
    msg['To'] = msg_to
    msg['Date'] = formatdate()
    msg['Message-ID'] = make_msgid()
    msg['Errors-To'] = envelope_from

    if request:
        msg['X-Submission-IP'] = request.remote_addr

    s = smtplib.SMTP(smtp_server)
    s.sendmail(envelope_from, msg_to, msg.as_string())
    s.close()

