import os
from copy import deepcopy
from unittest import TestCase
import numpy as np
from numpy.random import randint

from src.resources import path
from src.services.FormulaFunctions import eMass, protMass
from src.MolecularFormula import MolecularFormula
from src.entities.Ions import Fragment
from src.entities.SearchSettings import SearchSettings
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.services.assign_services.TD_SpectrumHandler import SpectrumHandler
from src.services.assign_services.AbstractSpectrumHandler import getErrorLimit, calculateError, getMz
from tests.test_other.test_MolecularFormula import averaginine, averagine
from tests.test_services.test_LibraryBuilder import initTestSequences


def concatenateArrays(new, spectrumHandler):
    newSpec = [row for row in spectrumHandler.getSpectrum()]
    try:
        if len(new > 1):
            # print("longer")
            for row in new:
                newSpec.append((row[0], row[1]))
        else:
            newSpec.append(new[0])
    except:
        newSpec.append(new[0])
    spectrumHandler.setSpectrum(np.array(newSpec, dtype=spectrumHandler.getDtype()))


def initTestLibraryBuilder(charge=-3, modif='CMCT'):
    initTestSequences()
    configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
    configs['zTolerance'] = 1.0
    filePath = os.path.join(path, 'tests', 'test_files', 'dummySpectrum.txt')
    settings = {'sequName': 'dummyRNA', 'charge': charge, 'fragmentation': 'RNA CAD', 'modifications': modif,
                'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 10 ** 6, 'fragLib': ''}
    props = SearchSettings(settings['sequName'], settings['fragmentation'], settings['modifications'])
    builder = FragmentLibraryBuilder(props, 1)
    builder.createFragmentLibrary()
    builder.addNewIsotopePattern()
    return configs, settings, props, builder


class TestSpectrumHandler(TestCase):
    def setUp(self):
        '''filePath = os.path.join(path, 'tests', 'dummySpectrum.txt')
        self._configs = ConfigurationHandlerFactory.getConfigHandler().getAll()

        self.settings = {'sequName': 'dummyRNA', 'charge': -3, 'fragmentation': 'RNA CAD', 'modifications': 'CMCT',
                    'nrMod': 1, 'spectralData': filePath, 'noiseLimit': 10**5, 'fragLib': ''}
        self.props = SearchSettings(self.settings['sequName'], self.settings['fragmentation'], self.settings['modifications'])
        self.builder = FragmentLibraryBuilder(self.props,1)
        self.builder.createFragmentLibrary()
        self.builder.addNewIsotopePattern()'''
        self.configs, self.settings, self.props, self.builder = initTestLibraryBuilder()
        self.spectrumHandler = SpectrumHandler(self.props, self.builder.getPrecursor(), self.settings, self.configs)

        self.settingsProt = {'sequName': 'dummyProt', 'charge': 4, 'fragmentation': 'Protein CAD', 'modifications': '-',
                             'nrMod': 0, 'spectralData': os.path.join(path, 'tests', 'test_files', 'dummySpectrum.txt'),
                             'noiseLimit': 10 ** 5, 'fragLib': ''}
        self.propsProt = SearchSettings(self.settingsProt['sequName'], self.settingsProt['fragmentation'],
                                        self.settingsProt['modifications'])
        self.builderProt = FragmentLibraryBuilder(self.propsProt, 0)
        self.builderProt.createFragmentLibrary()
        self.spectrumHandlerProt = SpectrumHandler(self.propsProt, self.builderProt.getPrecursor(), self.settingsProt,
                                                   self.configs)
        self.spectrumHandler.setNormalisationFactor(self.spectrumHandler.getNormalisationFactor())
        self.standardSpec = self.spectrumHandler.getSpectrum()
        '''builder2 = FragmentLibraryBuilder(self.props,2)
        builder2.createFragmentLibrary()
        settings2 = self.settings
        settings2['nrMod'] = 2
        self.spectrumHandler2 = SpectrumHandler(self.props,builder2.getPrecursor(),settings2)'''

    def test_calcPrecCharge(self):
        self.assertEqual(5, self.spectrumHandler.calcPrecCharge(6, 1))
        self.assertEqual(5, self.spectrumHandler.calcPrecCharge(-6, 1))

    def test_add_spectrum_from_csv_and_txt(self):
        # with open(os.path.join(path, 'tests', 'test_files', 'dummySpectrum.csv'), 'r') as f:
        # fromCsv = self.spectrumHandler.addSpectrumFromCsv(os.path.join(path, 'tests', 'test_files', 'dummySpectrum.csv'))
        # with open(self.settings['spectralData'], 'r') as f:
        self.assertEqual(1090, len(self.spectrumHandler.addSpectrumFromTxt(self.settings['spectralData'])))
        """N = len(fromCsv)
        self.assertEqual(N, len(fromTxt))
        for row in range(N):
            print(fromCsv[row], fromTxt[row])
            for col in range(2):
                self.assertAlmostEqual(fromCsv[row, col], fromTxt[row, col])"""

    def test_find_upper_bound(self):
        self.assertAlmostEqual(1800 + self.configs['upperBoundTolerance'], self.spectrumHandler.findUpperBound())

    def test_calculate_noise(self):
        window = 40
        for i in range(10):
            point = 400 + i * 100
            self.assertAlmostEqual(1.05, self.spectrumHandler.calculateNoise(point, window) / (
                    10 ** 6 + 100 * point), delta=0.12)

    def test_get_peaks_in_window(self):
        allPeaks = np.column_stack((np.arange(100., 300.), np.ones(200))).astype(self.spectrumHandler.getDtype())
        peaks = self.spectrumHandler.getPeaksInWindow(allPeaks, 200, 10)
        for theo, peak in zip(np.arange(196., 205.), peaks):
            self.assertAlmostEqual(theo, peak[0])

    def test_get_mod_charge(self):
        zEffect = self.props.getModifPattern().getItems()[0].getZEffect()
        fragment0 = Fragment('c', 5, '', '', [], 0)
        self.assertAlmostEqual(0, self.spectrumHandler.getModCharge(fragment0))
        fragment1 = Fragment('c', 5, '+CMCT', '', [], 0)
        self.assertAlmostEqual(zEffect, self.spectrumHandler.getModCharge(fragment1))
        fragment2 = Fragment('c', 5, '+2CMCT', '', [], 0)
        self.assertAlmostEqual(2 * zEffect, self.spectrumHandler.getModCharge(fragment2))

    def test_get_normalization_factor(self):
        normalisationFactor = abs(self.settings['charge']) / (len(self.props.getSequenceList()) - 1)
        self.assertAlmostEqual(normalisationFactor, self.spectrumHandler.getNormalisationFactor())

    def test_get_charge_range(self):
        nrP = len(self.props.getSequenceList()) - 1
        precModCharge = self.spectrumHandler.getModCharge(Fragment('c', 3, '+CMCT', '', [], 0))
        # self.spectrumHandler.setNormalisationFactor(self.spectrumHandler.getNormalisationFactor())
        tolerance = self.configs['zTolerance']
        precCharge = abs(self.settings['charge'])
        # self.spectrumHandlerProt.setNormalisationFactor(self.spectrumHandlerProt.getNormalisationFactor())
        self.spectrumHandler.setPrecModCharge(precModCharge)
        """rangeCalc = self.spectrumHandler.getChargeRange(Fragment('y', 1, '', MolecularFormula({'P': 0}), [], 0))
        self.assertEqual(0, rangeCalc.stop)"""

        rangeTheo = self.getRange(precCharge / nrP + precModCharge, tolerance, precCharge)
        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('c', 3, '', MolecularFormula({'P': 1}), [], 0))
        self.assertEqual(rangeTheo.start, rangeCalc.start)
        self.assertEqual(rangeTheo.stop, rangeCalc.stop)

        rangeTheo = self.getRange(2 * precCharge / nrP + precModCharge, tolerance, precCharge)
        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('c', 3, '', MolecularFormula({'P': 2}), [], 0))
        self.assertEqual(rangeTheo.start, rangeCalc.start)
        self.assertEqual(rangeTheo.stop, rangeCalc.stop)

        rangeTheo = self.getRange(2 * precCharge / nrP, tolerance, precCharge)
        rangeCalc = self.spectrumHandler.getChargeRange(Fragment('c', 3, '+CMCT', MolecularFormula({'P': 2}), [], 0))
        self.assertEqual(rangeTheo.start, rangeCalc.start)
        self.assertEqual(rangeTheo.stop, rangeCalc.stop)

        rangeTheo = self.getRange(abs(self.settingsProt['charge'] * 3) / len(self.propsProt.getSequenceList()),
                                  tolerance, self.settingsProt['charge'])
        self.spectrumHandlerProt.setPrecModCharge(0)
        rangeCalc = self.spectrumHandlerProt.getChargeRange(
            Fragment('c', 3, '', MolecularFormula({'P': 1}), ['G', 'A', 'P'], 0))
        self.assertEqual(rangeTheo.start, rangeCalc.start)
        self.assertEqual(rangeTheo.stop, rangeCalc.stop)
        rangeTheo = self.getRange(abs(self.settingsProt['charge'] * 3) / len(self.propsProt.getSequenceList()),  # - 1,
                                  tolerance, self.settingsProt['charge'])
        rangeCalc = self.spectrumHandlerProt.getChargeRange(
            Fragment('c', 3, '', MolecularFormula({'P': 1}), ['G', 'A', 'P'], 1))
        self.assertEqual(rangeTheo.start, rangeCalc.start)
        self.assertEqual(rangeTheo.stop, rangeCalc.stop)

    @staticmethod
    def getRange(probZ, tolerance, precCharge):
        low = int(round(probZ - tolerance))
        if low < 1:
            low = 1
        high = precCharge
        if probZ + tolerance < precCharge:
            high = int(round(probZ + tolerance))
        return range(low, high + 1)

    def test_get_correct_peak(self):
        '''isotopePattern_dtype = np.dtype([('m/z', np.float64), ('relAb', np.float64),
                                       ('calcInt', np.float64), ('error', np.float32), ('used', np.bool_)])'''
        dtype = [('m/z', np.float64), ('calcInt', np.float64)]
        theoPeak = np.array([(300.54, 0.5)], dtype=dtype)
        self.assertEqual(0, self.spectrumHandler.getCorrectPeak(np.array([]), theoPeak[0])[1])
        dummyPeak, error = self.getDummyPeak(theoPeak[0])
        dummyStructuredPeak = np.array([(dummyPeak[0][0], dummyPeak[0][1])], dtype=self.spectrumHandler.getDtype())
        print("*3*", dummyStructuredPeak)
        finPeak = self.spectrumHandler.getCorrectPeak(dummyStructuredPeak, theoPeak[0])
        print(dummyPeak.astype(self.spectrumHandler.getDtype())[0], finPeak)
        self.assertAlmostEqual(dummyPeak[0][0], finPeak[0])
        self.assertAlmostEqual(dummyPeak[0][1], finPeak[1])
        self.assertAlmostEqual(theoPeak['calcInt'], finPeak[2])
        self.assertAlmostEqual(error, finPeak[3])
        self.assertAlmostEqual(True, finPeak[4])
        for i in range(20):
            dummyPeak1, error1 = self.getDummyPeak(theoPeak[0])
            dummyPeak2 = deepcopy(dummyPeak1)
            dummyPeak2[0] *= (1 + error1 / 10 ** 6)
            dummyPeak3 = deepcopy(dummyPeak1)
            dummyPeak3[0] *= (1 - 2.1 * error1 / 10 ** 6)

            dummyPeaks = np.array([(peak[0][0], peak[0][1]) for peak in (dummyPeak1, dummyPeak2, dummyPeak3)],
                                  dtype=self.spectrumHandler.getDtype())
            finPeak = self.spectrumHandler.getCorrectPeak(dummyPeaks, theoPeak[0])
            self.assertAlmostEqual(dummyPeak1[0][0], finPeak[0])
            self.assertAlmostEqual(dummyPeak1[0][1], finPeak[1])
            self.assertAlmostEqual(theoPeak['calcInt'], finPeak[2])
            self.assertAlmostEqual(error1, finPeak[3])
            self.assertAlmostEqual(True, finPeak[4])
            theoPeak['m/z'] += 100

    def getDummyPeak(self, theoPeak, outside=False, dtype=None):
        configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        randomError = np.random.rand(1)
        if outside:
            randomError += 1
        randomError *= (-1) ** (np.random.randint(2)) * getErrorLimit(theoPeak['m/z'], configs['k'], configs['d'])
        print("randomError", randomError)
        mz = theoPeak[0] * (1 + randomError[0] / 10 ** 6)
        print(mz, theoPeak[1],
              (theoPeak[1] + np.random.rand(1) / 10 * (-1) ** (np.random.randint(2)))[0])
        foundI = (theoPeak[1] + np.random.rand(1)[0] / 10 * (-1) ** (np.random.randint(2)))
        print(theoPeak[1], np.random.rand(1)[0], 10 * (-1) ** np.random.randint(2))
        print(mz, foundI)
        arr = np.array([(mz, foundI)])
        # dtype=[('m/z', np.float64), ('calcInt', np.float64)])
        """if dtype is not None:
            arr = arr.astype(dtype)"""
        print("arr", arr)
        return arr, randomError[0]

    def test_find_peak(self):
        self.spectrumHandler.setSpectrum(self.standardSpec)
        dtype = [('m/z', float), ('calcInt', float)]
        theoPeak = np.array([(310.58, 0.5)], dtype=dtype)
        for i in range(5):
            dummyPeak, error = self.getDummyPeak(theoPeak[0], True)

            dummyPeak[0][1] *= 10 ** 7
            """oldspec = [row for row in self.spectrumHandler.getSpectrum()]
            print(list(dummyPeak[0]), oldspec)
            spec = np.array(oldspec + list(dummyPeak[0]),dtype=self.spectrumHandler.getDtype())
            self.spectrumHandler.setSpectrum(spec)"""
            dummyStructuredPeak = np.array([(dummyPeak[0][0], dummyPeak[0][1])])
            concatenateArrays(dummyStructuredPeak, self.spectrumHandler)
            self.assertEqual(0, self.spectrumHandler.findPeak(theoPeak[0])[1])
            theoPeak['m/z'] += 100

        self.spectrumHandler.setSpectrum(self.standardSpec)
        for i in range(5):
            dummyPeak, error = self.getDummyPeak(theoPeak[0])
            dummyPeak[0][1] *= 10 ** 7
            dummyStructuredPeak = np.array([(dummyPeak[0][0], dummyPeak[0][1])], dtype=self.spectrumHandler.getDtype())
            concatenateArrays(dummyStructuredPeak, self.spectrumHandler)
            self.assertTrue(self.spectrumHandler.findPeak(theoPeak[0])[1] > 0)
            theoPeak['m/z'] += 100
        self.setUp()

    def test_find_ions_basic(self):
        # prepare everything
        self.spectrumHandler.setSpectrum(self.standardSpec)
        self.spectrumHandler.findIons(self.builder.getFragmentLibrary())
        print([ion.getHash() for ion in self.spectrumHandler.getFoundIons()])
        self.assertEqual(0, len(self.spectrumHandler.getFoundIons()))
        precModCharge = self.spectrumHandler.getModCharge(self.builder.getPrecursor())
        # peaksToFind = []
        # nrsOfPeaks = {}
        originalSpectrum = self.spectrumHandler.getSpectrum()
        upperBound = self.spectrumHandler.getUpperBound()
        for i, fragment in enumerate(self.builder.getFragmentLibrary()):
            isotopePattern = fragment.getIsotopePattern()
            print(isotopePattern)
            for z in self.spectrumHandler.getChargeRange(fragment):
                theoreticalPeaks = deepcopy(isotopePattern)
                # if self.__settings['dissociation'] in ['ECD', 'EDD', 'ETD'] and fragment.number == 0:
                #    theoreticalPeaks['mass'] += ((self.protonMass-self.eMass) * (self.__charge - z))
                theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * -1, fragment.getRadicals())
                print(theoreticalPeaks)
                if (self.configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < upperBound):
                    peaksToFind = []
                    for peak in theoreticalPeaks[:np.random.randint(low=2, high=len(isotopePattern))]:
                        dummyPeak, error = self.getDummyPeak(peak)
                        dummyPeak[0][1] = round(10 ** 8 * dummyPeak[0][1])
                        peaksToFind.append(dummyPeak[0])
                    peaksToFind = np.array(peaksToFind)
                    print("peaksToFind", peaksToFind)

                    # find ion
                    """dummyStructuredPeak = np.array([(dummyPeak[0][0], dummyPeak[0][1])],
                                                   dtype=self.spectrumHandler.getDtype())
                    concatenateArrays(dummyStructuredPeak, self.spectrumHandler)"""
                    concatenateArrays(peaksToFind, self.spectrumHandler)
                    self.spectrumHandler.findIons(self.builder.getFragmentLibrary())

                    # test
                    found = self.spectrumHandler.getFoundIons()
                    foundFragment = None
                    print(found)
                    for frag in found:
                        if (frag.getName() == fragment.getName()) and (frag.getCharge() == z):
                            foundFragment = frag
                    self.assertEqual(fragment.getName(), foundFragment.getName())
                    foundIsoPattern = foundFragment.getIsotopePattern()
                    for j, peak in enumerate(peaksToFind):
                        self.assertAlmostEqual(peak[1], foundIsoPattern[j][1])
                    self.spectrumHandler.setSpectrum(originalSpectrum)
        self.setUp()

    def test_find_ions_noise(self):
        # prepare everything
        self.spectrumHandler.setSpectrum(self.standardSpec)
        self.spectrumHandler.findIons(self.builder.getFragmentLibrary())
        # print("fdslö", self.spectrumHandler.getFoundIons()[0].getHash())
        self.assertEqual(0, len(self.spectrumHandler.getFoundIons()))
        precModCharge = self.spectrumHandler.getModCharge(self.builder.getPrecursor())
        upperBound = self.spectrumHandler.getUpperBound()
        library = self.builder.getFragmentLibrary()
        for i in range(2):
            fragment = library[np.random.randint(low=0, high=len(library))]
            isotopePattern = fragment.getIsotopePattern()
            for z in self.spectrumHandler.getChargeRange(fragment):
                theoreticalPeaks = deepcopy(isotopePattern)
                theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * -1,
                                                fragment.getRadicals())
                if (self.configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < upperBound):
                    sortedPeaks = sorted(theoreticalPeaks, key=lambda row: row[1], reverse=True)

                    dummyPeak, error = self.getDummyPeak(sortedPeaks[0])
                    dummyPeak[0][1] = round(self.settings['noiseLimit'] / 100 * dummyPeak[0][1])
                    peaksToFind = dummyPeak

                    # find ions
                    concatenateArrays(peaksToFind, self.spectrumHandler)
                    print("dsf", self.spectrumHandler.getSpectrum())
                    """self.spectrumHandler.setSpectrum(
                        np.concatenate((self.spectrumHandler.getSpectrum(), peaksToFind), axis=0))"""
                    self.spectrumHandler.findIons(self.builder.getFragmentLibrary())

                    # test
                    found = self.spectrumHandler.getIonsInNoise()
                    foundFragment = None
                    for frag in found:
                        if (frag.getName() == fragment.getName()) and (frag.getCharge() == z):
                            foundFragment = frag
                    self.assertEqual(fragment.getName(), foundFragment.getName())
                    print(foundFragment.getName(), foundFragment.getIsotopePattern())
                    foundIsoPattern = foundFragment.getIsotopePattern()
                    print(foundIsoPattern, foundIsoPattern.dtype)
                    for peak in foundIsoPattern:
                        if peak['m/z'] in peaksToFind[:, 0]:
                            self.assertAlmostEqual(peaksToFind[0, 1], peak['I'])
                        else:
                            self.assertAlmostEqual(0, peak['I'])

            self.setUp()

    def test_get_charged_isotope_pattern(self):
        configs, settings, props, builder = initTestLibraryBuilder(30)
        spectrumHandlerPos = SpectrumHandler(props, builder.getPrecursor(), settings, configs)
        configs, settings, props, builder = initTestLibraryBuilder(-30)
        spectrumHandlerNeg = SpectrumHandler(props, builder.getPrecursor(), settings, configs)
        spectrumHandlerPos.getProtonIsotopePatterns()
        spectrumHandlerNeg.getProtonIsotopePatterns()
        for i in range(10):
            randNr = randint(1, 100)
            molFormulaDummy_RNA = MolecularFormula({key: int(round(val * randNr)) for key, val in averaginine.items()})
            molFormulaDummy_prot = MolecularFormula({key: int(round(val * randNr)) for key, val in averagine.items()})
            for molFormulaDummy_i in [molFormulaDummy_RNA, molFormulaDummy_prot]:
                exactIsotopePattern = molFormulaDummy_i.calculateIsotopePattern(0.996)
                # neutralIsotopePatternFFT = molFormulaDummy_i.calculateIsotopePatternFFT(1,exactIsotopePattern)
                exactIsotopePattern['calcInt'] /= np.sum(exactIsotopePattern['calcInt'])
                # print('exact:',exactIsotopePattern[0])
                maxZ = int(randNr / 2) + 2
                z = randint(1, maxZ)
                molForm_i_pos = molFormulaDummy_i.subtractFormula({'H': z})
                molForm_i_neg = molFormulaDummy_i.addFormula({'H': z})
                correctedPos = spectrumHandlerPos.getChargedIsotopePattern2(molForm_i_pos,
                                                                            molForm_i_pos.calculateIsotopePattern(
                                                                                0.996), z)  # ,neutralIsotopePatternFFT)
                correctedPos['m/z'] = getMz(correctedPos['m/z'], z, 0)
                exactIsotopePattern_pos = deepcopy(exactIsotopePattern)
                exactIsotopePattern_pos['m/z'] = exactIsotopePattern_pos['m/z'] / z - eMass
                exactIsotopePattern_neg = deepcopy(exactIsotopePattern)
                exactIsotopePattern_neg['m/z'] = exactIsotopePattern_neg['m/z'] / z + eMass
                # print(correctedPos['m/z'], exactIsotopePattern['m/z'])

                correctedNeg = spectrumHandlerNeg.getChargedIsotopePattern2(molForm_i_neg,
                                                                            molForm_i_neg.calculateIsotopePattern(
                                                                                0.996), z)  # ,neutralIsotopePatternFFT)
                correctedNeg['m/z'] = getMz(correctedNeg['m/z'], -z, 0)
                print(self.testIsotopePattern(exactIsotopePattern_pos, correctedPos, deltaCalcInt=1 * 10e-4))
                print(self.testIsotopePattern(exactIsotopePattern_neg, correctedNeg, deltaCalcInt=1 * 10e-4))
            '''print('max error', molFormulaDummy_i.toString(),
                  self.testIsotopePattern(exactIsotopePattern,molForm_i_cor_pos,max_ppm=1.5, deltaCalcInt=8*10e-5))
            print('max error', molFormulaDummy_i.toString(),
                  self.testIsotopePattern(exactIsotopePattern,molForm_i_cor_neg,max_ppm=1.5, deltaCalcInt=8*10e-5))'''
            '''except AssertionError as e:
                print(molFormulaDummy_i.toString())
                print(exactIsotopePattern,fastIsotopePattern)
                raise e'''

    def testIsotopePattern(self, theoIsotopePattern=None, calcIsotopePattern=None, complete=True, max_ppm=0.3,
                           deltaCalcInt=5 * 10e-6):
        if theoIsotopePattern is not None:
            ppms, diffs = [], []
            # theoIsotopePattern = np.array(theoIsotopePattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])
            # theoIsotopePattern['calcInt'] *= (calcIsotopePattern['calcInt'][0] / theoIsotopePattern['calcInt'][0])
            if len(theoIsotopePattern) > (len(calcIsotopePattern) + 1):
                raise Exception('Length of calculated isotope pattern to short')
            for i in range(min(len(theoIsotopePattern), len(calcIsotopePattern))):
                error = calculateError(theoIsotopePattern[i]['m/z'], calcIsotopePattern[i]['m/z'])
                self.assertLess(np.abs(error), max_ppm)
                ppms.append(error)

                # self.assertAlmostEqual(theoIsotopePattern[i]['m/z']/z, calcIsotopePattern[i]['m/z'], delta=5 * 10 ** (-6))
                self.assertAlmostEqual(theoIsotopePattern[i]['calcInt'], calcIsotopePattern[i]['calcInt'],
                                       delta=deltaCalcInt)
                diffs.append(calcIsotopePattern[i]['calcInt'] - theoIsotopePattern[i]['calcInt'])
            if complete:
                self.assertAlmostEqual(1.0, float(np.sum(calcIsotopePattern['calcInt'])), delta=0.005)
            # self.assertLess(np.sum(calcIsotopePattern['calcInt']), 1)
            diffs = np.array(diffs)
            return diffs[np.argmax(np.abs(diffs))], np.average(np.abs(diffs))

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


    def test_calculate_error(self):
        self.fail()   

    

    def test_set_searched_charge_states(self):
        self.fail()'''

    '''def tearDown(self):
        deleteTestSequences()'''


    def test_get_mz(self):
        Mass = 666.666
        self.assertAlmostEqual(Mass, getMz(Mass, 0, 0))
        for z in range(-8,8):
            if z!=0:
                self.assertAlmostEqual((Mass+z*1.007276)/abs(z), getMz(Mass, z, 0),delta=10**-6)
        self.assertAlmostEqual((Mass+5*protMass+eMass)/4, getMz(Mass, 4, 1),delta=10**-6)
        self.assertAlmostEqual((Mass+6*protMass+2*eMass)/4, getMz(Mass, 4, 2),delta=10**-6)
        self.assertAlmostEqual((Mass-5*protMass-eMass)/4, getMz(Mass, -4, 1),delta=10**-6)
        self.assertAlmostEqual((Mass-6*protMass-2*eMass)/4, getMz(Mass, -4, 2),delta=10**-6)
