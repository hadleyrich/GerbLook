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

def gerbv_gerber_size(filename):

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

def gerber_size(filename):
    """
    Calculate size of supplied gerber file in mm,mm

    Adapted from PHP code by Jonathan Georgino for Dangerous Prototypes. Thanks!
    """
    board = {}
    board['number_format'] = 'unknown'
    board['coordinate_mode'] = 'unknown'
    board['units'] = 'unknown'

    numformat = 'L' # default
    coordmode = 'A' # default

    units = None

    min_x_pt = 999999999
    min_y_pt = 999999999
    max_x_pt = -999999999
    max_y_pt = -999999999

    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('%FS'):
                numformat = line[3:4]
                if numformat == 'L':
                    board['number_format'] = 'Leading zeros omitted'
                elif numformat == 'T':
                    board['number_format'] = 'Trailing zeros omitted'
                elif numformat == 'D':
                    board['number_format'] = 'Explicit decimal point'

                coordmode = line[4:5]
                if coordmode == 'A':
                    board['coordinate_mode'] = 'absolute'
                elif coordmode == 'I':
                    board['coordinate_mode'] = 'incremental'
                else:
                    board['coordinate_mode'] = 'unknown'

                x_digs_before_decimal = int(line[6:7])
                x_digs_after_decimal = int(line[7:8])
                y_digs_before_decimal = int(line[9:10])
                y_digs_after_decimal = int(line[10:11])
            elif line.startswith('G70'): # Check for the Gcode for inches
                units = "in"
            elif line.startswith('G71'): # Check for the Gcode for mm
                units = "mm"
            elif line.startswith('%MOIN*%'): # Looking for units called out in the header, inches
                units = "in"
            elif line.startswith('%MOMM*%'): # Looking for units called out in the header, mm
                units = "mm"
            elif line.startswith('%*MOMM*%'): # Looking for units called out in the header, mm
                print 'This happened: %*MOMM*%'
                units = "mm"

            if not line.startswith('%'): # It's not part of the header, track the coordinates for min and maximums
                # This case catches lines with both x and y values
                m = re.search(r'X(-?\d+)Y(-?\d+)', line, flags=re.IGNORECASE)
                if m:
                    x = int(m.group(1))
                    y = int(m.group(2))
                    if numformat == 'T':  # This adjusts for the case of Trailing zeros omitted
                        x = x * pow(10, (x_digs_before_decimal + x_digs_after_decimal) - len(m.group(1)))
                        y = y * pow(10, (y_digs_before_decimal + y_digs_after_decimal) - len(m.group(2)))

                    if x < min_x_pt:
                        min_x_pt = x
                    elif x > max_x_pt:
                        max_x_pt = x

                    if y < min_y_pt:
                        min_y_pt = y
                    elif y > max_y_pt:
                        max_y_pt = y

                # This case catches lines with only x coords (y is unchanged)
                m = re.search(r'X(-?\d+)', line, flags=re.IGNORECASE)
                if m:
                    x = int(m.group(1))
                    if numformat == 'T': # This adjusts for the case of Trailing zeros omitted
                        x = x * pow(10, (x_digs_before_decimal + x_digs_after_decimal) - len(m.group(1)))

                    if x < min_x_pt:
                        min_x_pt = x
                    elif x > max_x_pt:
                        max_x_pt = x

                # This case catches lines with only y coords (x is unchanged)
                m = re.search(r'Y(-?\d+)', line, flags=re.IGNORECASE)
                if m:
                    y = int(m.group(1))
                    if numformat == 'T': # This adjusts for the case of Trailing zeros omitted
                        y = y * pow(10, (y_digs_before_decimal + y_digs_after_decimal) - len(m.group(1)))

                    if y < min_y_pt:
                        min_y_pt = y
                    elif y > max_y_pt:
                        max_y_pt = y

    if min_x_pt == 999999999 and min_y_pt == 999999999:
        raise ValueError("Couldn't find size")
    if units is None:
        raise ValueError("Couldn't find units")

    board['x_min'] = min_x_pt / pow(10, x_digs_after_decimal)
    board['x_max'] = max_x_pt / pow(10, x_digs_after_decimal)
    board['y_min'] = min_y_pt / pow(10, y_digs_after_decimal)
    board['y_max'] = max_y_pt / pow(10, y_digs_after_decimal)
    board['w_raw'] = (max_x_pt - min_x_pt) / pow(10, x_digs_after_decimal)
    board['h_raw'] = (max_y_pt - min_y_pt) / pow(10, y_digs_after_decimal)
    board['units'] = units

    board['w_mm'] = (max_x_pt - min_x_pt) / pow(10, x_digs_after_decimal)
    board['h_mm'] = (max_y_pt - min_y_pt) / pow(10, y_digs_after_decimal)
    if units == 'in': # Convert inches to mm
        board['w_mm'] = board['w_mm'] * 25.4
        board['h_mm'] = board['h_mm'] * 25.4

    return round(board['w_mm'], 2), round(board['h_mm'], 2)

def approx_gerber_size(filename, units=None):
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

