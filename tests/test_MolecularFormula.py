from unittest import TestCase
import numpy as np
from random import randint
from src.fastFunctions import getByIndex

from src.MolecularFormula import MolecularFormula

molFormulaDummy = MolecularFormula('C5H4N3O')
RNA_formulaDummy = MolecularFormula('C38H48N15O26P3') #GCAU
peptideFormulaDummy = MolecularFormula('C36H56N12O14S')  #GCASDQHPV
uniFormulaDummy = MolecularFormula('C5H5N5ONa')

dict0= {'C':5,'H':4,'N':3, 'O':1}
dict1= {'C':5,'H':4,'N':3, 'O':1, 'S': 10}
dict2= {'C':10,'H':8,'N':6, 'O':2, 'S': 10}

class MolecularFormulaTest(TestCase):

    def test_init(self):
        self.assertEqual(dict0, molFormulaDummy.getFormulaDict())

    def test_add_formula(self):
        self.assertEqual(dict2, molFormulaDummy.addFormula(dict1).getFormulaDict())

    def test_subtract_formula(self):
        molFormula2 = MolecularFormula(dict1)
        self.assertEqual({'C':0,'H':0,'N':0, 'O':0, 'S': 10}, molFormula2.subtractFormula(dict0).getFormulaDict())

    def test_multiply_formula(self):
        self.assertEqual(dict2, molFormulaDummy.multiplyFormula(2).addFormula({'S':10}).getFormulaDict())

    def test_check_for_negative_values(self):
        self.assertTrue(molFormulaDummy.subtractFormula({'S':1}))

    '''def test_to_string(self):
        self.fail()'''


    def testIsotopeTable(self, isotopeTable = None, values = None):
        if type(isotopeTable) != type(None) :
            self.assertEqual(len(isotopeTable), 9)
            self.assertEqual(len(isotopeTable[0]), 6)
            for row in isotopeTable:
                self.assertAlmostEqual(0,row['nrIso'])
                self.assertAlmostEqual(values[int(row['index'])],row['nr'])

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
        self.assertEqual(2, len(getByIndex(isotopeTable,0)))

    def test_calculate_mono_isotopic(self):
        self.assertAlmostEqual(1223.210776, RNA_formulaDummy.calculateMonoIsotopic(), delta=5 * 10 ** (-6))
        self.assertAlmostEqual(912.375965, peptideFormulaDummy.calculateMonoIsotopic(), delta=5 * 10 ** (-6))

    def test_calculate_isotope_pattern(self):
        RNA_pattern = [(1223.2107777180972, 0.58545685),(1224.2134684, 0.28360589), (1225.21578726, 0.09861313),
                       (1226.21815597, 0.02558403), (1227.22044876, 0.00558521)]
        peptide_pattern = [(912.37596571, 0.59104661), (913.37869526, 0.26946771), (914.37874787, 0.1035717),
                           (915.37979107, 0.02834297), (916.38113847, 0.00624432)]
        uni_pattern = [(174.03917908, 0.92733003),(175.04099458,0.06836688),(176.04296025,0.00412072)]
        self.testIsotopePattern(RNA_pattern, RNA_formulaDummy.calculateIsotopePattern())
        print(peptideFormulaDummy.calculateIsotopePattern())
        self.testIsotopePattern(peptide_pattern, peptideFormulaDummy.calculateIsotopePattern())
        self.testIsotopePattern(uni_pattern, uniFormulaDummy.calculateIsotopePattern())
        for i in range(20):
            molFormulaDummy_i = MolecularFormula({'C':randint(1,50), 'H':randint(1,100),
                                                  'N':randint(1,50),'O':randint(1,50),
                                                  'P':randint(0,2),'S':randint(0,2)})
            print(molFormulaDummy_i.getFormulaDict())
            calcIsotopePattern = molFormulaDummy_i.calculateIsotopePattern()
            self.assertAlmostEqual(1.0,float(np.sum(calcIsotopePattern['calcInt'])),delta=0.005)
            self.assertTrue(np.sum(calcIsotopePattern['calcInt'])<1)


    def testIsotopePattern(self, theoIsotopePattern=None, calcIsotopePattern=None):
        if theoIsotopePattern != None:
            theoIsotopePattern = np.array(theoIsotopePattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])
            theoIsotopePattern['calcInt'] *= (calcIsotopePattern['calcInt'][0] /theoIsotopePattern['calcInt'][0])
            if len(theoIsotopePattern) > (len(calcIsotopePattern)+1):
                raise Exception('Length of calculated isotope pattern to short')
            for i in range(len(theoIsotopePattern)):
                self.assertAlmostEqual(theoIsotopePattern[i]['m/z'], calcIsotopePattern[i]['m/z'], delta=5*10**(-6))
                self.assertAlmostEqual(theoIsotopePattern[i]['calcInt'], calcIsotopePattern[i]['calcInt'], delta=5*10**(-6))
            self.assertAlmostEqual(1.0,float(np.sum(calcIsotopePattern['calcInt'])),delta=0.005)
            self.assertTrue(np.sum(calcIsotopePattern['calcInt'])<1)

    '''def test_calc_isotope_pattern_slowly(self):
        self.fail()'''
