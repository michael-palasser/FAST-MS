import os
from unittest import TestCase
import numpy as np

from src import path
from src.MolecularFormula import MolecularFormula
from src.entities.Ions import Fragment
from src.entities.SearchProperties import PropertyStorage
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler


class TestSpectrumHandler(TestCase):
    def setUp(self):
        filePath = os.path.join(path, 'tests', 'dummySpectrum.txt')
        self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()

        self.settings = {'sequName': 'dummyRNA', 'charge': -3, 'fragmentation': 'RNA_CAD', 'modifications': 'CMCT',
                    'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 1.0, 'fragLib': ''}
        self.props = PropertyStorage(self.settings['sequName'], self.settings['fragmentation'], self.settings['modifications'])
        builder = FragmentLibraryBuilder(self.props,1)
        builder.createFragmentLibrary()
        self.spectrumHandler = SpectrumHandler(self.props,builder.getPrecursor(),self.settings)


        self.settingsProt = {'sequName': 'dummyProt', 'charge': 4, 'fragmentation': 'Protein_CAD', 'modifications': '-',
                    'nrMod': 0, 'spectralData': filePath, 'noiseLimit': 1.0, 'fragLib': ''}
        self.propsProt = PropertyStorage(self.settingsProt['sequName'], self.settingsProt['fragmentation'], self.settingsProt['modifications'])
        builder = FragmentLibraryBuilder(self.propsProt,0)
        builder.createFragmentLibrary()
        self.spectrumHandlerProt = SpectrumHandler(self.propsProt,builder.getPrecursor(),self.settingsProt)
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

    def test_get_charge_range(self):
        nrP = len(self.props.getSequenceList())-1
        precModCharge = self.spectrumHandler.getModCharge(Fragment('c',3,'+CMCT','',[],0))
        self.spectrumHandler.setNormalizationFactor(self.spectrumHandler.getNormalizationFactor())
        tolerance = self.configs['zTolerance']
        precCharge = abs(self.settings['charge'])
        self.spectrumHandlerProt.setNormalizationFactor(self.spectrumHandlerProt.getNormalizationFactor())

        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('y', 1, '', MolecularFormula({'P': 0}), [], 0),
                                                        precModCharge)
        self.assertEqual(0, rangeCalc.stop)

        rangeTheo = self.getRange(precCharge/nrP-precModCharge, tolerance, precCharge)
        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('c',3,'',MolecularFormula({'P':1}),[],0),precModCharge)
        print(rangeTheo,rangeCalc)
        self.assertEqual(rangeTheo.start,rangeCalc.start)
        self.assertEqual(rangeTheo.stop,rangeCalc.stop)

        rangeTheo = self.getRange(2*precCharge/nrP-precModCharge, tolerance, precCharge)
        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('c',3,'',MolecularFormula({'P':2}),[],0),precModCharge)
        self.assertEqual(rangeTheo.start,rangeCalc.start)
        self.assertEqual(rangeTheo.stop,rangeCalc.stop)

        rangeTheo = self.getRange(2*precCharge/nrP, tolerance, precCharge)
        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('c',3,'+CMCT',MolecularFormula({'P':2}),[],0),precModCharge)
        self.assertEqual(rangeTheo.start,rangeCalc.start)
        self.assertEqual(rangeTheo.stop,rangeCalc.stop)

        rangeTheo = self.getRange(abs(self.settingsProt['charge']*3)/len(self.propsProt.getSequenceList()), tolerance, self.settingsProt['charge'])
        rangeCalc = self.spectrumHandlerProt.getChargeRange(Fragment('c',3,'',MolecularFormula({'P':1}),['G', 'A', 'P'],0),0)
        self.assertEqual(rangeTheo.start,rangeCalc.start)
        self.assertEqual(rangeTheo.stop,rangeCalc.stop)


        rangeTheo = self.getRange(abs(self.settingsProt['charge']*3)/len(self.propsProt.getSequenceList())-1, tolerance, self.settingsProt['charge'])
        rangeCalc = self.spectrumHandlerProt.getChargeRange(Fragment('c',3,'',MolecularFormula({'P':1}),['G', 'A', 'P'],1),0)
        self.assertEqual(rangeTheo.start,rangeCalc.start)
        self.assertEqual(rangeTheo.stop,rangeCalc.stop)

    def getRange(self,probZ,tolerance, precCharge):
        low = int(round(probZ-tolerance))
        if low < 1 :
            low = 1
        high = precCharge
        if probZ+tolerance < precCharge:
            high = int(round(probZ+tolerance))
        return range(low,high+1)

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