import os
from unittest import TestCase
import numpy as np

from src import path
from src.Services import SequenceService
from src.entities.GeneralEntities import Sequence
from src.intact.IntactFinder import Finder
from src.intact.IntactLibraryBuilder import IntactLibraryBuilder
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory


def initFinders():
    configHandlerRNA = initConfigurations()
    configHandlerRNA.update('sprayMode','negative')
    configHandlerRNA.update('sequName', 'neoRibo')
    configHandlerProt = initConfigurations()
    configHandlerProt.update('sprayMode','positive')
    configHandlerProt.update('sequName', 'dummyProt')
    finderRNA = Finder(IntactLibraryBuilder(configHandlerRNA.get('sequName'), 'CMCT').createLibrary(), configHandlerRNA)
    finderProt = Finder(IntactLibraryBuilder(configHandlerProt.get('sequName'), '-').createLibrary(), configHandlerProt)
    return finderRNA, configHandlerRNA, finderProt, configHandlerProt

def initConfigurations():
    configHandler = ConfigurationHandlerFactory.getIntactHandler()
    configHandler.update('minMz',700)
    configHandler.update('maxMz',1600)
    configHandler.update('errorLimitCalib',50)
    configHandler.update('k',2.)
    configHandler.update('d',6.)
    return configHandler

def initTestSequences(sequenceService=SequenceService()):
    sequences = [Sequence(tup[0], tup[1], tup[2], i) for i, tup in
                 enumerate(sequenceService.getSequences())]
    sequences.append(Sequence('neoRibo', 'GGCUGCUUGUCCUUUAAUGGUCCAGUC', 'RNA', len(sequences) + 1))
    sequences.append(Sequence('dummyProt', 'GAPH', 'Protein', len(sequences) + 1))
    sequenceService.save(sequences)

class TestFinder(TestCase):
    #ToDo: test for protein
    def setUp(self):
        self.RNA_spectrum = os.path.join(path, 'tests', 'intact', '2511_RIO_test.txt')
        try:
            self.finderRNA, self.configRNA, self.finderProt, self.configProt = initFinders()
        except:
            initTestSequences()
            self.finderRNA, self.configRNA, self.finderProt, self.configProt = initFinders()


    def test_read_data(self):
        with open(self.RNA_spectrum,'r') as f:
            self.finderRNA.readData(f)
        self.assertEqual(4, len(self.finderRNA.getData()))
        for spectrum in self.finderRNA.getData():
            self.assertGreater(len(spectrum),0)
            self.assertEqual(np.dtype([('m/z', np.float64), ('z', np.uint8), ('relAb', np.float64)]), spectrum.dtype)

    '''def test_get_mz(self):
        self.fail()

    def test_get_error_limit(self):
        self.fail()'''

    def test_find_ions(self):
        with open(self.RNA_spectrum,'r') as f:
            self.finderRNA.readData(f)
        self.finderRNA.calibrate()
        for ionList in self.finderRNA.findIons(self.configRNA.get('k'), self.configRNA.get('d'), True):
            self.assertGreater(len(ionList), 0)

    '''def test_fun_parabola(self):
        self.fail()'''

    def test_calibrate(self):
        with open(self.RNA_spectrum,'r') as f:
            self.finderRNA.readData(f)
        errors1 = []
        for ionList in self.finderRNA.findIons(0, 50):
            errors1.append(np.abs(np.average([ion.calculateError() for ion in ionList])))
        self.finderRNA.calibrate()
        errors2, stddevs = [], []
        for ionList in self.finderRNA.findIons(0, 50):
            errors = np.array([ion.calculateError() for ion in ionList if abs(ion.calculateError()) < 30])
            errors2.append(np.abs(np.average(errors)))
            stddevs.append(np.std(errors))
        for i in range(len(errors1)):
            self.assertLess(errors2[i],errors1[i])
            #print(stddevs[i], errors2[i],errors1[i])
            self.assertLess(errors2[i],1)
            self.assertLess(stddevs[i],2)
