import os
import sys
import shortuuid
import shutil
import tempfile
import subprocess
import magic
from zipfile import ZipFile
from rarfile import RarFile
from werkzeug import secure_filename
from flask import Blueprint, request, render_template, \
    url_for, send_file, redirect, abort, current_app as app, g
from flask.ext.wtf import Form
from wtforms import FileField, SelectField

from gerblook.utils import *
from gerblook.models import *
from gerblook.gerber import *

mod = Blueprint('main', __name__)

class UploadForm(Form):
    gerbers = FileField('Gerber Files')
    soldermask_color = SelectField('Soldermask Color')
    silkscreen_color = SelectField('Silkscreen Color')
    copper_color = SelectField('Copper Color')

@mod.route('/', methods=['GET', 'POST'])
def index():
    errors = []

    form = UploadForm()
    form.soldermask_color.choices = [(x, x) for x in app.config['SOLDERMASK_COLORS'].keys()]
    form.silkscreen_color.choices = [(x, x) for x in app.config['SILKSCREEN_COLORS'].keys()]
    form.copper_color.choices = [(x, x) for x in app.config['COPPER_COLORS'].keys()]

    if form.validate_on_submit():
        tempdir = tempfile.mkdtemp()
        gerberdir = os.path.join(tempdir, 'gerbers')
        os.mkdir(gerberdir)

        gerbers = []
        for f in request.files.getlist('gerbers'):
            mimetype = magic.from_buffer(f.read(1024), mime=True)
            f.seek(0)
            if mimetype == 'application/zip':
                archive = ZipFile(f)
                for member in archive.namelist():
                    safe_filename = secure_filename(member)
                    extracted_filename = os.path.join(gerberdir, safe_filename)
                    open(extracted_filename, 'wb').write(archive.read(member))
                    gerbers.append(safe_filename)
            elif mimetype == 'application/x-rar':
                archive_name = os.path.join(tempdir, secure_filename(f.filename))
                f.save(archive_name)
                archive = RarFile(archive_name)
                for member in archive.namelist():
                    safe_filename = secure_filename(member)
                    extracted_filename = os.path.join(gerberdir, safe_filename)
                    open(extracted_filename, 'wb').write(archive.read(member))
                    gerbers.append(safe_filename)
            elif mimetype == 'text/plain':
                safe_filename = secure_filename(f.filename)
                f.save(os.path.join(gerberdir, safe_filename))
                gerbers.append(safe_filename)
            else:
                shutil.rmtree(tempdir)
                errors.append('That was an unexpected file type. Please upload a zip, rar or selection of gerber files.')
                return render_template('index.html', errors=errors, form=form)

        layers = guess_layers(gerbers, gerberdir)
                
        if 'outline' not in layers.keys():
            errors.append("Couldn't find outline layer.")
        if 'top_copper' not in layers.keys():
            errors.append("Couldn't find top copper layer.")
        if 'top_soldermask' not in layers.keys():
            errors.append("Couldn't find top soldermask layer.")
        #if 'top_silkscreen' not in layers.keys():
        #    errors.append("Couldn't find top silkscreen layer.")
        if 'bottom_copper' not in layers.keys():
            errors.append("Couldn't find bottom copper layer.")
        if 'bottom_soldermask' not in layers.keys():
            errors.append("Couldn't find bottom soldermask layer.")
        #if 'bottom_silkscreen' not in layers.keys():
        #    errors.append("Couldn't find bottom silkscreen layer.")

        if errors:
            shutil.rmtree(tempdir)
        else:
            uid = str(shortuuid.uuid())
            basedir = os.path.join(app.config['DATA_DIR'], uid)
            shutil.move(tempdir, basedir)
            gerberdir = os.path.join(basedir, 'gerbers')
            imagedir = os.path.join(basedir, 'images')
            os.mkdir(imagedir)

            try:
                color_silkscreen = app.config['SILKSCREEN_COLORS'][form.silkscreen_color.data]
            except KeyError:
                color_silkscreen = '#eeeeeeee'

            try:
                color_background = app.config['SOLDERMASK_COLORS'][form.soldermask_color.data]
            except KeyError:
                color_background = '#225533'

            try:
                color_copper = app.config['COPPER_COLORS'][form.copper_color.data]
            except KeyError:
                color_copper = '#a0a0a0ff'


            # Calculate size of gerber and output images
            x, y = gerber_size(os.path.join(gerberdir, layers['outline'][0]), units='mm')
            area = x * y
            DPI = '200'
            if area == 0:
                DPI = '200'
            elif area < 500:
                DPI = '600'
            elif area < 1000:
                DPI = '500'
            elif area < 5000:
                DPI = '400'
            elif area < 10000:
                DPI = '300'
            elif area < 20000:
                DPI = '200'

            print 'Calculated area: %s' % area
            print 'Set DPI: %s' % DPI

            details = {
                'gerber_size': (x, y),
                'dpi': DPI,
                'color_silkscreen': color_silkscreen,
                'color_background': color_background,
                'color_copper': color_copper,
                'layers': layers,
                'rendered': False,
            }
            detail_file = os.path.join(basedir, 'details.json')
            json.dump(details, open(detail_file, 'w'))

            app.r.lpush('gerblook/renderqueue', uid)
            return redirect(url_for('.pcb', uid=uid))

    return render_template('index.html', errors=errors, form=form)

@mod.route('/pcb/<uid>', methods=['GET', 'POST'])
def pcb(uid):
    uid = secure_filename(uid)
    basedir = os.path.join(app.config['DATA_DIR'], uid)
    if not os.path.isdir(basedir):
        abort(404)

    detail_file = os.path.join(basedir, 'details.json')
    try:
        details = json.load(open(detail_file))
    except:
        details = {
            'rendered': True,
        }
    images = os.listdir(os.path.join(basedir, 'images'))

    noalpha = False
    if 'noalpha' in request.args:
        noalpha = True

    return render_template('pcb.html', uid=uid, images=images, noalpha=noalpha, details=details)

@mod.route('/pcb/<uid>/state.json', methods=['GET'])
def pcb_state(uid):
    uid = secure_filename(uid)
    basedir = os.path.join(app.config['DATA_DIR'], uid)
    if not os.path.isdir(basedir):
        abort(404)

    return jsonify(progress=app.r.get('gerblook/pcb/%s/render-progress' % uid),
        activity=app.r.get('gerblook/pcb/%s/render-activity' % uid),
        queue_length=app.r.llen('gerblook/renderqueue'))

@mod.route('/image/<uid>/<image>', methods=['GET'])
def image(uid, image):
    uid = secure_filename(uid)
    image = secure_filename(image)
    basedir = os.path.join(app.config['DATA_DIR'], uid)
    if not os.path.isdir(basedir):
        abort(404)

    image = os.path.join(basedir, 'images', image)
    if not os.path.exists(image):
        abort(404)

    return send_file(image)

@mod.route('/faq')
def faq():
    return render_template('faq.html')


