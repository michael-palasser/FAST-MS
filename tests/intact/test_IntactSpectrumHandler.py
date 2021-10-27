import os
from unittest import TestCase

from src import path
from src.intact.IntactSpectrumHandler import IntactSpectrumHandler


class TestIntactSpectrumHandler(TestCase):
    def test_get_charge_range(self):
        filePath = os.path.join(path, 'tests', 'top_down', 'dummySpectrum.txt')
        handler = IntactSpectrumHandler({'minMz':300,'maxMz':1500, 'sprayMode':1, 'spectralData':filePath, 'noiseLimit': 10 ** 6})
        range = handler.getChargeRange(5000)
        self.assertEqual(4, range[0])
        self.assertEqual(16, range[-1])

    def test_find_ions(self):
        self.fail()
