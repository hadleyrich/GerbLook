import os
import re
import tempfile

from flask import current_app as app

from gerblook.utils import *

def guess_layers(filenames, gerberdir):
    layers = {}
    for filename in filenames:
        layer_result = guess_layer(filename, gerberdir)
        app.logger.debug('Guessed %s for %s' % (layer_result, filename))
        if layer_result:
            if layer_result in layers:
                layers[layer_result].append(filename)
            else:
                layers[layer_result] = [filename]
    if 'nonplated_drills' in layers:
        layers['nonplated_drills'].sort(key=lambda f: os.path.splitext(f)[1])
    if 'plated_drills' in layers:
        layers['plated_drills'].sort(key=lambda f: os.path.splitext(f)[1])
        
    return layers

def guess_layer(path, gerberdir):
    """Try and guess the type of gerber file from the given filename"""

    filename = path.lower()

    if re.search(r'\.(gpi)', filename):
        return

    if 'mfgcode' in filename:
        return

    if 'inner1' in filename:
        return 'inner_1'
    if 'inner2' in filename:
        return 'inner_2'
    if 'inner3' in filename:
        return 'inner_3'
    if 'inner4' in filename:
        return 'inner_4'
    if re.search(r'(vcut|vscore).*?\.gbr', filename):
        return 'vcut'

    if re.search(r'\.(dri|drl|drd|txt)', filename):
        if filename.endswith('.dri'):
            data = open(os.path.join(gerberdir, path)).read(1024)
            if 'Drill Station Info File' in data:
                return
        if 'npth' in filename:
            return 'nonplated_drills'
        return 'plated_drills'
    if re.search(r'\.out|\.oln|\.gm1|\.gbr|\.gml|\.gko|\.gm16', filename):
        return 'outline'

    if re.search(r'\.(gbl)', filename):
        return 'bottom_copper'
    if re.search(r'\.(gbs)', filename):
        return 'bottom_soldermask'
    if re.search(r'\.(gbo)', filename):
        return 'bottom_silkscreen'
    if re.search(r'\.(gbp)', filename):
        return 'bottom_paste'

    if re.search(r'\.(gtl)', filename):
        return 'top_copper'
    if re.search(r'\.(gts)', filename):
        return 'top_soldermask'
    if re.search(r'\.(gto)', filename):
        return 'top_silkscreen'
    if re.search(r'\.(gtp)', filename):
        return 'top_paste'

    if re.search(r'\.(g1|gl1)', filename):
        return 'inner_1'
    if re.search(r'\.(g2|gl2)', filename):
        return 'inner_2'
    if re.search(r'\.(g3|gl3)', filename):
        return 'inner_3'
    if re.search(r'\.(g4|gl4)', filename):
        return 'inner_4'

    if re.search(r'outline', filename):
        return 'outline'

    if 'bot' in filename and 'copper' in filename:
        return 'bottom_copper'
    if 'bot' in filename and 'solder' in filename:
        return 'bottom_soldermask'
    if 'bot' in filename and 'silk' in filename:
        return 'bottom_silkscreen'
    if 'bot' in filename and 'paste' in filename:
        return 'bottom_paste'

    if 'top' in filename and 'copper' in filename:
        return 'top_copper'
    if 'top' in filename and 'solder' in filename:
        return 'top_soldermask'
    if 'top' in filename and 'silk' in filename:
        return 'top_silkscreen'
    if 'top' in filename and 'paste' in filename:
        return 'top_paste'

def approx_gerber_size(filename):

    outfile = tempfile.mkstemp()[1]
    args = ['gerbv', '-x', 'png', '-D', '1000', '-o', outfile, '-b', '#ffffff']
    args += ['-f', '#000000ff', filename]
    result = call(args=args)

    args = ['convert', outfile, '-trim', outfile]
    result = call(args=args)

    args = ['identify', '-format', '%w,%h', outfile]
    result = call(args=args)
    w, h = result.split(',')

    os.unlink(outfile)

    return (int(w) * 0.0254, int(h) * 0.0254)

def gerber_size(filename, units=None):
    """
    Calculates the overall size of a gerber file.
    
    Adapted from code by Matthew Beckler
    http://www.wayneandlayne.com/blog/2013/04/02/
    """
    xmin = None
    xmax = None
    ymin = None
    ymax = None

    with open(filename, 'r') as fid:
        for line in fid:
            results = re.search("^(G\d+)?X(?P<x>\d+)Y(?P<y>[\d-]+)", line)
            if results:
                x = int(results.group('x'))
                y = int(results.group('y'))
                if not xmin or x < xmin:
                    xmin = x
                if not ymin or y < ymin:
                    ymin = y
                if not xmax or x > xmax:
                    xmax = x
                if not ymax or y > ymax:
                    ymax = y

    if not xmin or not xmax or not ymin or not ymax:
        return (0, 0)

    w = xmax - xmin
    h = ymax - ymin

    if units == "mm":
        return (w * 0.00254, h * 0.00254)
    if units == "inch":
        return (w / 10000.0, h / 10000.0)
    return (w, h)

