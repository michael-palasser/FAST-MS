import os
from unittest import TestCase
import numpy as np

from src import path
from src.services.DataServices import SequenceService
from src.services.assign_services.Finders import IntactFinder
from src.services.library_services.IntactLibraryBuilder import IntactLibraryBuilder
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory


def initFinders():
    configHandlerRNA = initConfigurations()
    configHandlerRNA.update('sprayMode','negative')
    configHandlerRNA.update('sequName', 'neoRibo')
    configHandlerProt = initConfigurations()
    configHandlerProt.update('sprayMode','positive')
    configHandlerProt.update('sequName', 'dummyProt')
    finderRNA = IntactFinder(IntactLibraryBuilder(SequenceService().get(configHandlerRNA.get('sequName')), 'CMCT').createLibrary(), configHandlerRNA.getAll())
    finderProt = IntactFinder(IntactLibraryBuilder(SequenceService().get(configHandlerProt.get('sequName')), '-').createLibrary(), configHandlerProt.getAll())
    return finderRNA, configHandlerRNA, finderProt, configHandlerProt

def initConfigurations():
    configHandler = ConfigurationHandlerFactory.getIntactAssignHandler()
    configHandler.update('minMz',700)
    configHandler.update('maxMz',1600)
    configHandler.update2('errorLimitCalib',50)
    configHandler.update2('maxStd',2)
    configHandler.update2('k',2.)
    configHandler.update2('d',6.)
    return configHandler

def initTestSequences(sequenceService=SequenceService()):
    sequences = sequenceService.getSequences()
    names = [tup[0] for tup in sequences]
    if 'neoRibo' not in names:
        sequences.append(('neoRibo', 'GGCUGCUUGUCCUUUAAUGGUCCAGUC', 'RNA', len(sequences) + 1))
    if 'dummyProt' not in names:
        sequences.append(('dummyProt', 'GAPH', 'Protein', len(sequences) + 1))
    sequenceService.save(sequences)

class TestFinder(TestCase):
    #ToDo: test for protein
    def setUp(self):
        self.RNA_spectrum = os.path.join(path, 'tests', 'test_files', '2511_RIO_test.txt')
        try:
            self.finderRNA, self.configRNA, self.finderProt, self.configProt = initFinders()
        except:
            initTestSequences()
            self.finderRNA, self.configRNA, self.finderProt, self.configProt = initFinders()


    def test_read_file(self):
        self.finderRNA.readData([self.RNA_spectrum])
        self.assertEqual(4, len(self.finderRNA.getData()[0]))
        for spectrum in self.finderRNA.getData()[0]:
            self.assertGreater(len(spectrum),0)
            self.assertEqual(np.dtype([('m/z', np.float64), ('z', np.uint8), ('relAb', np.float64)]), spectrum.dtype)

    '''def test_get_mz(self):
        self.fail()

    def test_get_error_limit(self):
        self.fail()'''

    def test_find_ions(self):
        '''
        Also tests findIonsInSpectrum
        :return:
        '''
        self.finderRNA.readData([self.RNA_spectrum])
        self.finderRNA.calibrateAll()
        for ionList in self.finderRNA.findIons(self.configRNA.get('k'), self.configRNA.get('d'), True)[0]:
            self.assertGreater(len(ionList), 0)

    '''def test_fun_parabola(self):
        self.fail()'''

    def test_calibrate_all(self):
        '''
        Also tests findCalibrationFunction
        :return:
        '''
        self.finderRNA.readData([self.RNA_spectrum])
        errors1 = []
        for ionList in self.finderRNA.findIons(0, 50)[0]:
            errors1.append(np.abs(np.average([ion.getError() for ion in ionList])))
        self.finderRNA.calibrateAll()
        errors2, stddevs = [], []
        for ionList in self.finderRNA.findIons(0, 50)[0]:
            errors = np.array([ion.getError() for ion in ionList if abs(ion.getError()) < 30])
            errors2.append(np.abs(np.average(errors)))
            stddevs.append(np.std(errors))
        for i in range(len(errors1)):
            self.assertLess(errors2[i],errors1[i])
            #print(stddevs[i], errors2[i],errors1[i])
            self.assertLess(errors2[i],1)
            self.assertLess(stddevs[i],2)

