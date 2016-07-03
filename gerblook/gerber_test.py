import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import unittest

from gerblook import gerber

class GuessLayerTest(unittest.TestCase):
  FILES_SIMPLE = [
    # Default names for KiCad 4.0.2, 2 layer design
    ('design-B.Cu.gbr',      'bottom_copper'),
    ('design-B.Mask.gbr',    'bottom_soldermask'),
    ('design-B.Paste.gbr',   'bottom_paste'),
    ('design-B.SilkS.gbr',   'bottom_silkscreen'),
    ('design-Edge.Cuts.gbr', 'outline'),
    ('design-F.Cu.gbr',      'top_copper'),
    ('design-F.Mask.gbr',    'top_soldermask'),
    ('design-F.Paste.gbr',   'top_paste'),
    ('design-F.SilkS.gbr',   'top_silkscreen'),
    ('design-In1.Cu.gbr',    'inner_1'),
    ('design-In2.Cu.gbr',    'inner_2'),

    # "Protel File names"
    ('design.gbl', 'bottom_copper'),
    ('design.gbs', 'bottom_soldermask'),
    ('design.gbp', 'bottom_paste'),
    ('design.gbo', 'bottom_silkscreen'),
    ('design.gm1', 'outline'),
    ('design.gtl', 'top_copper'),
    ('design.gts', 'top_soldermask'),
    ('design.gtp', 'top_paste'),
    ('design.gto', 'top_silkscreen'),
    ('design.g2',  'inner_2'),
    ('design.g3',  'inner_3'),

    #('design-NPTH.drl', '-NPTH.drl'),
    #('design-NPTH-drl_map.plt', '-NPTH-drl_map.plt'),
    #('design.drl
    #('design-drl_map.plt', '-drl_map.plt'),
  ]

  def testFilesSimple(self):
    for fname, expected in GuessLayerTest.FILES_SIMPLE:
      actual = gerber.guess_layer(fname, None)
      self.assertEqual(expected, actual, "%s should return %s but got %s" % (fname, expected, actual))

if __name__ == '__main__':
    unittest.main()
