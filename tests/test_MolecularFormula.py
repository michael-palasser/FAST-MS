from unittest import TestCase
import numpy as np
from random import randint
from src.fastFunctions import getByIndex, calculatePeptFineStructure, calculateFineStructure, calculateNuclFineStructure

from src.MolecularFormula import MolecularFormula
from src.services.DataServices import PeriodicTableService
from src.services.assign_services.AbstractSpectrumHandler import calculateError

averagine ={'C': 4.9384, 'H': 7.7583, 'N': 1.3577, 'O': 1.4773, 'S': 0.0417}
averaginine = {'C': 9.5, 'H': 11.75, 'N': 3.75, 'O': 7, 'P': 1}
molFormulaDummy = MolecularFormula('C5H4N3O')
RNA_formulaDummy = MolecularFormula('C38H48N15O26P3')  # GACU
peptideFormulaDummy = MolecularFormula('C36H56N12O14S')  # GCASDQHPV
uniFormulaDummy = MolecularFormula('C5H5N5ONa')
RNA_pattern = np.array([(1223.21078, 0.58727166), (1224.21346, 0.28260795), (1225.21578 , 0.09801103 ),
                        (1226.21814, 0.02534772), (1227.22043, 0.00552071)],
                       dtype=[('m/z', np.float64), ('calcInt', np.float64)])
peptide_pattern = np.array([(912.37597, 0.59277779), (913.37869, 0.26845428), (914.37872, 0.10304914),
                            (915.37977, 0.02810875), (916.38111, 0.00617633)],
                           dtype=[('m/z', np.float64), ('calcInt', np.float64)])
uni_pattern = np.array([(174.03918, 0.92771614), (175.04099, 0.06800264), (176.04295, 0.00409642)],
                       dtype=[('m/z', np.float64), ('calcInt', np.float64)])

dict0 = {'C': 5, 'H': 4, 'N': 3, 'O': 1}
dict1 = {'C': 5, 'H': 4, 'N': 3, 'O': 1, 'S': 10}
dict2 = {'C': 10, 'H': 8, 'N': 6, 'O': 2, 'S': 10}
MIN_SUM = 0.996


class MolecularFormulaTest(TestCase):

    def test_init(self):
        self.assertEqual(dict0, molFormulaDummy.getFormulaDict())

    def test_add_formula(self):
        self.assertEqual(dict2, molFormulaDummy.addFormula(dict1).getFormulaDict())

    def test_subtract_formula(self):
        molFormula2 = MolecularFormula(dict1)
        self.assertEqual({'C': 0, 'H': 0, 'N': 0, 'O': 0, 'S': 10}, molFormula2.subtractFormula(dict0).getFormulaDict())

    def test_multiply_formula(self):
        self.assertEqual(dict2, molFormulaDummy.multiplyFormula(2).addFormula({'S': 10}).getFormulaDict())

    def test_check_for_negative_values(self):
        self.assertTrue(molFormulaDummy.subtractFormula({'S': 1}))

    '''def test_to_string(self):
        self.fail()'''

    def test_determine_system(self):
        molFormula = MolecularFormula('C5H4N3O')
        elements = [key for key, val in molFormula.getFormulaDict().items() if val > 0]
        self.assertTrue(molFormula.checkSystem(elements, {'C', 'H', 'N', 'O', 'P'}))
        molFormula = MolecularFormula('C5H4N3OS0')
        elements = [key for key, val in molFormula.getFormulaDict().items() if val > 0]
        self.assertTrue(molFormula.checkSystem(elements, {'C', 'H', 'N', 'O', 'P'}))
        molFormula = MolecularFormula('C38H48N15O26P3')
        elements = [key for key, val in molFormula.getFormulaDict().items() if val > 0]
        self.assertTrue(molFormula.checkSystem(elements, {'C', 'H', 'N', 'O', 'P'}))
        molFormula = MolecularFormula('C36H56N12O14S')
        elements = [key for key, val in molFormula.getFormulaDict().items() if val > 0]
        self.assertTrue(molFormula.checkSystem(elements, {'C', 'H', 'N', 'O', 'S'}))
        molFormula = MolecularFormula('C5H5N5ONa')
        elements = [key for key, val in molFormula.getFormulaDict().items() if val > 0]
        self.assertFalse(molFormula.checkSystem(elements, {'C', 'H', 'N', 'O', 'P'}))
        self.assertFalse(molFormula.checkSystem(elements, {'C', 'H', 'N', 'O', 'S'}))

    def testIsotopeTable(self, isotopeTable=None, values=None):
        if type(isotopeTable) != type(None):
            self.assertEqual(len(isotopeTable), 9)
            self.assertEqual(len(isotopeTable[0]), 6)
            for row in isotopeTable:
                self.assertAlmostEqual(0, row['nrIso'])
                self.assertAlmostEqual(values[int(row['index'])], row['nr'])

    def sortByMass(self, array):
        return np.sort(array, order='mass')

    def test_makeNucIsotopeTable(self):
        isotopeTable = molFormulaDummy.makeNucIsotopeTable()
        values = list(molFormulaDummy.getFormulaDict().values())
        self.testIsotopeTable(isotopeTable, values)
        return isotopeTable

    def test_makeProteinIsotopeTable(self):
        isotopeTable = molFormulaDummy.makeProteinIsotopeTable()
        values = list(molFormulaDummy.getFormulaDict().values())
        self.testIsotopeTable(isotopeTable, values)
        return isotopeTable

    def test_makeIsotopeTable(self):
        isotopeTable = molFormulaDummy.makeIsotopeTable()
        values = list(molFormulaDummy.getFormulaDict().values())
        self.testIsotopeTable(isotopeTable, values)
        return isotopeTable

    def testMakeIsotopeTable_functions(self):
        nucIsotopeTable = self.sortByMass(self.test_makeNucIsotopeTable())
        protIsotopeTable = self.sortByMass(self.test_makeProteinIsotopeTable())
        uniIsotopeTable = self.sortByMass(self.test_makeIsotopeTable())
        for i in range(len(nucIsotopeTable)):
            for j in range(len(nucIsotopeTable[0])):
                self.assertAlmostEqual(nucIsotopeTable[i][j], protIsotopeTable[i][j])
                self.assertAlmostEqual(nucIsotopeTable[i][j], uniIsotopeTable[i][j])
        isotopeTable = MolecularFormula('C5H5N5O30P').makeIsotopeTable()
        self.assertEqual(2, len(getByIndex(isotopeTable, 0)))

    def test_calculate_mono_isotopic(self):
        self.assertAlmostEqual(1223.210776, RNA_formulaDummy.calculateMonoIsotopic(), delta=5 * 10 ** (-6))
        self.assertAlmostEqual(912.375965, peptideFormulaDummy.calculateMonoIsotopic(), delta=5 * 10 ** (-6))


    def test_calculate_isotope_pattern(self):
        P2 = MolecularFormula('P2').calculateIsotopePattern(MIN_SUM)
        self.assertAlmostEqual(2 * 30.973762, P2['m/z'][0])
        self.assertAlmostEqual(1, P2['calcInt'][0])
        self.testIsotopePattern(RNA_pattern, RNA_formulaDummy.calculateIsotopePattern(MIN_SUM))
        self.testIsotopePattern(peptide_pattern, peptideFormulaDummy.calculateIsotopePattern(MIN_SUM))
        self.testIsotopePattern(uni_pattern, uniFormulaDummy.calculateIsotopePattern(MIN_SUM))
        for i in range(10):
            molFormulaDummy_i = MolecularFormula({'C': randint(5, 50), 'H': randint(10, 100),
                                                  'N': randint(1, 40), 'O': randint(1, 40),
                                                  'P': randint(0, 2), 'S': randint(0, 2)})
            calcIsotopePattern = molFormulaDummy_i.calculateIsotopePattern(MIN_SUM)
            try:
                self.assertAlmostEqual(1.0, float(np.sum(calcIsotopePattern['calcInt'])), delta=0.004)
                self.assertTrue(np.sum(calcIsotopePattern['calcInt']) < 1)
            except AssertionError:
                print(calcIsotopePattern)
                raise AssertionError(molFormulaDummy_i.getFormulaDict())

    def testIsotopePattern(self, theoIsotopePattern=None, calcIsotopePattern=None, complete=True, max_ppm=0.5,
                           deltaCalcInt=5*10e-6):
        if theoIsotopePattern is not None:
            ppms = []
            # theoIsotopePattern = np.array(theoIsotopePattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])
            #theoIsotopePattern['calcInt'] *= (calcIsotopePattern['calcInt'][0] / theoIsotopePattern['calcInt'][0])
            self.assertLess(np.sum(calcIsotopePattern['calcInt']), 1.000)
            if complete:
                theoIsotopePattern['calcInt']/=np.sum(theoIsotopePattern['calcInt'])
                calcIsotopePattern['calcInt']/=np.sum(calcIsotopePattern['calcInt'])
            else:
                theoIsotopePattern['calcInt'] *= (calcIsotopePattern['calcInt'][0] / theoIsotopePattern['calcInt'][0])
            if len(theoIsotopePattern) > (len(calcIsotopePattern) + 1):
                raise Exception('Length of calculated isotope pattern to short')
            for i in range(min(len(theoIsotopePattern),len(calcIsotopePattern))):
                error =calculateError(calcIsotopePattern[i]['m/z'],theoIsotopePattern[i]['m/z'])
                self.assertLess(np.abs(error),max_ppm)
                #self.assertAlmostEqual(theoIsotopePattern[i]['m/z'], calcIsotopePattern[i]['m/z'], delta=5 * 10 ** (-6))
                self.assertAlmostEqual(theoIsotopePattern[i]['calcInt'], calcIsotopePattern[i]['calcInt'],
                                       delta=deltaCalcInt)
                ppms.append(error)
            if complete:
                self.assertAlmostEqual(1.0, float(np.sum(calcIsotopePattern['calcInt'])), delta=0.005)
            ppms = np.array(ppms)
            return ppms[np.argmax(np.abs(ppms))], np.average(np.abs(ppms))


    def test_make_ffttables(self):
        formDict = {'C': 100, 'H': 100, 'N': 55, 'O': 30, 'S': 1, 'Na': 1}
        formula = MolecularFormula(formDict)
        abundanceTable, elemNrs,dm = formula.makeFFTTables(formula.calculateMonoIsotopic())
        periodicTable = formula.getPeriodicTable()
        checked = []
        for i in range(len(abundanceTable)):
            elem = list(formDict.keys())[i]
            for isotope in periodicTable[elem]:
                self.assertAlmostEqual(isotope[2], abundanceTable[i,int(round(isotope[1]))])
                checked.append((i,int(round(isotope[1]))))
            self.assertAlmostEqual(1,np.sum(abundanceTable[i]), delta=10e-4)
        for valForm, valTable in zip(formDict.values(),elemNrs):
            self.assertEqual(valForm,valTable)
        self.assertAlmostEqual(self.getDm(formula), dm)

    def getDm(self,formula):
        formDict=formula.getFormulaDict()
        periodicTable = formula.getPeriodicTable()
        dm = []
        for i,elem in enumerate(formDict.keys()):
            mono = periodicTable[elem][0]
            for isotope in periodicTable[elem]:
                if formDict[elem] != 0:
                    if isotope[0]-mono[0] != 0:
                        dm_i = isotope[1]-mono[1]
                        dm.append((dm_i/round(dm_i)*formDict[elem]*isotope[2],formDict[elem]*isotope[2]))
        dm =np.array(dm)
        return np.sum(dm[:, 0]) / np.sum(dm[:, 1])

    def test_calculate_abundances_fft(self):
        '''averagine ={'C': 4.9384, 'H': 7.7583, 'N': 1.3577, 'O': 1.4773, 'S': 0.0417}
        averaginine = {'C': 9.5, 'H': 11.75, 'N': 3.75, 'O': 7, 'P': 1}'''
        for i in range(20):
            #randNr = randint(10, 100)
            '''molFormulaDummy_RNA = MolecularFormula({key:int(round(val*randNr)) for key,val in averaginine.items()})
            molFormulaDummy_prot = MolecularFormula({key:int(round(val*randNr)) for key,val in averagine.items()})'''
            molFormulaDummy_i = MolecularFormula({'C': randint(5, 50), 'H': randint(10, 100),
                                                  'N': randint(1, 40), 'O': randint(1, 40),
                                                  'P': randint(0, 2), 'S': randint(0, 2)})
            #exactIsotopePattern = molFormulaDummy_i.calculateIsotopePattern(MIN_SUM)
            abundanceTable, elemNrs, _ = molFormulaDummy_i.makeFFTTables(molFormulaDummy_i.calculateMonoIsotopic())
            fastIsotopePattern = molFormulaDummy.calculateAbundancesFFT(abundanceTable, elemNrs)
            try:
                sumInt = np.sum(np.array(fastIsotopePattern)[:,1])
                self.assertAlmostEqual(1.0, sumInt, delta=0.004)
                self.assertTrue(sumInt < 1)
            except AssertionError:
                print(fastIsotopePattern)
                raise AssertionError(molFormulaDummy_i.getFormulaDict())


    def test_calculate_isotope_pattern_fft(self):
        #print(key for key in {'S'} in {'C','S','H'})
        #print(MolecularFormula('S').calculateIsotopePatternFFT(0.996,10))
        #return
        for i in range(10):
            randNr = randint(30, 150)
            molFormulaDummy_RNA = MolecularFormula({key:int(round(val*randNr)) for key,val in averaginine.items()})
            molFormulaDummy_prot = MolecularFormula({key:int(round(val*randNr)) for key,val in averagine.items()})
            '''molFormulaDummy_both = MolecularFormula({'C': randint(100, 1000), 'H': randint(200, 2000),
                                                  'N': randint(50, 400), 'O': randint(50, 400),
                                                  'P': randint(0, 20), 'S': randint(0, 20)})'''
            for j,molFormulaDummy_i in enumerate([molFormulaDummy_RNA, molFormulaDummy_prot]):#, molFormulaDummy_both]:
                exactIsotopePattern = molFormulaDummy_i.calculateIsotopePattern(MIN_SUM)
                fastIsotopePattern = molFormulaDummy_i.calculateIsotopePatternFFT(MIN_SUM, 1)
                '''print(molFormulaDummy_i)
                print(exactIsotopePattern)
                print(fastIsotopePattern)'''
                try:
                    max_ppm = 1
                    if exactIsotopePattern['m/z'][0]>10000:
                        print('hey',randNr, exactIsotopePattern['m/z'][0])
                        max_ppm = 0.6
                    print(j%2,'max error', molFormulaDummy_i.toString(),
                          self.testIsotopePattern(exactIsotopePattern,fastIsotopePattern,max_ppm=max_ppm, deltaCalcInt=1*10e-4))
                except AssertionError as e:
                    print(molFormulaDummy_i.toString())
                    print(exactIsotopePattern,fastIsotopePattern)
                    raise e
        print('RRE2 / calmodulin')
        molFormulaDummy_RNA = MolecularFormula('C630H778N255O459P65') #rre2
        molFormulaDummy_prot = MolecularFormula('C714H1120N188O255S9') #calmodulin
        for j,molFormulaDummy_i in enumerate([molFormulaDummy_RNA, molFormulaDummy_prot]):#, molFormulaDummy_both]:
            exactIsotopePattern = molFormulaDummy_i.calculateIsotopePattern(MIN_SUM)
            fastIsotopePattern = molFormulaDummy_i.calculateIsotopePatternFFT(MIN_SUM, 1)
            print(j%2,'max error', molFormulaDummy_i.toString(),
                  self.testIsotopePattern(exactIsotopePattern,fastIsotopePattern,max_ppm=0.6, deltaCalcInt=1*10e-4))



    def test_calc_isotope_pattern_slowly(self):
        length = 2
        isotopePattern = RNA_formulaDummy.calcIsotopePatternPart(length)
        self.assertEqual(length,len(isotopePattern))
        self.testIsotopePattern(RNA_pattern[:length], isotopePattern, False)

    def testX(self):
        molFormulaDummy_prot = MolecularFormula('C714H1120N188O255S9') #calmodulin
        charge = 4
        h_formula = MolecularFormula({'H':4})
        molFormulaDummy_prot2 = molFormulaDummy_prot.addFormula(h_formula.getFormulaDict())
        '''abTable = []
        for row in molFormulaDummy_prot.calculateIsotopePattern(0.99)
            abTable.append((int(row[0],row[1])))'''
        #abTable = molFormulaDummy_prot.calculateIsotopePattern(0.99).astype(np.dtype([('m/z', int), ('calcInt', float)]))
        #print(abTable)
        neutralPattern = molFormulaDummy_prot.calculateIsotopePattern(0.99)
        print(neutralPattern)
        maxIso = int(np.max(neutralPattern['m/z']))
        minIso = int(np.min(neutralPattern['m/z']))
        abTable = np.zeros((2,maxIso+5))
        for i in range(len(neutralPattern)):
            abTable[0][minIso+i] = neutralPattern[i]['calcInt']
        for isotope in PeriodicTableService().get('H').getItems():
            abTable[1][isotope[0]] = isotope[2]
        print(molFormulaDummy_prot.calculateAbundancesFFT(abTable,np.array([1,charge])))
        print(molFormulaDummy_prot2.calculateIsotopePattern(0.99))
    '''def test_get_poisson_table(self):
        formula = MolecularFormula('C1000H1000N550O300S10')
        print(formula.makeIsotopeTable())
        print(formula.makePoissonTable())

    def test_calculate_poisson_isotope_pattern(self):
        formula = MolecularFormula('C100H100N55O30S1')
        print(formula.makePoissonTable())
        print(formula.calculatePoissonIsotopePattern(5))'''



