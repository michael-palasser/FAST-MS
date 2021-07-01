from copy import deepcopy
from unittest import TestCase

from src.Exceptions import InvalidInputException
from src.Services import *
from src.entities.GeneralEntities import Element, Sequence


class TestPeriodicTableService(TestCase):
    def setUp(self):
        self.service = PeriodicTableService()

    def test_check_format_of_item(self):
        numericals = (0,1,2)
        self.service.checkFormatOfItem((1,100,0.5),numericals)
        for item in [(1, '',0.5), (1,100,'-'), ('',100,0.5),(-1,100,0.5)]:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item, numericals)

    def test_save_and_delete(self):
        name = 'Xeo'
        assert name not in self.service.getAllPatternNames()
        pattern = Element(name,[(15,10.,0.5),(16,10.,0.3),(17,10.,0.2)],None)
        self.service.save(pattern)
        savedPattern = self.service.get(pattern.getName())
        self.assertEqual(name,savedPattern.getName())
        self.assertEqual(pattern.getItems(),savedPattern.getItems())
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())
        with self.assertRaises(InvalidInputException):
            pattern = Element('h',[(15,10.,0.5),(16,10.,0.3),(17,10.,0.2)],None)
            self.service.save(pattern)
            pattern = Element(name,[(1,100,0.5),(2,100,0.4)],None)
            self.service.save(pattern)

    def test_check_name(self):
        self.service.checkName('He')
        for name in ['h','HE', '1H', 'H1', 'H1g','','H_g']:
            with self.assertRaises(InvalidInputException):
                self.service.checkName(name)

    def test_check_format_of_items(self):
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([])
        knownElements = self.service.getAllPatternNames()
        numericals = (0,1,2)
        self.service.checkFormatOfItems([(1,100,0.5),(2,100,0.49)],knownElements,numericals)
        dummies = [[(1,100,0.5),(2,100,0.4)],
                   [(1,100,0.5),(2,100.1,0.51)],
                   [(1,100,0.5),(1,100,0.51)],
                   [(1.1,100,0.5),(2,100,0.49)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,numericals)


class TestMoleculeService(TestCase):
    def setUp(self):
        self.service = MoleculeService()

    def test_save(self):
        name = 'Xeo'
        assert name not in self.service.getAllPatternNames()
        pattern = Macromolecule(name,'','-',[('Gm', 'CH5N2O', '', ''),('Am', 'C13H5N2OP', '', '')],None)
        self.service.save(pattern)
        savedPattern = self.service.get(pattern.getName())
        self.assertEqual(name,savedPattern.getName())
        self.assertEqual(pattern.getItems(),savedPattern.getItems())
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())
        with self.assertRaises(InvalidInputException):
            pattern = Macromolecule(name, '', '-', [('gm', 'CH5N2O', '', ''), ('Am', 'C13H5N2OP', '', '')], None)
            self.service.save(pattern)
            pattern = Macromolecule(name, '', '-', [('Gm', 'CH5N2Ox', '', ''), ('Am', 'C13H5N2OP', '', '')], None)
            self.service.save(pattern)


    def test_check_format_of_item(self):
        self.service.checkFormatOfItem(('Gm','CH5N2O','',''),())
        for item in [('','CH5N2O','',''),('-','CH5N2O','',''),('Gm','-','',''),('Gm','','','')]:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item,())

    def test_check_format_of_items(self):
        knownElements = ('C','H','N','O','P','S')
        numericals = ()
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([],knownElements,numericals)

        self.service.checkFormatOfItems([('Gm', 'CH5N2O', '', ''),('Am', 'C13H5N2OP', '', '')],knownElements,numericals)
        dummies = [[('Gm', 'CH5N2O', '', ''),('Gm', 'CH5N2Ox', '', '')],
                   [('Gm', 'CH5N2O', '', ''),('Gm', 'CH5N2O', '', '')],
                   [('Gm', 'CH5N2O', '', ''),('Gn', 'sCH5N2O', '', '')]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,numericals)

    def test_check_name(self):
        self.service.checkName('Arg')
        for name in ['arg','Arg1','A1rg','1Arg','ARg','ArG', 'Ar_g']:
            with self.assertRaises(InvalidInputException):
                self.service.checkName(name)


class TestSequenceService(TestCase):
    def setUp(self):
        self.service = SequenceService()

    def test_save(self):
        name = 'dummy'
        assert name not in self.service.getAllSequenceNames()
        oldSequences = [(tup[0], tup[1], tup[2]) for tup in self.service.getSequences()]
        sequences = deepcopy(oldSequences)
        dummy = (name, 'GACU', 'RNA')
        sequences.append(dummy)
        self.service.save(sequences)
        savedSequence = self.service.get(name)
        self.assertEqual(name, savedSequence.getName())
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllSequenceNames())
        self.service.save(sequences)
        sequences = deepcopy(oldSequences)
        sequences.append(('dummy1', 'GACUH', 'RNA'))
        with self.assertRaises(InvalidInputException):
            self.service.save(sequences)
        self.assertEqual(len(oldSequences), len(self.service.getAllSequenceNames()))
        self.assertNotIn('dummy1', self.service.getAllSequenceNames())
        sequences = deepcopy(oldSequences)
        sequences.append(('dummy1', 'GACU', 'RNA'))
        sequences.append(('dummy1', 'GACU', 'RNA'))
        with self.assertRaises(InvalidInputException):
            self.service.save(sequences)
        self.assertEqual(len(oldSequences), len(self.service.getAllSequenceNames()))
        self.assertNotIn('dummy1', self.service.getAllSequenceNames())

    def test_check_format_of_item(self):
        moleculeRepository = MoleculeRepository()
        molecules = moleculeRepository.getAllPatternNames()
        bbs = {}
        for molecule in molecules:
            bbs[molecule] = [bb[0] for bb in moleculeRepository.getPattern(molecule).getItems()]
        sequTup = ('dummy1','GACU','RNA')
        self.service.checkFormatOfItem(sequTup, bbs)
        sequTup = ('dummy2','GAHP','Protein')
        self.service.checkFormatOfItem(sequTup, bbs)
        dummies = [('dummy1', 'GACUH', 'RNA'),
                   ('dummy4', '', 'RNA'),
                   ('dummy5', '-', 'RNA'),
                   ('dummy+6', '-', 'RNA'),
                   ('dummy7', 'gGACU', 'RNA'),
                   ('dummy8', 'GACU', ''),
                   ('dummy9', 'GACU', '-'),
                   ('dummy10', 'GACU', 'rRNA'),
                   ('', 'GACU', 'RNA'),
                   ('-', 'GACU', 'RNA'),]
        for sequTup in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(sequTup, bbs)


class TestFragmentationService(TestCase):
    def setUp(self):
        self.service = FragmentationService()

    def test_save(self):
        name = 'dummy'
        assert name not in self.service.getAllPatternNames()
        pattern = FragmentationPattern(name,'Prec',[('a','C5','CH5N2O','-',0,1,1),('y-G','-','CH5N2O','G',0,-1,0)],
                                       [('Prec','-','-','-',0,1),('Prec-G','C5','-','-',0,0)],None)
        self.service.save(pattern)
        savedPattern = self.service.get(pattern.getName())
        with self.assertRaises(InvalidInputException):
            self.service.save(pattern)
        self.assertEqual(name,savedPattern.getName())
        self.assertEqual(pattern.getItems(),savedPattern.getItems())
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())
        dummies = [FragmentationPattern(name, 'Prec',
                                           [('a', 'C5', 'CH5N2O', '-', 0, 1, 1), ('y-G', '-', 'CH5N2O', 'G', 0, -1, 0)],
                                           [('Prec', '-', '-', '-', 0, 1), ('Prec', 'C5', '-', '-', 0, 0)], None),
                   FragmentationPattern(name, 'Prec',[('a', 'Cx5', 'CH5N2O', '-', 0, 1, 1)],
                                        [('Prec', '-', '-', '-', 0, 1)], None),
                   FragmentationPattern(name, 'Prec', [('a', 'C5', 'CH5N2O', '-', 0, 2, 1)],
                                        [('Prec', '-', '-', '-', 0, 1)], None),
                   FragmentationPattern(name, 'Prec-G', [('a', 'C5', 'CH5N2O', '-', 0, 2, 1)],
                                        [('Prec', '-', '-', '-', 0, 1)], None)
                   ]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.save(dummy)

    def test_check_format_of_item(self):
        self.service.checkFormatOfItem(('a','','CH5N2O','-',0,1,1),(4,5,6))
        self.service.checkFormatOfItem(('y-G','-','CH5N2O','G',0,-1,1),(4,5,6))
        self.service.checkFormatOfItem(('y_G','-','CH5N2O','G',0,-1,1),(4,5,6))
        for item in [('','','CH5N2O','G',0,1,1), ('-','','CH5N2O','G',0,1,1),('a','','CH5N2O','G','x',1,1),
                     ('a','','CH5N2O','G',0,'x',1),('a','','CH5N2O','G',0,'-',1)]:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item,(4,5))

    def test_check_format_of_items(self):
        knownElements = ('C','H','N','O','P','S')
        numericals = (4,5)
        numericalsPrec = (4,)
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([],knownElements,numericals)
        self.service.checkFormatOfItems([('a','C5','CH5N2O','-',0,1,1),('y-G','-','CH5N2O','G',0,-1,0)],knownElements,numericals)
        dummies = [[('a','C5','CH5N2O','-',0,1,1),('a','C5','CH5N2O','-',0,1,1)],
                   [('a','Cx5','CH5N2O','-',0,1,1)],
                   [('a','C5','CH5N2O','-',0,'',1)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,numericals)
        self.service.checkFormatOfItems([('Prec','C5','CH5N2O','-',0,1),('Prec-G','C5','CH5N2O','-',0,0)],
                                        knownElements,numericalsPrec)
        dummies = [[('Prec','C5','CH5N2O','-',0,1),('Prec','C5','CH5N2O','-',0,1)],
                   [('Prec','Cx5','CH5N2O','-',0,1)],
                   [('Prec','C5','CH5N2O','-',0,'')]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,numericalsPrec)



class TestModificationService(TestCase):
    def test_save(self):
        self.fail()

    def test_check_format_of_item(self):
        service = PeriodicTableService()

    def test_check_format_of_items(self):
        self.fail()

    def test_check_name(self):
        self.fail()

class TestIntactIonService(TestCase):

    def test_save(self):
        self.fail()

    def test_check_format_of_item(self):
        service = PeriodicTableService()


    def test_check_format_of_items(self):
        self.fail()

    def test_check_name(self):
        self.fail()