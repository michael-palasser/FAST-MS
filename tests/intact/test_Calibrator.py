import os
from copy import deepcopy
from unittest import TestCase

from src import path
from src.services.DataServices import SequenceService
from src.services.assign_services.Calibrator import Calibrator
from src.services.library_services.IntactLibraryBuilder import IntactLibraryBuilder
from src.services.assign_services.IntactSpectrumHandler import IntactSpectrumHandler
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.assign_services.TD_SpectrumHandler import SpectrumHandler
from tests.intact.test_IntactFinder import initConfigurations, initTestSequences
from tests.top_down.test_SpectrumHandler import initTestLibraryBuilder


def getTestIntactSettings():
    settings = ConfigurationHandlerFactory.getFullIntactHandler().getAll()
    spectralFile = os.path.join(path, 'tests', 'intact', '2511_neoRibo_3xRIO_CMCT_1.5mMPip_4mMIm_01_0.52.txt')
    calFile = os.path.join(path, 'tests', 'intact', '2511_RIO_test.txt')
    try:
        settings.update({'sequName': 'neoRibo', 'modifications': 'CMCT', 'calibration': True,
                         'spectralData': spectralFile, "calIons": calFile, 'noiseLimit': 520000, 'sprayMode':'negative',
                         'minMz': 400, 'maxMz': 1600, 'errorLimitCalib':50, 'k':2, 'd':6, 'maxStd':2})
    except:
        settings = ConfigurationHandlerFactory.getIntactHandler().getAll()
        settings.update({'sequName': 'neoRibo', 'modifications': 'CMCT', 'calibration': True,
                         'spectralData': spectralFile, "calIons": calFile, 'noiseLimit': 520000, 'sprayMode':'negative',
                         'minMz': 400, 'maxMz': 1600})
    return settings

def getTestIntactLibraryBuilder(settings):
    libraryBuilder = IntactLibraryBuilder(SequenceService().get(settings['sequName']), settings['modifications'])
    libraryBuilder.createLibrary()
    libraryBuilder.addNewIsotopePattern()
    return libraryBuilder

def getCalibratedSpectrum():
    settings = getTestIntactSettings()
    libraryBuilder = getTestIntactLibraryBuilder(settings)
    spectrumHandler = IntactSpectrumHandler(settings, ConfigurationHandlerFactory.getTD_ConfigHandler().getAll())
    calibrator = Calibrator(libraryBuilder.getNeutralLibrary(), settings)
    uncalibrated = deepcopy(spectrumHandler.getSpectrum())
    calSpectrum = calibrator.calibratePeaks(spectrumHandler.getSpectrum())
    return {'uncalibrated':uncalibrated, 'calSpectrum':calSpectrum, 'calibrator':calibrator,
            'spectrumHandler':spectrumHandler,'settings':settings, 'libraryBuilder':libraryBuilder,
            'foundIons':calibrator.getFinder().findIonsInSpectrum(4.5,0.5, calibrator.getIonData())}

class TestCalibrator(TestCase):
    def setUp(self):
        configHandlerRNA = initConfigurations()
        configHandlerRNA.update('sprayMode', 'negative')
        configHandlerRNA.update('sequName', 'neoRibo')
        configHandlerRNA.update2('calIons', os.path.join(path, 'tests', 'intact', '2511_RIO_test_0.txt'))

        #self._SNAP_list = os.path.join(path, 'tests', 'intact', '2511_RIO_test_0.txt')
        try:
            self._calibrator = Calibrator(IntactLibraryBuilder(SequenceService().get(configHandlerRNA.get('sequName')),
                                                               'CMCT').createLibrary(),
                       configHandlerRNA.getAll())
        except:
            initTestSequences()
            self._calibrator = Calibrator(IntactLibraryBuilder(SequenceService().get(configHandlerRNA.get('sequName')),
                                                               'CMCT').createLibrary(),
                       configHandlerRNA.getAll())

    def test_init(self):
        pass

    def test_calibrate_peaks(self):
        configs, settings, props, builder = initTestLibraryBuilder()
        spectrumHandler = SpectrumHandler(props, builder.getPrecursor(), settings, configs)
        spectrumHandler.addSpectrum(os.path.join(path, 'tests', 'top_down', 'dummySpectrum.txt'))
        uncalibrated = deepcopy(spectrumHandler.getSpectrum())
        calibrated = self._calibrator.calibratePeaks(uncalibrated)
        for uncal, cal in zip(spectrumHandler.getSpectrum(), calibrated):
            self.assertNotEqual(uncal[0], cal[0])
            self.assertAlmostEqual(uncal[1], cal[1])
        #intact:
        d = getCalibratedSpectrum()
        for uncal, cal in zip(d['uncalibrated'], d['calSpectrum']):
            self.assertNotEqual(uncal[0], cal[0])
            self.assertAlmostEqual(uncal[1], cal[1])