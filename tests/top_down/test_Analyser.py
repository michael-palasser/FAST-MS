import sys
from copy import deepcopy
from unittest import TestCase
import numpy as np
from PyQt5.QtWidgets import QApplication

from src.entities.Ions import FragmentIon, Fragment
from src.gui.widgets.SequCovWidget import SequCovWidget
from src.services.analyser_services.Analyser import Analyser
from tests.top_down.test_IntensityModeller import initTestSpectrumHandler


class TestAnalyser(TestCase):
    def setUp(self):
        self.configs, settings, self.props, builder, self.spectrumHandler = initTestSpectrumHandler()
        fragments = builder.getFragmentLibrary()
        #self.spectrumHandler.setNormalisationFactor(self.spectrumHandler.getNormalizationFactor())
        self.ions = {}
        for fragment in fragments:
            zRange = self.spectrumHandler.getChargeRange(fragment)
            for z in zRange:
                ion = FragmentIon(fragment, 1., z, fragment.getIsotopePattern(), 10e5)
                self.ions[ion.getHash()] = ion
        self.analyser = Analyser([], self.props.getSequenceList(), settings['charge'],
                                 self.props.getModifPattern().getModification())

    def test_calculate_rel_abundance_of_species(self):
        typeDict = {'a': 4, 'b': 1}  # , 'dummyRNA':6}
        ions = []
        for type, val in typeDict.items():
            for i in range(1, 5):
                ion = FragmentIon(Fragment(type, i, '', '', [], 0), 2., 2, [], 10e5)
                ion.setIntensity(10 ** 7 * val)
                ion.setQuality(0.1)
                ions.append(ion)
        ion = FragmentIon(Fragment('dummyRNA', 0, '', '', [], 0), 2., 2, [], 10e5)
        ion.setIntensity(10 ** 7 * 6)
        ion.setQuality(0.1)
        ions.append(ion)
        self.analyser.setIons(ions)
        for type, val in self.analyser.calculateRelAbundanceOfSpecies()[0].items():
            if type == 'dummyRNA':
                self.assertAlmostEqual(3 / 8, val)
            else:
                self.assertAlmostEqual(typeDict[type] / 8, val)
        ions = []
        for type, val in typeDict.items():
            for i in range(1, 5):
                z = 1
                if type == 'a':
                    z = 2
                ion = FragmentIon(Fragment(type, i, '', '', [], 0), 2., z, [], 10e5)
                ion.setIntensity(10 ** 7 * val)
                ion.setQuality(0.1)
                ions.append(ion)
        ion = FragmentIon(Fragment('dummyRNA', 0, '', '', [], 0), 2., 3, [], 10e5)
        ion.setIntensity(10 ** 7 * 6)
        ion.setQuality(0.1)
        ions.append(ion)
        self.analyser.setIons(ions)
        for type, val in self.analyser.calculateRelAbundanceOfSpecies()[0].items():
            if type == 'a':
                self.assertAlmostEqual(0.5, val)
            else:
                self.assertAlmostEqual(0.25, val)

    def test_get_modification_loss(self):
        mod = self.props.getModifPattern().getModification()
        precSum = 0
        unModSum = 0
        ions = []
        for ion in self.ions.values():
            if ion.getNumber() == 0:
                if mod in ion.getModification():
                    val = np.random.randint(1, 10) * 10 ** 8
                else:
                    val = np.random.randint(1, 10) * 10 ** 7
                    unModSum += val / ion.getCharge()
                ion.setIntensity(val)
                precSum += val / ion.getCharge()
            else:
                ion.setIntensity(10 ** 6)
            ions.append(ion)
        self.analyser.setIons(ions)
        self.assertAlmostEqual(unModSum / precSum, self.analyser.getPrecursorModification())

    def test_calculate_occupancies(self):
        mod = self.props.getModifPattern().getModification()
        types = np.unique([ion.getType() for ion in self.ions.values()])
        ions = []
        for currentType in types:
            if len(currentType) > 1:  # precursor not relevant
                continue
            arr = np.zeros((len(self.props.getSequenceList()), 2))
            for ion in self.ions.values():
                intensity = np.random.randint(1, 10) * 10 ** 7
                ion.setIntensity(intensity)
                if ion.getType() == currentType:
                    if mod in ion.getModificationList():
                        arr[ion.getNumber() - 1, 1] += intensity / ion.getCharge()
                    arr[ion.getNumber() - 1, 0] += intensity / ion.getCharge()
                ions.append(ion)
            self.analyser.setIons(ions)
            occupDict = self.analyser.calculateOccupancies([currentType])[0]
            self.assertTrue(currentType in occupDict.keys())
            self.assertEqual(1, len(occupDict.keys()))
            self.assertEqual(len(arr), len(occupDict[currentType]))
            for i, val in enumerate(occupDict[currentType]):
                if arr[i, 0] != 0:
                    self.assertAlmostEqual(arr[i, 1] / arr[i, 0], val)
            occupDict = self.analyser.calculateOccupancies([currentType], '+CMCT', ['+CMCT'])[0]
            self.assertTrue(currentType in occupDict.keys())
            self.assertEqual(1, len(occupDict.keys()))
            self.assertEqual(len(arr), len(occupDict[currentType]))
            for i, val in enumerate(occupDict[currentType]):
                if arr[i, 1] != 0:
                    self.assertAlmostEqual(0, val)
        ions = [FragmentIon(Fragment('c',5,'+2CMCT','',[],0), 1., 2, [], 10e5),
                FragmentIon(Fragment('c',4,'+1CMCT','',[],0), 1., 2, [], 10e5),
                FragmentIon(Fragment('c',4,'+2CMCT','',[],0), 1., 2, [], 10e5),
                FragmentIon(Fragment('c',3,'+1CMCT','',[],0), 1., 2, [], 10e5),
                FragmentIon(Fragment('c',2,'+1CMCT','',[],0), 1., 2, [], 10e5),
                FragmentIon(Fragment('c',2,'+','',[],0), 1., 2, [], 10e5),
                FragmentIon(Fragment('c',1,'+','',[],0), 1., 2, [], 10e5)]
        [ion.setIntensity(5*10**6) for ion in ions]
        analyser = Analyser(ions, 7*['G'],4,'+CMCT')
        percentages = analyser.calculateOccupancies(['c','y'],'+CMCT')[0]
        for i in range(5):
            self.assertAlmostEqual(i/2,percentages['c'][i])

    def test_get_nr_of_modifications(self):
        self.assertEqual(1, self.analyser.getNrOfModifications('+CMCT', '+CMCT'))
        self.assertEqual(1, self.analyser.getNrOfModifications('+CMCT-G', '+CMCT'))
        self.assertEqual(2, self.analyser.getNrOfModifications('+CMCT-2G', '-G'))
        for _ in range(10):
            randNr = np.random.randint(10)
            self.assertEqual(randNr, self.analyser.getNrOfModifications('+' + str(randNr) + 'CMCT', '+CMCT'))
            self.assertEqual(randNr, self.analyser.getNrOfModifications('+' + str(randNr) + 'CMCT-A', '+CMCT'))
        self.assertEqual(1, self.analyser.getNrOfModifications('+PARO', '+PARO'))
        self.assertEqual(2, self.analyser.getNrOfModifications('+2PARO', '+PARO'))

    '''def test_calculate_proportions(self):
        self.fail()'''

    def test_analyse_charges(self):
        types = np.unique([ion.getType() for ion in self.ions.values()])
        ions = []
        for currentType in types:
            if len(currentType) > 1:  # precursor not relevant
                continue
            sequLength = len(self.props.getSequenceList())
            arr = np.zeros((sequLength, 2))
            redArr = deepcopy(arr)
            allCharges = {i + 1: [] for i in range(sequLength)}
            for ion in self.ions.values():
                intensity = 10 ** 7
                ion.setIntensity(intensity)
                if ion.getType() == currentType:
                    redArr[ion.getNumber() - 1, 0] += intensity / ion.getCharge()
                    redArr[ion.getNumber() - 1, 1] += intensity
                    arr[ion.getNumber() - 1, 0] += intensity
                    arr[ion.getNumber() - 1, 1] += intensity * ion.getCharge()
                    allCharges[ion.getNumber()].append(ion.getCharge())
                ions.append(ion)
            self.analyser.setIons(ions)
            chargeDict, minMax = self.analyser.analyseCharges([currentType], False)
            redChargeDict, redMinMax = self.analyser.analyseCharges([currentType], True)
            print(allCharges)
            for dict_i, theoArr in zip([chargeDict, redChargeDict], [arr, redArr]):
                self.assertTrue(currentType in dict_i.keys())
                self.assertEqual(1, len(dict_i.keys()))
                self.assertEqual(len(theoArr), len(dict_i[currentType]))
                for i, val in enumerate(dict_i[currentType]):
                    if theoArr[i, 1] != 0:
                        self.assertAlmostEqual(theoArr[i, 1] / theoArr[i, 0], val)
            self.assertTrue(currentType in minMax.keys())
            for i, row in enumerate(minMax[currentType]):
                if len(allCharges[i + 1]) > 0:
                    self.assertEqual(min(allCharges[i + 1]), row[0])
                    self.assertEqual(max(allCharges[i + 1]), row[1])

    '''def test_to_table(self):
        self.fail()'''


    def test_get_sequence_coverage(self):
        print('ions:',[ion.getName() for ion in self.ions.values()])
        self.analyser.setIons(self.ions.values())
        coverages, calcCoverages, overall = self.analyser.getSequenceCoverage(['a','c'])
        print('coverages:',coverages)
        self.assertTrue(np.all(coverages[0]['c'][:-1]))
        self.assertTrue(np.all(coverages[1]['w'][1:]))
        self.assertFalse(coverages[0]['a'][0])
        self.assertFalse(coverages[1]['y'][-1])
        print('calcCoverages:',calcCoverages)
        for type in ('c','w','forward','backward','total'):
            self.assertAlmostEqual(1,calcCoverages[type])
        for type in ('a','y'):
            #print(type, coverages[type])
            self.assertAlmostEqual(2/3,calcCoverages[type])
        print('overall',overall)
        self.assertTrue(np.all(overall[:-1,0]))
        self.assertTrue(np.all(overall[1:,1]))
        self.assertTrue(np.all(overall[:,2]))
        ions = deepcopy(self.ions)
        for hash in self.ions.keys():
            if ('c02' in hash[0]) or ('a02' in hash[0]):
                del ions[hash]
        self.analyser.setIons(ions.values())
        coverages, calcCoverages, overall = self.analyser.getSequenceCoverage(['a','c'])
        for type in ('w','backward','total'):
            self.assertAlmostEqual(1,calcCoverages[type])
        for type in ('c','y','forward'):
            #print(type, coverages[type])
            self.assertAlmostEqual(2/3,calcCoverages[type])
        self.assertAlmostEqual(1/3,calcCoverages['a'])
        ions = deepcopy(self.ions)
        for hash in self.ions.keys():
            if ('c02' in hash[0]) or ('a02' in hash[0]) or ('w03' in hash[0])  or ('y03' in hash[0]):
                del ions[hash]
        self.analyser.setIons(ions.values())
        coverages, calcCoverages, overall = self.analyser.getSequenceCoverage(['a','c'])
        for type in ('c','w','forward','backward'):
            #print(type, coverages[type])
            self.assertAlmostEqual(2/3,calcCoverages[type])
        for type in ('a', 'y'):
            # print(type, coverages[type])
            self.assertAlmostEqual(1 / 3, calcCoverages[type])
        self.assertAlmostEqual(3/4,calcCoverages['total'])


