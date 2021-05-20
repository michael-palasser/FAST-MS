from copy import deepcopy
from unittest import TestCase
import numpy as np

from src.entities.Ions import FragmentIon, Fragment
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

    def test_fun_sum_square_scalar(self):
        for i in range(10):
            spectralIntensities = np.random.rand(5)*10**7
            theoIntensities = np.random.rand(5)
            x=10**7
            sum_square = 0
            for spectralIntensity, theoIntensity in zip(spectralIntensities, theoIntensities):
                sum_square += (spectralIntensity - theoIntensity * x) ** 2
            self.assertAlmostEqual(1.,sum_square/
                                   self.intensityModeller.fun_sum_square_scalar(x,spectralIntensities,theoIntensities))

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
            print(spectralIntensities)
            for j in range(6):
                spectralIntensities[j] = spectralIntensities[j]*(1+0.02*(-1)**j)
            spectralIntensities[i] *=2
            print(spectralIntensities)
            solution, outliers = self.intensityModeller.modelDistribution(spectralIntensities,theoIntensities, np.arange(6))
            self.assertEqual(1, len(outliers))
            self.assertEqual(i, outliers[0])

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
        self.fail()

    '''def test_delete_same_monoisotopics(self):
        self.fail()

    def test_delete_ion(self):
        self.fail()'''

    def test_remodel_overlaps(self):
        self.fail()

    '''def test_comment_ions_in_patterns(self):
        self.fail()'''

    def test_set_up_equ_matrix(self):
        self.fail()

    def test_fun_sum_square(self):
        self.fail()

    def test_remodel_complex_patterns(self):
        self.fail()

    '''def test_delete_ions(self):
        self.fail()'''

    def test_remodel_intensity(self):
        self.fail()

    def test_switch_ion(self):
        self.fail()

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
