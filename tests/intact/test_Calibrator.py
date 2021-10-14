import os
from copy import deepcopy
from unittest import TestCase

from src import path
from src.intact.IntactFinder import Calibrator
from src.intact.IntactLibraryBuilder import IntactLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler
from tests.intact.test_IntactFinder import initConfigurations, initTestSequences
from tests.top_down.test_SpectrumHandler import initTestLibraryBuilder


class TestCalibrator(TestCase):
    def setUp(self):
        configHandlerRNA = initConfigurations()
        configHandlerRNA.update('sprayMode', 'negative')
        configHandlerRNA.update('sequName', 'neoRibo')
        configHandlerRNA.update('spectralData', os.path.join(path, 'tests', 'intact', '2511_RIO_test_0.txt'))
        #self._SNAP_list = os.path.join(path, 'tests', 'intact', '2511_RIO_test_0.txt')
        try:
            self._calibrator = Calibrator(IntactLibraryBuilder(configHandlerRNA.get('sequName'), 'CMCT').createLibrary(),
                       configHandlerRNA)
        except:
            initTestSequences()
            self._calibrator = Calibrator(IntactLibraryBuilder(configHandlerRNA.get('sequName'), 'CMCT').createLibrary(),
                       configHandlerRNA)

    def test_init(self):
        pass

    def test_calibrate_peaks(self):
        configs, settings, props, builder = initTestLibraryBuilder()
        spectrumHandler = SpectrumHandler(props, builder.getPrecursor(), settings)
        spectrumHandler.addSpectrum(os.path.join(path, 'tests', 'top_down', 'dummySpectrum.txt'))
        uncalibrated = deepcopy(spectrumHandler.getSpectrum())
        calibrated = self._calibrator.calibratePeaks(uncalibrated)
        for uncal, cal in zip(spectrumHandler.getSpectrum(), calibrated):
            self.assertNotEqual(uncal[0], cal[0])
            self.assertAlmostEqual(uncal[1], cal[1])