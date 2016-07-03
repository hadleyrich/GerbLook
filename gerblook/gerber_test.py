import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import unittest

from gerblook import gerber

def logger(msg):
  print msg


class GuessLayerTest(unittest.TestCase):
  FILES_SIMPLE = [
    # Default names for KiCad 4.0.2, 2 layer design
    {
      'bottom_copper':     ['design-B.Cu.gbr'],
      'bottom_paste':      ['design-B.Paste.gbr'],
      'bottom_silkscreen': ['design-B.SilkS.gbr'],
      'bottom_soldermask': ['design-B.Mask.gbr'],
      'inner_1':           ['design-In1.Cu.gbr'],
      'inner_2':           ['design-In2.Cu.gbr'],
      'outline':           ['design-Edge.Cuts.gbr'],
      'top_copper':        ['design-F.Cu.gbr'],
      'top_paste':         ['design-F.Paste.gbr'],
      'top_silkscreen':    ['design-F.SilkS.gbr'],
      'top_soldermask':    ['design-F.Mask.gbr'],
    },
    {
      'bottom_copper':     ['design-one-B.Cu.gbr'],
      'bottom_paste':      ['design-one-B.Paste.gbr'],
      'bottom_silkscreen': ['design-one-B.SilkS.gbr'],
      'bottom_soldermask': ['design-one-B.Mask.gbr'],
      'inner_1':           ['design-one-In1.Cu.gbr'],
      'inner_2':           ['design-one-In2.Cu.gbr'],
      'outline':           ['design-one-Edge.Cuts.gbr'],
      'top_copper':        ['design-one-F.Cu.gbr'],
      'top_paste':         ['design-one-F.Paste.gbr'],
      'top_silkscreen':    ['design-one-F.SilkS.gbr'],
      'top_soldermask':    ['design-one-F.Mask.gbr'],
    },

    # "Protel File names"
    {
      'bottom_copper':     ['design.gbl'],
      'bottom_paste':      ['design.gbp'],
      'bottom_silkscreen': ['design.gbo'],
      'bottom_soldermask': ['design.gbs'],
      'inner_2':           ['design.g2'],
      'inner_3':           ['design.g3'],
      'outline':           ['design.gm1'],
      'top_copper':        ['design.gtl'],
      'top_paste':         ['design.gtp'],
      'top_silkscreen':    ['design.gto'],
      'top_soldermask':    ['design.gts'],
    },

    #('design-one-NPTH.drl', '-NPTH.drl'),
    #('design-one-NPTH-drl_map.plt', '-NPTH-drl_map.plt'),
    #('design-one.drl
    #('design-one-drl_map.plt', '-drl_map.plt'),
  ]

  def testSingleFilesSimple(self):
    for testcase in self.FILES_SIMPLE:
      for expected_type in testcase:
        for fname in testcase[expected_type]:
          actual_type = gerber.guess_layer(fname, None)
          self.assertEqual(
            actual_type, expected_type,
            "%s should return %s but got %s" % (fname, expected_type, actual_type))

  def testMultiFilesSimple(self):
    for testcase in self.FILES_SIMPLE:
      files = []
      for expected_type in testcase:
        for fname in testcase[expected_type]:
          files.append(fname)

      actual = gerber.guess_layers(files, None, logger)
      self.assertItemsEqual(actual, testcase)


if __name__ == '__main__':
    unittest.main()
