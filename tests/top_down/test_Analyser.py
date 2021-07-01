from copy import deepcopy
from unittest import TestCase
import numpy as np

from src.entities.Ions import FragmentIon, Fragment
from src.top_down.Analyser import Analyser
from tests.top_down.test_IntensityModeller import initTestSpectrumHandler


class TestAnalyser(TestCase):
    def setUp(self):
        self.configs, settings, self.props, builder, self.spectrumHandler = initTestSpectrumHandler()
        fragments = builder.getFragmentLibrary()
        self.spectrumHandler.setNormalizationFactor(self.spectrumHandler.getNormalizationFactor())
        self.ions = {}
        for fragment in fragments:
            zRange = self.spectrumHandler.getChargeRange(fragment,0)
            for z in zRange:
                ion = FragmentIon(fragment,1.,z,fragment.getIsotopePattern(),10e5)
                self.ions[ion.getHash()]=ion
        self.analyser = Analyser([],self.props.getSequenceList(),settings['charge'],
                                 self.props.getModification().getName())


    def test_calculate_rel_abundance_of_species(self):
        typeDict = {'a':4,'b':1}#, 'dummyRNA':6}
        ions = []
        for type, val in typeDict.items():
            for i in range(1,5):
                ion =FragmentIon(Fragment(type,i,'','',[],0),2.,2,[],10e5)
                ion.setIntensity(10**7*val)
                ion.setQuality(0.1)
                ions.append(ion)
        ion = FragmentIon(Fragment('dummyRNA', 0, '', '', [], 0), 2., 2, [], 10e5)
        ion.setIntensity(10 ** 7 * 6)
        ion.setQuality(0.1)
        ions.append(ion)
        self.analyser.setIons(ions)
        for type,val in self.analyser.calculateRelAbundanceOfSpecies().items():
            if type == 'dummyRNA':
                self.assertAlmostEqual(3/8,val)
            else:
                self.assertAlmostEqual(typeDict[type]/8,val)
        ions = []
        for type, val in typeDict.items():
            for i in range(1,5):
                z=1
                if type=='a':
                    z=2
                ion =FragmentIon(Fragment(type,i,'','',[],0),2.,z,[],10e5)
                ion.setIntensity(10**7*val)
                ion.setQuality(0.1)
                ions.append(ion)
        ion = FragmentIon(Fragment('dummyRNA', 0, '', '', [], 0), 2., 3, [], 10e5)
        ion.setIntensity(10 ** 7 * 6)
        ion.setQuality(0.1)
        ions.append(ion)
        self.analyser.setIons(ions)
        for type,val in self.analyser.calculateRelAbundanceOfSpecies().items():
            if type == 'a':
                self.assertAlmostEqual(0.5,val)
            else:
                self.assertAlmostEqual(0.25,val)

    def test_get_modification_loss(self):
        mod = self.props.getModification().getModification()
        precSum = 0
        unModSum=0
        ions = []
        for ion in self.ions.values():
            if ion.getNumber()==0:
                if mod in ion.getModification():
                    val= np.random.randint(1,10)*10**8
                else:
                    val= np.random.randint(1,10)*10**7
                    unModSum+=val/ion.getCharge()
                ion.setIntensity(val)
                precSum += val/ion.getCharge()
            else:
                ion.setIntensity(10**6)
            ions.append(ion)
        self.analyser.setIons(ions)
        self.assertAlmostEqual(unModSum/precSum, self.analyser.getModificationLoss())


    def test_calculate_occupancies(self):
        mod = self.props.getModification().getModification()
        types = np.unique([ion.getType() for ion in self.ions.values()])
        ions = []
        for currentType in types:
            if len(currentType) > 1: #precursor not relevant
                continue
            arr = np.zeros((len(self.props.getSequenceList()),2))
            for ion in self.ions.values():
                intensity = np.random.randint(1,10)*10**7
                ion.setIntensity(intensity)
                if ion.getType()==currentType:
                    if mod in ion.getModification():
                        arr[ion.getNumber()-1,1] += intensity/ion.getCharge()
                    arr[ion.getNumber() - 1, 0] += intensity/ion.getCharge()
                ions.append(ion)
            self.analyser.setIons(ions)
            occupDict = self.analyser.calculateOccupancies([currentType])
            self.assertTrue(currentType in occupDict.keys())
            self.assertEqual(1, len(occupDict.keys()))
            self.assertEqual(len(arr), len(occupDict[currentType]))
            for i,val in enumerate(occupDict[currentType]):
                if arr[i,0] != 0:
                    self.assertAlmostEqual(arr[i,1]/arr[i,0],val)
            occupDict = self.analyser.calculateOccupancies([currentType],['+CMCT'])
            self.assertTrue(currentType in occupDict.keys())
            self.assertEqual(1, len(occupDict.keys()))
            self.assertEqual(len(arr), len(occupDict[currentType]))
            for i,val in enumerate(occupDict[currentType]):
                if arr[i,1] != 0:
                    self.assertAlmostEqual(0,val)

    def test_get_nr_of_modifications(self):
        self.assertEqual(1, self.analyser.getNrOfModifications('+CMCT'))
        self.assertEqual(1, self.analyser.getNrOfModifications('+CMCT-G'))
        for i in range(10):
            randNr = np.random.randint(10)
            self.assertEqual(randNr,self.analyser.getNrOfModifications('+'+str(randNr)+'CMCT'))
            self.assertEqual(randNr,self.analyser.getNrOfModifications('+'+str(randNr)+'CMCT-A'))

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
            allCharges = {i+1:[] for i in range(sequLength)}
            for ion in self.ions.values():
                intensity = 10 ** 7
                ion.setIntensity(intensity)
                if ion.getType() == currentType:
                    redArr[ion.getNumber() - 1, 0] += intensity  / ion.getCharge()
                    redArr[ion.getNumber() - 1, 1] += intensity
                    arr[ion.getNumber() - 1, 0] += intensity
                    arr[ion.getNumber() - 1, 1] += intensity * ion.getCharge()
                    allCharges[ion.getNumber()].append(ion.getCharge())
                ions.append(ion)
            self.analyser.setIons(ions)
            chargeDict, minMax = self.analyser.analyseCharges([currentType], False)
            redChargeDict, redMinMax = self.analyser.analyseCharges([currentType], True)
            print(allCharges)
            for dict_i, theoArr in zip([chargeDict, redChargeDict], [arr,redArr]):
                self.assertTrue(currentType in dict_i.keys())
                self.assertEqual(1, len(dict_i.keys()))
                self.assertEqual(len(theoArr), len(dict_i[currentType]))
                for i, val in enumerate(dict_i[currentType]):
                    if theoArr[i, 1] != 0:
                        self.assertAlmostEqual(theoArr[i, 1] / theoArr[i, 0], val)
            self.assertTrue(currentType in minMax.keys())
            for i,row in enumerate(minMax[currentType]):
                if len(allCharges[i+1])>0:
                    self.assertEqual(min(allCharges[i+1]),row[0])
                    self.assertEqual(max(allCharges[i+1]),row[1])

    '''def test_to_table(self):
        self.fail()'''
