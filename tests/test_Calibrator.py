import os
from copy import deepcopy
from unittest import TestCase
import numpy as np

from src import path
from src.entities.SearchSettings import SearchSettings
from src.services.DataServices import SequenceService
from src.services.assign_services.AbstractSpectrumHandler import calculateError
from src.services.assign_services.Calibrator import Calibrator
from src.services.assign_services.Finders import TD_Finder
from src.services.library_services.IntactLibraryBuilder import IntactLibraryBuilder
from src.services.assign_services.IntactSpectrumHandler import IntactSpectrumHandler
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.assign_services.TD_SpectrumHandler import SpectrumHandler
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from tests.test_IntactFinder import initConfigurations, initTestSequences
from tests.top_down.test_SpectrumHandler import initTestLibraryBuilder


def getTestIntactSettings():
    settings = ConfigurationHandlerFactory.getFullIntactHandler().getAll()
    spectralFile = os.path.join(path, 'tests', 'test_files', '2511_neoRibo_3xRIO_CMCT_1.5mMPip_4mMIm_01_0.52.txt')
    calFile = os.path.join(path, 'tests', 'test_files', '2511_RIO_test.txt')
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
    spectrumHandler = IntactSpectrumHandler(settings, ConfigurationHandlerFactory.getConfigHandler().getAll())
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
        configHandlerRNA.update2('calIons', os.path.join(path, 'tests', 'test_files', '2511_RIO_test_0.txt'))

        #self._SNAP_list = os.path.join(path, 'test_files', 'intact', '2511_RIO_test_0.txt')
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
        spectrumHandler.addSpectrum(os.path.join(path, 'tests', 'test_files', 'dummySpectrum.txt'))
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

        configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        filePath = os.path.join(path, 'tests', 'test_files', 'CR_1_2_annealed_noMg_ESI_500mMDEPC_125min_Sk75_CAD12p5_134_uncal.txt')
        settings = {'sequName': 'CR_1_2', 'charge': -4, 'fragmentation': 'RNA_CAD', 'modifications': +134,
                    'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 10 ** 6, 'fragLib': '',
                    'calIons': os.path.join(path, 'tests', 'test_files', 'CR_1_2_annealed_noMg_ESI_500mMDEPC_125min_Sk75_CAD12p5_134_SNAP.txt')}
        props = SearchSettings(settings['sequName'], settings['fragmentation'], settings['modifications'])
        builder = FragmentLibraryBuilder(props, 1)
        builder.createFragmentLibrary()
        builder.addNewIsotopePattern()
        spectrumHandler = SpectrumHandler(props, builder.getPrecursor(), settings, configs)
        uncalibrated = deepcopy(spectrumHandler.getSpectrum())

        allSettings = dict(settings)
        allSettings.update(configs)
        calibrator = Calibrator(builder.getFragmentLibrary(), allSettings, spectrumHandler.getChargeRange)
        calibrated = calibrator.calibratePeaks(uncalibrated)
        for uncal, cal in zip(spectrumHandler.getSpectrum(), calibrated):
            self.assertNotEqual(uncal[0], cal[0])
            self.assertAlmostEqual(uncal[1], cal[1])

        finder1 = TD_Finder(builder.getFragmentLibrary(), settings, spectrumHandler.getChargeRange)
        finder2 = calibrator.getFinder()
        file = os.path.join(path, 'tests', 'test_files', 'CR_1_2_annealed_noMg_ESI_500mMDEPC_125min_Sk75_CAD12p5_134_SNAP_cal.txt')
        data = calibrator.getIonData()
        data['m/z'] = finder2.calibrate(data['m/z'], calibrator.getCalibrationValues()[0])
        #manCalData = np.array([row[0] for row in finder1.readFile(file)[0]])
        #for


        manCalIons = {(ion.getName(), ion.getCharge()):ion for ion in finder1.findIonsInSpectrum(0, configs['errorLimitCalib'], finder1.readFile(file)[0])}
        autoCalIons = {(ion.getName(), ion.getCharge()):ion for ion in finder2.findIonsInSpectrum(0, configs['errorLimitCalib'], data)}
        deviations, autoErrors, manErrors = [], [], []

        for key in manCalIons.keys():
            deviation = calculateError(autoCalIons[key].getMonoisotopic(),manCalIons[key].getMonoisotopic())
            '''if abs(deviation)> 0.1:
                print(deviation, autoCalIons[key].getMonoisotopic(), autoCalIons[key].getName())'''
            self.assertLess(abs(deviation),0.4)
            autoError = calculateError(autoCalIons[key].getMonoisotopic(),autoCalIons[key].getTheoMz())
            manError = calculateError(manCalIons[key].getMonoisotopic(),manCalIons[key].getTheoMz())
            if abs(manError) < 10:
                autoErrors.append(autoError)
                manErrors.append(manError)
                deviations.append(deviation)
        print(np.std(deviations), np.average([abs(error) for error in deviations]))

        self.assertLess(np.std(deviations),0.2)
        self.assertLess(np.average([abs(error) for error in deviations]),0.25)
        print(np.average([abs(error) for error in autoErrors]), np.average([abs(error) for error in manErrors]))
        self.assertLess(np.average([abs(error) for error in autoErrors]), np.average([abs(error) for error in manErrors]))

        #for hash in assignedIons: