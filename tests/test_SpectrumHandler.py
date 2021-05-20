import os
from copy import deepcopy
from unittest import TestCase
import numpy as np

from src import path
from src.MolecularFormula import MolecularFormula
from src.Services import SequenceService
from src.entities.Ions import Fragment
from src.entities.SearchProperties import PropertyStorage
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler, getErrorLimit
from tests.test_LibraryBuilder import initTestSequences,deleteTestSequences

def initTest():
    initTestSequences(SequenceService())
    configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
    filePath = os.path.join(path, 'tests', 'dummySpectrum.txt')
    settings = {'sequName': 'dummyRNA', 'charge': -3, 'fragmentation': 'RNA_CAD', 'modifications': 'CMCT',
                     'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 10 ** 5, 'fragLib': ''}
    props = PropertyStorage(settings['sequName'], settings['fragmentation'],settings['modifications'])
    builder = FragmentLibraryBuilder(props, 1)
    builder.createFragmentLibrary()
    builder.addNewIsotopePattern()
    return configs, settings, props, builder

class TestSpectrumHandler(TestCase):
    def setUp(self):
        '''filePath = os.path.join(path, 'tests', 'dummySpectrum.txt')
        self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()

        self.settings = {'sequName': 'dummyRNA', 'charge': -3, 'fragmentation': 'RNA_CAD', 'modifications': 'CMCT',
                    'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 10**5, 'fragLib': ''}
        self.props = PropertyStorage(self.settings['sequName'], self.settings['fragmentation'], self.settings['modifications'])
        self.builder = FragmentLibraryBuilder(self.props,1)
        self.builder.createFragmentLibrary()
        self.builder.addNewIsotopePattern()'''
        self.configs, self.settings, self.props, self.builder = initTest()
        self.spectrumHandler = SpectrumHandler(self.props,self.builder.getPrecursor(),self.settings)


        self.settingsProt = {'sequName': 'dummyProt', 'charge': 4, 'fragmentation': 'Protein_CAD', 'modifications': '-',
                    'nrMod': 0, 'spectralData': os.path.join(path, 'tests', 'dummySpectrum.txt'), 'noiseLimit': 10**5, 'fragLib': ''}
        self.propsProt = PropertyStorage(self.settingsProt['sequName'], self.settingsProt['fragmentation'], self.settingsProt['modifications'])
        self.builderProt = FragmentLibraryBuilder(self.propsProt,0)
        self.builderProt.createFragmentLibrary()
        self.spectrumHandlerProt = SpectrumHandler(self.propsProt,self.builderProt.getPrecursor(),self.settingsProt)
        self.spectrumHandler.setNormalizationFactor(self.spectrumHandler.getNormalizationFactor())
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
        '''isotopePattern_dtype = np.dtype([('m/z', np.float64), ('relAb', np.float64),
                                       ('calcInt', np.float64), ('error', np.float32), ('used', np.bool_)])'''
        dtype = [('m/z', np.float64), ('calcInt', np.float64)]
        theoPeak = np.array([(300.54, 0.5)], dtype=dtype)
        self.assertEqual(0,self.spectrumHandler.getCorrectPeak(np.array([]),theoPeak[0])[1])
        dummyPeak, error = self.getDummyPeak(theoPeak)
        finPeak = self.spectrumHandler.getCorrectPeak(dummyPeak,theoPeak[0])
        self.assertAlmostEqual(dummyPeak[0][0],finPeak[0])
        self.assertAlmostEqual(dummyPeak[0][1],finPeak[1])
        self.assertAlmostEqual(theoPeak['calcInt'],finPeak[2])
        self.assertAlmostEqual(error,finPeak[3])
        self.assertAlmostEqual(True,finPeak[4])
        for i in range(20):
            dummyPeak1, error1 = self.getDummyPeak(theoPeak)
            dummyPeak2 = deepcopy(dummyPeak1)
            dummyPeak2[0] *=(1+error1/10**6)
            dummyPeak3 = deepcopy(dummyPeak1)
            dummyPeak3[0] *=(1-2.1*error1/10**6)
            dummyPeaks = np.concatenate((dummyPeak1,dummyPeak2,dummyPeak3),axis=0)
            finPeak = self.spectrumHandler.getCorrectPeak(dummyPeaks,theoPeak[0])
            self.assertAlmostEqual(dummyPeak1[0][0],finPeak[0])
            self.assertAlmostEqual(dummyPeak1[0][1],finPeak[1])
            self.assertAlmostEqual(theoPeak['calcInt'],finPeak[2])
            self.assertAlmostEqual(error1,finPeak[3])
            self.assertAlmostEqual(True,finPeak[4])
            theoPeak['m/z'] += 100

    def getDummyPeak(self, theoPeak, outside=False):
        if outside == False:
            randomError = np.random.rand(1)*(-1)**(np.random.randint(2))*getErrorLimit(theoPeak['m/z'])
        else:
            randomError = (np.random.rand(1)+1)*(-1)**(np.random.randint(2))*getErrorLimit(theoPeak['m/z'])
        mz = theoPeak['m/z']*(1+randomError/10**6)
        return np.array([(mz[0], (theoPeak['calcInt']+np.random.rand(1)/10*(-1)**(np.random.randint(2)))[0])]), randomError[0]

    def test_find_peak(self):
        dtype = [('m/z', np.float64), ('calcInt', np.float64)]
        theoPeak = np.array([(310.58, 0.5)], dtype=dtype)
        for i in range(5):
            dummyPeak, error = self.getDummyPeak(theoPeak, True)
            dummyPeak[0][1] *= 10**7
            self.spectrumHandler.setSpectrum(np.concatenate((self.spectrumHandler.getSpectrum(),dummyPeak),axis=0))
            self.assertEqual(0,self.spectrumHandler.findPeak(theoPeak[0])[1])
            theoPeak['m/z'] += 100
        for i in range(5):
            dummyPeak, error = self.getDummyPeak(theoPeak)
            dummyPeak[0][1] *= 10**7
            self.spectrumHandler.setSpectrum(np.concatenate((self.spectrumHandler.getSpectrum(),dummyPeak),axis=0))
            self.assertTrue(self.spectrumHandler.findPeak(theoPeak[0])[1]>0)
            theoPeak['m/z'] += 100
        self.setUp()


    def test_find_ions_basic(self):
        #prepare everything
        self.spectrumHandler.findIons(self.builder.getFragmentLibrary())
        self.assertEqual(0,len(self.spectrumHandler.getFoundIons()))
        precModCharge = self.spectrumHandler.getModCharge(self.builder.getPrecursor())
        #peaksToFind = []
        #nrsOfPeaks = {}
        originalSpectrum = self.spectrumHandler.getSpectrum()
        upperBound = self.spectrumHandler.getUpperBound()
        for i,fragment in enumerate(self.builder.getFragmentLibrary()):
            isotopePattern = fragment.getIsotopePattern()
            for z in self.spectrumHandler.getChargeRange(fragment,precModCharge):
                theoreticalPeaks = deepcopy(isotopePattern)
                #if self.__settings['dissociation'] in ['ECD', 'EDD', 'ETD'] and fragment.number == 0:
                #    theoreticalPeaks['mass'] += ((self.protonMass-self.eMass) * (self.__charge - z))
                theoreticalPeaks['m/z'] = self.spectrumHandler.getMz(theoreticalPeaks['m/z'], z * -1, fragment.getRadicals())
                if (self.configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < upperBound):
                    peaksToFind = []
                    for peak in theoreticalPeaks[:np.random.randint(low=1,high=len(isotopePattern))]:
                        dummyPeak,error = self.getDummyPeak(peak)
                        dummyPeak[0][1] =round(10**8*dummyPeak[0][1])
                        peaksToFind.append(dummyPeak[0])
                    peaksToFind=np.array(peaksToFind)

                    #find ions
                    self.spectrumHandler.setSpectrum(np.concatenate((self.spectrumHandler.getSpectrum(),peaksToFind),axis=0))
                    self.spectrumHandler.findIons(self.builder.getFragmentLibrary())

                    #test
                    found = self.spectrumHandler.getFoundIons()
                    foundFragment = None
                    for frag in found:
                        if (frag.getName() == fragment.getName()) and (frag.getCharge() == z):
                            foundFragment=frag
                    self.assertEqual(fragment.getName(),foundFragment.getName())
                    foundIsoPattern = foundFragment.getIsotopePattern()
                    for j,peak in enumerate(peaksToFind):
                        self.assertAlmostEqual(peak[1],foundIsoPattern[j][1])
                    self.spectrumHandler.setSpectrum(originalSpectrum)
        self.setUp()

    def test_find_ions_noise(self):
        #prepare everything
        self.spectrumHandler.findIons(self.builder.getFragmentLibrary())
        self.assertEqual(0,len(self.spectrumHandler.getFoundIons()))
        precModCharge = self.spectrumHandler.getModCharge(self.builder.getPrecursor())
        upperBound = self.spectrumHandler.getUpperBound()
        library = self.builder.getFragmentLibrary()
        for i in range(2):
            fragment = library[np.random.randint(low=0,high=len(library))]
            isotopePattern = fragment.getIsotopePattern()
            for z in self.spectrumHandler.getChargeRange(fragment, precModCharge):
                theoreticalPeaks = deepcopy(isotopePattern)
                theoreticalPeaks['m/z'] = self.spectrumHandler.getMz(theoreticalPeaks['m/z'], z * -1,
                                                                     fragment.getRadicals())
                if (self.configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < upperBound):
                    sortedPeaks = sorted(theoreticalPeaks,key=lambda row:row[1],reverse=True)

                    dummyPeak, error = self.getDummyPeak(sortedPeaks[0])
                    dummyPeak[0][1] = round(self.settings['noiseLimit']/100 * dummyPeak[0][1])
                    peaksToFind = dummyPeak

                    # find ions
                    self.spectrumHandler.setSpectrum(
                        np.concatenate((self.spectrumHandler.getSpectrum(), peaksToFind), axis=0))
                    self.spectrumHandler.findIons(self.builder.getFragmentLibrary())

                    # test
                    found = self.spectrumHandler.getIonsInNoise()
                    foundFragment = None
                    for frag in found:
                        if (frag.getName() == fragment.getName()) and (frag.getCharge() == z):
                            foundFragment = frag
                    self.assertEqual(fragment.getName(), foundFragment.getName())
                    foundIsoPattern = foundFragment.getIsotopePattern()
                    for peak in foundIsoPattern:
                        if peak['m/z'] in peaksToFind[:,0]:
                            self.assertAlmostEqual(peaksToFind[0,1], peak['relAb'])
                        else:
                            self.assertAlmostEqual(0, peak['relAb'])

            self.setUp()

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

    def tearDown(self):
        deleteTestSequences(SequenceService())