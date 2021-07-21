from random import randint
from unittest import TestCase
import numpy as np
import math

import src.fastFunctions as f
from scipy.stats import binom, multinomial, poisson
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
                     dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64), ('relAb', np.float64),
                            ('mass', np.float64), ('M+', np.float64)])
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
                self.assertAlmostEqual(index_0_theo[i][j], val)
        for i, row in enumerate(f.getByIndex(uni_table, 2)):
            for j, val in enumerate(row):
                self.assertAlmostEqual(index_2_theo[i][j], val)
        for i in range(50):
            isotopeTable = MolecularFormula({'C': randint(0, 50), 'H': randint(0, 100), 'N': randint(0, 30),
                                             'O': randint(0, 30), 'K': randint(0, 5)}).makeIsotopeTable()
            for j in range(int(np.max(isotopeTable['index'])) + 1):
                if j not in isotopeTable['index']:
                    print('Problem:', isotopeTable)
                    raise Exception(str(j) + ' not found')

    def test_log_fact(self):
        self.assertAlmostEqual(math.exp(f.logFact(15)), math.factorial(15), delta=0.01)
        self.assertAlmostEqual(math.exp(f.logFact(50) - f.logFact(45)), math.factorial(50) / math.factorial(45),
                               delta=0.01)

    def test_binomial(self):
        k, n, p = 2, 50, 1.078000e-02
        self.assertAlmostEqual(binom.pmf(k, n, p), f.binomial(k, n, p))

    def test_multinomial(self):
        oxygen = f.getByIndex(uni_table, 4)
        k = np.array([23, 2, 1])
        p = oxygen['relAb']
        n = int(np.sum(k))
        self.assertAlmostEqual(multinomial.pmf(k, n, p), f.multinomial(k, n, p))

    def test_calculate_percentage(self):
        mass_theo = 5 * 12 + 3 * 1.00782503 + 2 * 2.01410178 + 3 * 14.003074 + 2 * 15.0001089 + 22.98976928 + 16.99913176 + 17.99915961
        abundance_theo = binom.pmf(0, 5, 1.078000e-02) * binom.pmf(2, 5, 1.157000e-04) * binom.pmf(2, 5,
                                                                                                   3.642000e-03) * 1 * \
                         multinomial.pmf([0, 1, 1], 2, [9.975716e-01, 3.810000e-04, 2.051400e-03])
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
        for i, nr in enumerate([1, 4, 10, 19]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculateNuclFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))
        nrs = [1, 4, 11, 24]
        for i in range(20):
            molFormulaDummy_i = MolecularFormula({'C': randint(3, 50), 'H': randint(3, 150), 'N': randint(3, 50),
                                                  'O': randint(3, 50), 'P': randint(0, 10)})
            isotopeTable = molFormulaDummy_i.makeNucIsotopeTable()
            try:
                for isoPeak, nr in enumerate(nrs):
                    f.setIsotopeTable(isotopeTable)
                    self.assertEqual(nr, len(f.calculateNuclFineStructure(isoPeak, isotopeTable)))
            except AssertionError:
                raise AssertionError(molFormulaDummy_i.getFormulaDict())

    def test_get_max_values(self):
        table1 = MolecularFormula('C5H5N5OP').makeNucIsotopeTable()
        for correct, val in zip([3, 3, 3, 3, 3, 3, 1, 1, 1, 1], f.getMaxValues(3, table1)):
            self.assertEqual(correct, val)
        table2 = MolecularFormula('C14H27N5O5S').makeProteinIsotopeTable()
        for correct, val in zip([1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0], f.getMaxValues(1, table2)):
            self.assertEqual(correct, val)

    def test_calculate_pept_fine_structure(self):
        isotopeTable = MolecularFormula('C36H56N12O14S').makeProteinIsotopeTable()  # GCASDQHPV
        for i, nr in enumerate([1, 5, 16, 39]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculatePeptFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))
        nrs = [1, 5, 17, 45]
        for i in range(20):
            molFormulaDummy_i = MolecularFormula({'C': randint(3, 50), 'H': randint(3, 100), 'N': randint(3, 30),
                                                  'O': randint(3, 30), 'S': randint(3, 5)})
            isotopeTable = molFormulaDummy_i.makeProteinIsotopeTable()
            try:
                for isoPeak, nr in enumerate(nrs):
                    f.setIsotopeTable(isotopeTable)
                    self.assertEqual(nr, len(f.calculatePeptFineStructure(isoPeak, isotopeTable)))
            except AssertionError:
                raise AssertionError(molFormulaDummy_i.getFormulaDict())

        isotopeTable = MolecularFormula({'C': 4, 'H': 36, 'N': 41, 'O': 19, 'S': 1}).makeProteinIsotopeTable()
        sumInt = 0
        for i, nr in enumerate([1, 5, 16, 39]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculatePeptFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))
            sumInt += np.sum(np.array(fineStructure)[:, 1])
            print(np.sum(np.array(fineStructure)[:, 1]))
        print(sumInt)

    def test_set_isotope_table(self):
        newTable = f.setIsotopeTable(uni_table)
        for i in [3, 5, 8, 9]:
            self.assertAlmostEqual(0, newTable['nrIso'][i])

    def test_calculate_fine_structure(self):
        isotopeTable = MolecularFormula('C5H5N5OP').makeIsotopeTable()
        for i, nr in enumerate([1, 4, 10, 19]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculateFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))

        isotopeTable = MolecularFormula('C36H56N12O14S').makeIsotopeTable()  # GCASDQHPV
        for i, nr in enumerate([1, 5, 16, 39]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculateFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))
        isotopeTable = MolecularFormula('C5H5N5ONa').makeIsotopeTable()
        for i, nr in enumerate([1, 4, 10, 19]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculateFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))
        nrs = [1, 5, 17, 45]
        for i in range(20):
            molFormulaDummy_i = MolecularFormula({'C': randint(3, 50), 'H': randint(3, 100), 'N': randint(3, 30),
                                                  'O': randint(3, 30), 'K': randint(3, 5)})
            isotopeTable = molFormulaDummy_i.makeIsotopeTable()
            try:
                for isoPeak, nr in enumerate(nrs):
                    f.setIsotopeTable(isotopeTable)
                    self.assertEqual(nr, len(f.calculateFineStructure(isoPeak, isotopeTable)))
            except AssertionError:
                raise AssertionError(molFormulaDummy_i.getFormulaDict())

        nrs = [1, 5, 17, 45, 103]
        for i in range(20):
            molFormulaDummy_i = MolecularFormula({'C': randint(20, 50), 'H': randint(40, 100), 'N': randint(4, 40),
                                                  'O': randint(4, 40), 'P': randint(0, 5), 'S': randint(4, 5)})
            isotopeTable = molFormulaDummy_i.makeIsotopeTable()
            try:
                for isoPeak, nr in enumerate(nrs):
                    f.setIsotopeTable(isotopeTable)
                    self.assertEqual(nr, len(f.calculateFineStructure(isoPeak, isotopeTable)))
            except AssertionError:
                print(isoPeak)
                raise AssertionError(molFormulaDummy_i.getFormulaDict())
        isotopeTable = MolecularFormula({'C': 4, 'H': 36, 'N': 41, 'O': 19, 'S': 1}).makeIsotopeTable()
        sumInt = 0
        for i, nr in enumerate([1, 5, 16, 39]):
            f.setIsotopeTable(isotopeTable)
            fineStructure = f.calculateFineStructure(i, isotopeTable)
            self.assertEqual(nr, len(fineStructure))
            sumInt += np.sum(np.array(fineStructure)[:, 1])
            print(np.sum(np.array(fineStructure)[:, 1]))
        print(sumInt)

    def test_loop_through_isotopes(self):
        isotopeTable = MolecularFormula('C5H5N5OP').makeIsotopeTable()
        self.assertEqual(2, len(f.loopThroughIsotopes(0, isotopeTable, [(0., 0.)], 0)))

    def test_fact(self):
        self.assertEqual(math.factorial(10), f.fact(10))

    '''def test_calculate_poisson_percentage(self):
        poissonElement = np.array((100,1.2,1.01),
                                  dtype=[('nr', float),('lambda',float), ('mass',float)])
        self.assertAlmostEqual(poisson.pmf(6,poissonElement['lambda']),f.calculatePoissonPercentage(poissonElement, 6)[1])'''


    def test_calculate_fftfine_structure(self):
        np.set_printoptions(suppress=True)
        formula = MolecularFormula('C100H100N55O30S1')
        abundanceTable, elemNrs = formula.makeFFTTable(formula.calculateMonoIsotopic())
        normArr = formula.calculateIsotopePattern()
        normArr['calcInt'] /= np.sum(normArr['calcInt'])
        fftArr = f.calculateFFTFineStructure(abundanceTable, massTable, elemNrs)[:len(normArr)]
        fftArr[:,1] /= np.sum(fftArr[:,1])
        print()
        for fft, norm in zip(fftArr,normArr):
            print(fft,'\t',norm, '\t', fft[1]/norm['calcInt'], '\t', fft[1]/norm['calcInt'])
        print()
