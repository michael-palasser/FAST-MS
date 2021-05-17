import os
from unittest import TestCase
import numpy as np

from src import path
from src.entities.Ions import Fragment
from src.entities.SearchProperties import PropertyStorage
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler


class TestSpectrumHandler(TestCase):
    def setUp(self):
        filePath = os.path.join(path, 'tests', 'dummySpectrum.txt')
        self.settings = {'sequName': 'dummyRNA', 'charge': -2, 'fragmentation': 'RNA_CAD', 'modifications': 'CMCT',
                    'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 1.0, 'fragLib': ''}
        self.props = PropertyStorage(self.settings['sequName'], self.settings['fragmentation'], self.settings['modifications'])
        self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
        builder = FragmentLibraryBuilder(self.props,1)
        builder.createFragmentLibrary()
        self.spectrumHandler = SpectrumHandler(self.props,builder.getPrecursor(),self.settings)
        '''builder2 = FragmentLibraryBuilder(self.props,2)
        builder2.createFragmentLibrary()
        settings2 = self.settings
        settings2['nrMod'] = 2
        self.spectrumHandler2 = SpectrumHandler(self.props,builder2.getPrecursor(),settings2)'''


    def test_calcPrecCharge(self):
        self.assertEqual(5, self.spectrumHandler.calcPrecCharge(6,1))
        self.assertEqual(5, self.spectrumHandler.calcPrecCharge(-6,-1))

    def test_add_spectrum_from_csv_and_txt(self):
        with open(os.path.join(path, 'tests', 'dummySpectrum.csv'), 'r') as f:
            fromCsv = self.spectrumHandler.addSpectrumFromCsv(f)
        with open(self.settings['spectralData'], 'r') as f:
            fromTxt = self.spectrumHandler.addSpectrumFromTxt(f)
        N = len(fromCsv)
        self.assertEqual(N,len(fromTxt))
        for row in range(N):
            for col in range(2):
                self.assertAlmostEqual(fromCsv[row,col],fromTxt[row,col])

    def test_find_upper_bound(self):
        self.assertAlmostEqual(1800+self.configs['upperBoundTolerance'] ,self.spectrumHandler.findUpperBound())

    def test_calculate_noise(self):
        for i in range(10):
            self.assertAlmostEqual(0.95, self.spectrumHandler.calculateNoise(400+i*100,40)/(10**6+100*400+i*100), delta=0.1)


    def test_get_peaks_in_window(self):
        allPeaks = np.column_stack((np.arange(100.,300.), np.ones(200)))
        peaks = self.spectrumHandler.getPeaksInWindow(allPeaks,200,10)
        for theo, peak in zip(np.arange(196., 205.),peaks):
            self.assertAlmostEqual(theo, peak[0])

    def test_get_mod_charge(self):
        zEffect = self.props.getModification().getItems()[0].getZEffect()
        fragment0 = Fragment('c',5,'','',[],0)
        self.assertAlmostEqual(0,self.spectrumHandler.getModCharge(fragment0))
        fragment1 = Fragment('c',5,'+CMCT','',[],0)
        self.assertAlmostEqual(-zEffect,self.spectrumHandler.getModCharge(fragment1))
        fragment2 = Fragment('c',5,'+2CMCT','',[],0)
        self.assertAlmostEqual(-2*zEffect,self.spectrumHandler.getModCharge(fragment2))

    def test_get_normalization_factor(self):
        normalizationFactor = abs(self.settings['charge'])/(len(self.props.getSequenceList())-1)
        self.assertAlmostEqual(normalizationFactor,self.spectrumHandler.getNormalizationFactor())

    def test_get_search_parameters(self):
        self.fail()

    def test_get_correct_peak(self):
        self.fail()

    def test_find_peaks(self):
        self.fail()


    '''def test_resize_spectrum(self):
        self.fail()

    def test_add_spectrum(self):
            self.fail()'''

    '''def test_get_spectrum(self):
        spectrum = np.array([(100.1,1),(200.1,1),(300.1,1),(400.1,1),(500.1,1)])
        self.spectrumHandler.setSpectrum(spectrum)
        trunctuatedSpectrum = self.spectrumHandler.getSpectrum(200,400)
        self.assertAlmostEqual(500.2,np.sum(trunctuatedSpectrum[:,0]))'''



    '''def test_get_ions_in_noise(self):
        self.fail()

    def test_get_searched_charge_states(self):
        self.fail()

    def test_empty_lists(self):
        self.fail()

        
    def test_add_to_deleted_ions(self):
        self.fail()

    def test_get_mz(self):
        self.fail()

    def test_calculate_error(self):
        self.fail()   

    

    def test_set_searched_charge_states(self):
        self.fail()'''