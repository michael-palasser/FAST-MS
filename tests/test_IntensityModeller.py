from copy import deepcopy
from unittest import TestCase
import numpy as np
from scipy.stats import norm

from src.MolecularFormula import MolecularFormula
from src.entities.Ions import FragmentIon, Fragment
from tests.test_LibraryBuilder import deleteTestSequences
from tests.test_SpectrumHandler import initTestLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler
from src.top_down.IntensityModeller import IntensityModeller

def initTestSpectrumHandler():
    configs, settings, props, builder = initTestLibraryBuilder()
    spectrumHandler = SpectrumHandler(props,builder.getPrecursor(),settings)
    return configs, settings, props, builder, spectrumHandler

class TestIntensityModeller(TestCase):
    def setUp(self):
        self.configs, settings, props, self.builder, self.spectrumHandler = initTestSpectrumHandler()
        self.intensityModeller = IntensityModeller(self.configs)

    '''def test_get_observed_ions(self):
        self.fail()

    def test_get_deleted_ions(self):
        self.fail()

    def test_get_remodelled_ions(self):
        self.fail()

    def test_add_remodelled_ion(self):
        self.fail()'''

    def test_loss_1D_sum_square(self):
        for i in range(10):
            spectralIntensities = np.random.rand(5)*10**7
            theoIntensities = np.random.rand(5)
            x=10**7
            sum_square = 0
            for spectralIntensity, theoIntensity in zip(spectralIntensities, theoIntensities):
                sum_square += (spectralIntensity - theoIntensity * x) ** 2
            self.assertAlmostEqual(1., sum_square /
                                   self.intensityModeller.loss_1D_sum_square(x, spectralIntensities, theoIntensities))

    def test_model_distribution(self):
        for i in range(5):
            theoIntensities = np.random.rand(6)
            spectralIntensities = theoIntensities*10**(7+i)
            for j in range(6):
                spectralIntensities[j] = spectralIntensities[j]*(1+0.02*(-1)**j)
            solution, outliers = self.intensityModeller.modelDistribution(spectralIntensities,theoIntensities, np.arange(6))
            self.assertAlmostEqual(1,solution.x/10**(7+i), delta=10e-2)
        for i in range(5):
            theoIntensities = np.random.rand(6)
            spectralIntensities = theoIntensities*10**(7+i)
            print(theoIntensities,spectralIntensities)
            for j in range(6):
                spectralIntensities[j] = spectralIntensities[j]*(1+0.02*(-1)**j)
            solution1, outliers = self.intensityModeller.modelDistribution(spectralIntensities,theoIntensities, np.arange(6))
            spectralIntensities[i] *=2
            solution, outliers = self.intensityModeller.modelDistribution(spectralIntensities,theoIntensities, np.arange(6))
            self.assertGreaterEqual(len(outliers),1)
            self.assertEqual(i, outliers[0])
            if len(outliers)==1:
                self.assertAlmostEqual(1.05,solution.x/solution1.x, delta=0.1)

            #FragmentIon(Fragment('c',3,'+CMCT','',[],0),0,)



    '''def test_model_ion(self):
        self.fail()'''

    def test_calculate_intensity(self):
        peaksArrType = np.dtype([('m/z', np.float64), ('relAb', np.float64),
                                       ('calcInt', np.float64), ('error', np.float32), ('used', np.bool_)])
        for fragment in self.builder.getFragmentLibrary():
            #isotopePattern = fragment.getIsotopePattern() *10**7
            isotopePattern = deepcopy(fragment.getIsotopePattern())
            intensities = isotopePattern['calcInt']*10**7
            #mzs = isotopePattern['m/z']
            length = len(isotopePattern)
            if not length%2:
                length -=1
            for i in range(length):
                intensities[i] += 2*10**5*(-1)**i
            finIsoPattern = []
            for i,peak in enumerate(isotopePattern):
                finIsoPattern.append((peak['m/z'],intensities[i],peak['calcInt'],np.random.rand(),True))
            finIsoPattern = np.array(finIsoPattern,dtype=peaksArrType)
            ion = self.intensityModeller.calculateIntensity(FragmentIon(fragment, 0,0,finIsoPattern,10**5))
            self.assertAlmostEqual(1.,ion.getIntensity()/np.sum(intensities), delta=0.01)
            self.assertAlmostEqual(ion.getIntensity(), float(np.sum(ion.getIsotopePattern()['calcInt'])), delta=0.5)
            self.assertTrue(0.<=ion.getQuality()<1.)


    '''def test_process_ions(self):
        self.fail()'''

    '''def test_process_noise_ions(self):
        self.fail()'''

    def test_find_same_monoisotopics(self):
        observedIons = [FragmentIon(Fragment('c',12,'','',[],0),1000.023,3,[],1),
                        FragmentIon(Fragment('w',12,'','',[],0),1000.023001,3,[],1),
                        FragmentIon(Fragment('c',13,'','',[],0),1010.023001,3,[],1),
                        FragmentIon(Fragment('c',24,'','',[],0),1000.023,6,[],1)]
        self.intensityModeller.setIonLists(observedIons,[],[])
        monoisotopicList = [np.array([(ion.getName(), ion.getCharge(), ion.getMonoisotopic())],
                dtype=[('name','U32'),('charge', np.uint8),('mono',np.float64)]) for ion in observedIons]
        self.intensityModeller.setMonoisotopicList(monoisotopicList)
        sameMonos = self.intensityModeller.findSameMonoisotopics()
        self.assertEqual(1, len(sameMonos))
        self.assertEqual(2, len(sameMonos[0]))
        names = [ion.getName() for ion in sameMonos[0]]
        self.assertTrue('c12' in names)
        self.assertTrue('w12' in names)



    '''def test_delete_same_monoisotopics(self):
        self.fail()

    def test_delete_ion(self):
        self.fail()'''

    '''def test_remodel_overlaps(self):
        self.fail()'''

    '''def test_comment_ions_in_patterns(self):
        self.fail()'''

    def getOverlappingPattern(self):
        ions = {}
        i = 1
        allPeaks = {}
        dtype = np.dtype([('m/z', np.float64), ('relAb', np.float64),('calcInt', np.float64), ('error', np.float32),
                          ('used', np.bool_)])
        for formulaStr, type in zip(['C200H300NOP', 'C200H302NOP', 'C200H304NOP'],
                                    ['a', 'b', 'c', 'd']):
            formula = MolecularFormula(formulaStr)
            theoIsotopePattern = []
            for peak in formula.calculateIsotopePattern():
                mz, intensity = round(peak['m/z'],0) / 2, peak['calcInt'] * 10 ** 7 * i
                theoIsotopePattern.append((mz, intensity, peak['calcInt'], 0., True))
                if mz in allPeaks.keys():
                    allPeaks[mz] += intensity
                else:
                    allPeaks[mz] = intensity
            theoIsotopePattern = np.array(theoIsotopePattern, dtype=dtype)
            ion = FragmentIon(Fragment(type, 12, '', '', [], 0), formula.calculateMonoIsotopic(), 2, theoIsotopePattern,
                              1)
            ions[ion.getHash()] = self.intensityModeller.calculateIntensity(ion)
            i += 1
        observedIons = {}
        for key, theoIon in ions.items():
            isotopePattern = []
            for peak in theoIon.getIsotopePattern():
                intensity = allPeaks[peak['m/z']]
                print('hey', peak['relAb'],intensity)
                isotopePattern.append((peak['m/z'], intensity, peak['calcInt'], 0., True))
            isotopePattern = np.array(isotopePattern, dtype=dtype)
            ion = deepcopy(theoIon)
            ion.setIsotopePattern(isotopePattern)
            observedIons[key] = self.intensityModeller.calculateIntensity(ion)
            #observedIons[key] = ion
        formula = MolecularFormula('C155H290N30O10')
        isotopePattern = []
        for peak in formula.calculateIsotopePattern():
            mz, intensity = round(peak['m/z'] / 2, 2), peak['calcInt'] * 10 ** 7
            isotopePattern.append((mz, intensity, peak['calcInt'], 0., True))
        isotopePattern = np.array(isotopePattern, dtype=dtype)
        ion = FragmentIon(Fragment('a', 13, '', '', [], 0), formula.calculateMonoIsotopic(), 2, isotopePattern,1)
        observedIons[ion.getHash()]=ion
        return ions,observedIons

    def test_find_overlaps(self):
        theoIons, observedIons = self.getOverlappingPattern()
        self.intensityModeller.setIonLists(list(observedIons.values()), [],[])
        simplePatterns,complexPatterns = self.intensityModeller.findOverlaps(1)
        self.assertEqual(0,len(simplePatterns))
        self.assertEqual(len(theoIons),len(complexPatterns[0]))
        simplePatterns,complexPatterns = self.intensityModeller.findOverlaps(len(theoIons))
        self.assertEqual(0,len(complexPatterns))
        self.assertEqual(len(theoIons),len(simplePatterns[0]))
        return simplePatterns, theoIons

    '''def test_set_up_equ_matrix(self):
        ions, observedIons = self.getOverlappingPattern()
        self.intensityModeller.setIonLists(list(observedIons.values()), [],[])
        simplePatterns,complexPatterns = self.intensityModeller.findOverlaps(100)
        for pattern in simplePatterns:
            print(pattern)
            del_ions = []
            spectr_peaks = list()
            for ion in pattern:
                for peak in observedIons[ion].getIsotopePattern():  # spectral list
                    if (peak['m/z'], peak['relAb']) not in spectr_peaks:
                        spectr_peaks.append((peak['m/z'], peak['relAb']))
            spectr_peaks = np.array(sorted(spectr_peaks, key=lambda tup: tup[0]))'''

    '''def test_fun_sum_square(self):
        self.fail()'''

    def test_remodel_intensity(self):
        simplePatterns,theoIons = self.test_find_overlaps()
        for hash,ion in self.intensityModeller.getObservedIons().items():
            if hash in theoIons.keys():
                self.assertNotEqual(ion.getIntensity(),theoIons[hash].getIntensity())
        self.intensityModeller.remodelIntensity(simplePatterns,[])
        for hash,ion in self.intensityModeller.getObservedIons().items():
            if hash in theoIons.keys():
                self.assertEqual(ion.getIntensity(),theoIons[hash].getIntensity())

        simplePatterns,theoIons = self.test_find_overlaps()
        deleted = list(self.intensityModeller.getObservedIons().keys())[1]
        self.intensityModeller.remodelIntensity(simplePatterns,[deleted])
        for hash,ion in self.intensityModeller.getObservedIons().items():
            if hash in theoIons.keys():
                self.assertNotEqual(ion.getIntensity(),theoIons[hash].getIntensity())

    '''def test_remodel_complex_patterns(self):
        self.fail()'''

    '''def test_delete_ions(self):
        self.fail()'''


    '''def test_switch_ion(self):
        self.fail()'''

    def test_get_adjacent_ions(self):
        self.fail()

    '''def test_get_ion(self):
        self.fail()'''

    '''def test_get_remodelled_ion(self):
        self.fail()'''

    def test_get_limits(self):
        self.fail()

    def test_get_prec_region(self):
        self.fail()

    def test_remodel_single_ion(self):
        self.fail()

    def test_model_simply(self):
        self.fail()

    '''def test_set_ion_lists(self):
        self.fail()'''

    '''def tearDown(self):
        deleteTestSequences()'''