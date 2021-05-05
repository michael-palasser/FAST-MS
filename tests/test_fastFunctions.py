from unittest import TestCase
import numpy as np
import src.fastFunctions as f
from scipy.stats import binom, multinomial
import math
from src.MolecularFormula import MolecularFormula

'''G = stringToFormula('C5H5N5O',{},1)
uni_table = np.empty((5,6))
for i in
uni_table = np.array((0,5, 1,))'''

uni_table = np.array([(0., 5., 0., 9.893800e-01, 12., 0.),
                      (0., 5., 0., 1.078000e-02, 13.00335484, 1.),
                      (1., 5., 0., 9.998857e-01, 1.00782503, 0.),
                      (1., 5., 2., 1.157000e-04, 2.01410178, 1.),
                      (2., 5., 0., 9.963620e-01, 14.003074, 0.),
                      (2., 5., 2., 3.642000e-03, 15.0001089, 1.),
                      (3., 1., 0., 1.000000e+00, 22.98976928, 0.),
                      (4., 2., 0., 9.975716e-01, 15.99491462, 0.),
                      (4., 2., 1., 3.810000e-04, 16.99913176, 1.),
                      (4., 2., 1., 2.051400e-03, 17.99915961, 2.)],
                     dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),('relAb',np.float64),
                          ('mass',np.float64), ('M+',np.float64)])
'''nuc_table = np.array([(0., 5., 0., 9.893800e-01, 12., 0.),
                      (0., 5., 0., 1.078000e-02, 13.00335484, 1.),
                      (1., 5., 0., 9.998857e-01, 1.00782503, 0.),
                      (1., 5., 2., 1.157000e-04, 2.01410178, 1.),
                      (2., 5., 0., 9.963620e-01, 14.003074, 0.),
                      (2., 5., 2., 3.642000e-03, 15.0001089, 1.),
                      (3., 2., 0., 9.975716e-01, 15.99491462, 0.),
                      (3., 2., 1., 3.810000e-04, 16.99913176, 1.),
                      (3., 2., 1., 2.051400e-03, 17.99915961, 2.)],
                     dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),('relAb',np.float64),
                          ('mass',np.float64), ('M+',np.float64)])'''
'''table3 = np.array([(0., 5., 0., 9.893800e-01, 12., 0.),
                   (0., 5., 0., 1.078000e-02, 13.00335484, 1.),
                   (1., 5., 0., 9.998857e-01, 1.00782503, 0.),
                   (1., 5., 2., 1.157000e-04, 2.01410178, 1.),
                   (2., 5., 0., 9.963620e-01, 14.003074, 0.),
                   (2., 5., 2., 3.642000e-03, 15.0001089, 1.),
                   (3., 2., 0., 9.975716e-01, 15.99491462, 0.),
                   (3., 2., 1., 3.810000e-04, 16.99913176, 1.),
                   (3., 2., 1., 2.051400e-03, 17.99915961, 2.),
                   (4., 2., 0., 9.975716e-01, 15.99491462, 0.),
                   (4., 2., 1., 3.810000e-04, 16.99913176, 1.),
                   (4., 2., 1., 2.051400e-03, 17.99915961, 2.)],
                  dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),('relAb',np.float64),
                          ('mass',np.float64), ('M+',np.float64)])'''

class fastFunctions_Test(TestCase):

    def test_get_by_index(self):
        index_0_theo = np.array([(0., 5., 0., 9.893800e-01, 12., 0.), (0., 5., 0., 1.078000e-02, 13.00335484, 1.)])
        index_2_theo = np.array([(2., 5., 0., 9.963620e-01, 14.003074, 0.), (2., 5., 2., 3.642000e-03, 15.0001089, 1.)])
        for i, row in enumerate(f.getByIndex(uni_table, 0)):
            for j, val in enumerate(row):
                self.assertAlmostEqual(index_0_theo[i][j],val)
        for i, row in enumerate(f.getByIndex(uni_table, 2)):
            for j, val in enumerate(row):
                self.assertAlmostEqual(index_2_theo[i][j],val)

    def test_log_fact(self):
        self.assertAlmostEqual(math.exp(f.logFact(15)), math.factorial(15), delta=0.01)
        self.assertAlmostEqual(math.exp(f.logFact(50)-f.logFact(45)), math.factorial(50)/math.factorial(45), delta=0.01)

    def test_binomial(self):
        k,n,p= 2,50,1.078000e-02
        self.assertAlmostEqual(binom.pmf(k,n,p), f.binomial(k,n,p))

    def test_multinomial(self):
        oxygen = f.getByIndex(uni_table, 4)
        k=np.array([23,2,1])
        p = oxygen['relAb']
        n = int(np.sum(k))
        self.assertAlmostEqual(multinomial.pmf(k,n,p), f.multinomial(k,n,p))

    def test_calculate_percentage(self):
        mass_theo = 5*12+3*1.00782503+2*2.01410178+3*14.003074+2*15.0001089+22.98976928+16.99913176+17.99915961
        abundance_theo = binom.pmf(0,5,1.078000e-02)*binom.pmf(2,5,1.157000e-04)*binom.pmf(2,5,3.642000e-03)*1*\
                    multinomial.pmf([0,1,1],2,[9.975716e-01,3.810000e-04,2.051400e-03])
        mass_i, propI = f.calculatePercentage(uni_table)
        self.assertAlmostEqual(mass_theo, mass_i)
        self.assertAlmostEqual(abundance_theo, propI)

    '''uni_table = np.array([(0., 5., 5., 9.893800e-01, 12., 0.),
    (0., 5., 0., 1.078000e-02, 13.00335484, 1.),
    (1., 5., 3., 9.998857e-01, 1.00782503, 0.),
    (1., 5., 2., 1.157000e-04, 2.01410178, 1.),
    (2., 5., 3., 9.963620e-01, 14.003074, 0.),
    (2., 5., 2., 3.642000e-03, 15.0001089, 1.),
    (3., 1., 1., 1.000000e+00, 22.98976928, 0.),
    (4., 2., 0., 9.975716e-01, 15.99491462, 0.),
    (4., 2., 1., 3.810000e-04, 16.99913176, 1.),
    (4., 2., 1., 2.051400e-03, 17.99915961, 2.)],'''

    def test_calculate_nucl_fine_structure(self):
        isotopeTable = MolecularFormula('C5H5N5OP').makeNucIsotopeTable()
        #with more O: [1,4,11,58]
        for i, nr in enumerate([1,4,10,40]):
            fineStructure = f.calculateNuclFineStructure(i, isotopeTable)
            self.assertEqual(nr,len(fineStructure))

    def test_get_max_values(self):
        table1 = MolecularFormula('C5H5N5OP').makeNucIsotopeTable()
        for correct,val in zip([3, 3, 3, 3, 3, 3, 1, 1, 1, 1],f.getMaxValues(3, table1)):
            self.assertEqual(correct,val)
        table2 = MolecularFormula('C14H27N5O5S').makeProteinIsotopeTable()
        for correct,val in zip([1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],f.getMaxValues(1, table2)):
            self.assertEqual(correct,val)

    def test_calculate_pept_fine_structure(self):
        self.fail()

    def test_set_isotope_table(self):
        newTable = f.setIsotopeTable(uni_table)
        for i in [3,5,8,9]:
            self.assertAlmostEqual(0,newTable['nrIso'][i])

    def test_calculate_fine_structure(self):
        self.fail()

    def test_loop_through_isotopes(self):
        self.fail()
