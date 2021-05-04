from unittest import TestCase
import numpy as np

from src.MolecularFormula import MolecularFormula

molFormulaDummy = MolecularFormula('C5H4N3O')
RNA_FormulaDummy = MolecularFormula('C38H48N15O26P3') #GCAU
print(RNA_FormulaDummy.getFormulaDict())
Peptide_ProtFormulaDummy = MolecularFormula('C36H56N12O14S')  #GCASDQHPV
print(Peptide_ProtFormulaDummy.getFormulaDict())

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
        if isotopeTable != None:
            self.assertEqual(len(isotopeTable), 9)
            self.assertEqual(len(isotopeTable[0]), 6)
            print(isotopeTable)
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

    def test_calculate_mono_isotopic(self):
        self.assertAlmostEqual(1223.210776,RNA_FormulaDummy.calculateMonoIsotopic(), delta=5*10**(-6))
        self.assertAlmostEqual(912.375965,Peptide_ProtFormulaDummy.calculateMonoIsotopic(), delta=5*10**(-6))

    def test_calculate_isotope_pattern(self):
        #RNA_pattern = np.array()
        #RNA_FormulaDummy.calculateIsotopePattern()
        peptide_pattern = [(912.375965, 0.592912), (913.379156, 0.270249), (914.382294, 0.103321),
                           (915.375239, 0.028104), (916.378483, 0.005413)]
        peptide_pattern = np.array(peptide_pattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])
        self.testIsotopePattern(peptide_pattern, Peptide_ProtFormulaDummy.calculateIsotopePattern())


    def testIsotopePattern(self, theoIsotopePattern=None, calcIsotopePattern=None):
        if theoIsotopePattern != None:
            self.assertEqual(len(theoIsotopePattern), len(calcIsotopePattern))
            for i in range(len(theoIsotopePattern)):
                self.assertAlmostEqual(theoIsotopePattern[i]['m/z'], calcIsotopePattern[i]['m/z'], delta=5*10**(-6))
                self.assertAlmostEqual(theoIsotopePattern[i]['calcInt'], calcIsotopePattern[i]['calcInt'], delta=5*10**(-6))

    def test_calc_isotope_pattern_slowly(self):
        self.fail()
