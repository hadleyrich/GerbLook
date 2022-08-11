import os
import re
import tempfile

from flask import current_app as app

from gerblook.utils import *

def guess_layers(filenames, gerberdir, logger=None):
  if not logger:
    logger = app.logger.debug
  layers = {}
  for filename in filenames:
    layer_result = guess_layer(filename, gerberdir)
    logger('Guessed %s for %s' % (layer_result, filename))
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

  match = re.search(r'\.gl?([1-7])$', filename)
  if match:
    return 'inner_%s' % match.group(1)

  match = re.search(r'inner([1-7])', filename)
  if match:
    return 'inner_%s' % match.group(1)

  match = re.search(r'in([1-7])_cu', filename)
  if match:
    return 'inner_%s' % match.group(1)

  match = re.search(r'internalplane([1-7])\.ger', filename)
  if match:
  	return 'inner_%s' % match.group(1)

  if re.search(r'(vcut|vscore).*?\.gbr', filename):
    return 'vcuts'

  if re.search(r'\.(dri|drl|drd|txt|drills\.xln)', filename):
    if filename.endswith('.dri'):
      data = open(os.path.join(gerberdir, path)).read(1024)
      if 'Drill Station Info File' in data:
        return
    if 'npth' in filename:
      return 'nonplated_drills'
    return 'plated_drills'

  # KiCad default naming
  match = re.search(r'-([^-_.]+)[._]([^.]+)\.gbr', filename)
  if match:
    l = None
    if match.group(1) == 'b':
      l = 'bottom_'
    elif match.group(1) == 'f':
      l = 'top_'
    elif match.group(1).startswith('in'):
      return 'inner_%s' % match.group(1)[2:]
    else:
      # Don't support this naming yet?
      pass

    if l:
      if match.group(2) == 'cu':
        return l+'copper'
      elif match.group(2) == 'mask':
        return l+'soldermask'
      elif match.group(2) == 'silks':
        return l+'silkscreen'
      elif match.group(2) == 'paste':
        return l+'paste'

  if re.search(r'\.(out|oln|gm1|gbr|gml|gko|gm16|boardoutline\.ger)', filename):
    return 'outline'

  if re.search(r'\.(gbl|sol|bot|bottomlayer\.ger)', filename):
    return 'bottom_copper'
  if re.search(r'\.(gbs|sts|smb|bottomsoldermask\.ger)', filename):
    return 'bottom_soldermask'
  if re.search(r'\.(gbo|ssb|bottomsilkscreen\.ger)', filename):
    return 'bottom_silkscreen'
  if re.search(r'\.(gbp|bcream\.ger)', filename):
    return 'bottom_paste'

  if re.search(r'\.(gtl|cmp|top|toplayer\.ger)', filename):
    return 'top_copper'
  if re.search(r'\.(gts|stc|smt|topsoldermask\.ger)', filename):
    return 'top_soldermask'
  if re.search(r'\.(gto|sst|topsilkscreen\.ger)', filename):
    return 'top_silkscreen'
  if re.search(r'\.(gtp|tcream\.ger)', filename):
    return 'top_paste'

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
  board = full_gerber_size(filename)
  return round(board['w'], 2), round(board['h'], 2)

def full_gerber_size(filename):
  """
  Calculate size of supplied gerber file in mm,mm

  Adapted from PHP code by Jonathan Georgino for Dangerous Prototypes. Thanks!
  """
  board = {}
  board['number_format'] = None
  board['coordinate_mode'] = None
  board['units'] = None

  board['x_min'] = 999999999
  board['y_min'] = 999999999
  board['x_max'] = -999999999
  board['y_max'] = -999999999

  f = open(filename)
  for line in f:
    if line.startswith('%FS'):
      if line[3:4] == 'L':
        board['number_format'] = 'Leading zeros omitted'
      elif line[3:4] == 'T':
        board['number_format'] = 'Trailing zeros omitted'
      else:
        board['number_format'] = 'unknown'

      if line[4:5] == 'A':
        board['coordinate_mode'] = 'absolute'
      elif line[4:5] == 'I':
        board['coordinate_mode'] = 'incremental'
      else:
        board['coordinate_mode'] = 'unknown'

      x_digs_before_decimal = int(line[6:7])
      x_digs_after_decimal = int(line[7:8])
      x_digs_total = x_digs_before_decimal + x_digs_after_decimal
      y_digs_before_decimal = int(line[9:10])
      y_digs_after_decimal = int(line[10:11])
      y_digs_total = y_digs_before_decimal + y_digs_after_decimal
    elif line.startswith('G70'): # Check for the Gcode for inches
      board['units'] = "in"
    elif line.startswith('G71'): # Check for the Gcode for mm
      board['units'] = "mm"
    elif line.startswith('%MOIN*%'): # Looking for units called out in the header, inches
      board['units'] = "in"
    elif line.startswith('%MOMM*%'): # Looking for units called out in the header, mm
      board['units'] = "mm"
    elif not line.startswith('%'): # It's not part of the header, track the coordinates for min and maximums
      x = None
      y = None

      # This case catches lines with both x and y values
      m = re.search(r'X(-?\d+)Y(-?\d+)', line, flags=re.IGNORECASE)
      if m:
        x = m.group(1)
        y = m.group(2)

      # This case catches lines with only x coords (y is unchanged)
      m = re.search(r'X(-?\d+)', line, flags=re.IGNORECASE)
      if m:
        x = m.group(1)

      # This case catches lines with only y coords (x is unchanged)
      m = re.search(r'Y(-?\d+)', line, flags=re.IGNORECASE)
      if m:
        y = m.group(1)


      if x is not None:
        multiplier = 1
        if x.startswith('-'):
          x = x[1:(len(x))]
          multiplier = -1
        if board['number_format'] == 'Leading zeros omitted':
          x = x.zfill(x_digs_total)
        elif board['number_format'] == 'Trailing zeros omitted':
          x = x + '0' * (x_digs_total - len(x))
        val = int(x[0:x_digs_before_decimal])
        if val < 0:
          x = val - (float(x[x_digs_before_decimal:x_digs_total]) / pow(10, x_digs_after_decimal))
        else:
          x = val + (float(x[x_digs_before_decimal:x_digs_total]) / pow(10, x_digs_after_decimal))
        x = x * multiplier
        if x < board['x_min']:
          board['x_min'] = x
        elif x > board['x_max']:
          board['x_max'] = x
      if y is not None:
        multiplier = 1
        if y.startswith('-'):
          y = y[1:len(y)]
          multiplier = -1
        if board['number_format'] == 'Leading zeros omitted':
          y = y.zfill(y_digs_total)
        elif board['number_format'] == 'Trailing zeros omitted':
          y = y + '0' * (y_digs_total - len(y))
        val = int(y[0:y_digs_before_decimal])
        if val < 0:
          y = val - (float(y[y_digs_before_decimal:y_digs_total]) / pow(10, y_digs_after_decimal))
        else:
          y = val + (float(y[y_digs_before_decimal:y_digs_total]) / pow(10, y_digs_after_decimal))
        y = y * multiplier
        if y < board['y_min']:
          board['y_min'] = y
        elif y > board['y_max']:
          board['y_max'] = y

  if board['x_min'] == 999999999 and board['y_min'] == 999999999:
    raise ValueError("Couldn't find size")
  if board['units'] is None:
    raise ValueError("Couldn't find units")
  if board['number_format'] is None:
    raise ValueError("Couldn't find number format")

  board['w_raw'] = board['x_max'] - board['x_min']
  board['h_raw'] = board['y_max'] - board['y_min']

  board['w'] = board['w_raw']
  board['h'] = board['h_raw']
  if board['units'] == 'in': # Convert inches to mm
    board['w'] = board['w'] * 25.4
    board['h'] = board['h'] * 25.4

  return board

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