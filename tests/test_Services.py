from copy import deepcopy
from unittest import TestCase

from src.services.DataServices import *
from src.entities.GeneralEntities import Element

knownElements = ('C', 'H', 'N', 'O', 'P', 'S')

class TestPeriodicTableService(TestCase):
    def setUp(self):
        self.service = PeriodicTableService()
        self.numericals = (0,1,2)

    def test_check_format_of_item(self):
        self.service.checkFormatOfItem((1,100,0.5),self.numericals)
        for item in [(1, '',0.5), (1,100,'-'), ('',100,0.5),(-1,100,0.5)]:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item, self.numericals)

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
        for name in ['h','HE', '1H', 'H1', 'H1g','']:
            with self.assertRaises(InvalidInputException):
                print(name)
                self.service.checkName(name)

    def test_check_format_of_items(self):
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([])
        knownElements = self.service.getAllPatternNames()
        self.service.checkFormatOfItems([(1,100,0.5),(2,100,0.49)],knownElements,self.numericals)
        dummies = [[(1,100,0.5),(2,100,0.4)],
                   [(1,100,0.5),(2,100.1,0.51)],
                   [(1,100,0.5),(1,100,0.5)],
                   [(1.1,100,0.5),(2,100,0.49)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                print(dummy)
                self.service.checkFormatOfItems(dummy,knownElements,self.numericals)


class TestMoleculeService(TestCase):
    def setUp(self):
        self.service = MoleculeService()
        self.numericals = ()

    def test_save(self):
        name = 'Xeo'
        if name in self.service.getAllPatternNames():
            self.service.delete('Xeo')
        assert name not in self.service.getAllPatternNames()
        pattern = Macromolecule(name,'','-',[('Gm', '', 'CH5N2O'),('Am', '', 'C13H5N2OP')],None)
        self.service.save(deepcopy(pattern))
        savedPattern = self.service.get(pattern.getName())
        self.assertEqual(name,savedPattern.getName())
        self.assertEqual(pattern.getItems(),[item[:3] for item in savedPattern.getItems()])
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())
        with self.assertRaises(InvalidInputException):
            pattern = Macromolecule(name, '', '-', [('gm', '', 'CH5N2O'), ('Am', '', 'C13H5N2OP')], None)
            self.service.save(pattern)
            pattern = Macromolecule(name, '', '-', [('Gm', '', 'CH5N2Ox'), ('Am', '', 'C13H5N2OP')], None)
            self.service.save(pattern)

        assert name not in self.service.getAllPatternNames()


    def test_check_format_of_item(self):
        self.service.checkFormatOfItem(('Gm',"",'CH5N2O'),())
        for item in [('','','CH5N2O'),('-','','CH5N2O'),('Gm','','-'),('Gm','','')]:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item,())

    def test_check_format_of_items(self):
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([],knownElements,self.numericals)

        self.service.checkFormatOfItems([('Gm', '', 'CH5N2O'),('Am', '', 'C13H5N2OP')],knownElements,
                                        self.numericals)
        dummies = [[('Gm', '', 'CH5N2O'),('Gm', '', 'CH5N2Ox')],
                   [('Gm', '', 'CH5N2O'),('Gm', '', 'CH5N2O')],
                   [('Gm', '', 'CH5N2O'),('Gn', '', 'sCH5N2O')]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,self.numericals)

    def test_check_name(self):
        self.service.checkName('Arg')
        for name in ['arg','1Arg','ARg','ArG']:
            print(name)
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
        self.numericals = (4,5)

    def test_save(self):
        name = 'dummy'
        if name in self.service.getAllPatternNames():
            self.service.delete(name)
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
                   FragmentationPattern(name, 'Prec-G', [('a', 'C5', 'CH5N2O', '-', 0, 1, 1)],
                                        [('Prec', '-', '-', '-', 0, 1)], None)
                   ]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.save(dummy)
            assert name not in self.service.getAllPatternNames()

    def test_check_format_of_item(self):
        dummies = [('a','','CH5N2O','-',0,1,1),('y-G','-','CH5N2O','G',0,-1,1),('y_G','-','CH5N2O','G',0,-1,1)]
        for dummy in dummies:
            self.service.checkFormatOfItem(dummy,self.numericals)
        dummies = [('','','CH5N2O','G',0,1,1), ('-','','CH5N2O','G',0,1,1),('a','','CH5N2O','G','x',1,1),
                     ('a','','CH5N2O','G',0,'x',1),('a','','CH5N2O','G',0,'-',1)]
        for item in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item,self.numericals)

    def test_check_format_of_items(self):
        numericalsPrec = (4,)
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([],knownElements,self.numericals)
        self.service.checkFormatOfItems([('a','C5','CH5N2O','-',0,1,1),('y-G','-','CH5N2O','G',0,-1,0)],knownElements,self.numericals)
        dummies = [[('a','C5','CH5N2O','-',0,1,1),('a','C5','CH5N2O','-',0,1,1)],
                   [('a','Cx5','CH5N2O','-',0,1,1)],
                   [('a','C5','CH5N2O','-',0,'',1)],
                   [('a','C5','cCH5N2O','0',0,1,1)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,self.numericals)
        self.service.checkFormatOfItems([('Prec','C5','CH5N2O','-',0,1),('Prec-G','C5','CH5N2O','-',0,0)],
                                        knownElements,numericalsPrec)
        dummies = [[('Prec','C5','CH5N2O','-',0,1),('Prec','C5','CH5N2O','-',0,1)],
                   [('Prec','Cx5','CH5N2O','-',0,1)],
                   [('Prec','C5','CH5N2O','-','x',1)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,numericalsPrec)



class TestModificationService(TestCase):
    def setUp(self):
        self.service = ModificationService()
        self.numericals = (4,5)

    def test_save(self):
        name = 'dummy'
        assert name not in self.service.getAllPatternNames()
        pattern = ModificationPattern(name,'+X',[('+X','CH5N2O','','-',0,0.4,1,1),('+X-y','CH5N2O','','-',0,-0.4,1,1)],
                                       [('+X-y-G',)],None)
        self.service.save(pattern)
        savedPattern = self.service.get(pattern.getName())
        with self.assertRaises(InvalidInputException):
            self.service.save(pattern)
        self.assertEqual(name,savedPattern.getName())
        self.assertEqual(pattern.getItems(),savedPattern.getItems())
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())

        pattern = ModificationPattern(name,'X',[('X','CH5N2O','','-',0,0.4,1,1)],[('+X-y-G',)],None)
        self.service.save(pattern)
        self.assertEqual('+X', self.service.get(pattern.getName()).getItems()[0][0])
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())

        dummies = [ModificationPattern(name,'X',[('+X','CH5N2O','','-',0,0.4,1,1),('+X','CH5N2O','','-',0,-0.4,1,1)],
                                       [('+X-y-G',)],None),
                   ModificationPattern(name, name, [('+X', 'CxH5N2O', '', '-', 0, 0.4, 1, 1),
                                                    ('+X-y', 'CH5N2O', '', '-', 0, -0.4, 1, 1)],[('+X-y-G',)], None)]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.save(dummy)
            assert name not in self.service.getAllPatternNames()

    def test_check_format_of_item(self):
        dummies = [('+X','CH5N2O','','-',0,0.4,1,1),('+X','CH5N2O','C','',0,-0.4,1,1),('+X','CH5N2O','C','',0,-0.4,1,0)]
        for dummy in dummies:
            self.service.checkFormatOfItem(dummy,self.numericals)
        dummies = [('','CH5N2O','','-',0,0.4,1,1),('+X','CH5N2O','C','','-',-0.4,1,1),('+X','CH5N2O','C','',0,'-',1,0)]
        for item in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItem(item,(4,5))

    def test_check_format_of_items(self):
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([],knownElements,self.numericals)
        self.service.checkFormatOfItems([('+X','CH5N2O','','-',0,0.4,1,1),('+X-y','CH5N2O','','-',0,-0.4,1,1)],
                                        knownElements,self.numericals)
        dummies = [[('+X','CH5N2O','','-',0,0.4,1,1),('+X','CH5N2O','','-',0,0.4,1,1)],
                   [('+X','CxH5N2O','','-',0,0.4,1,1)],
                   [('+X','cCH5N2O','','-',0,0.4,1,1)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,self.numericals)


class TestIntactIonService(TestCase):
    def setUp(self):
        self.service = IntactIonService()
        self.numericals = (3,)

    def test_save(self):
        name = 'dummy'
        assert name not in self.service.getAllPatternNames()
        pattern = IntactPattern(name,[('+X','CH5N2O','',1,0,1),('+X-y','CH5N2O','C',0,0,1)],None)
        self.service.save(pattern)
        savedPattern = self.service.get(pattern.getName())
        with self.assertRaises(InvalidInputException):
            self.service.save(pattern)
        self.assertEqual(name,savedPattern.getName())
        self.assertEqual(pattern.getItems(),savedPattern.getItems())
        self.service.delete(name)
        self.assertNotIn(name, self.service.getAllPatternNames())

        dummies = [IntactPattern(name,[('+X','CH5N2O','',1,0,1),('+X','CH5N2O','',1,0,1),('+X-y','CH5N2O','C',0,1)],None),
                   IntactPattern(name, [('+X','CxH5N2O','',1,0,1),('+X-y','CH5N2O','C',0,0,1)], None)]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.save(dummy)
            assert name not in self.service.getAllPatternNames()

    def test_check_format_of_item(self):
        dummies = [('+X','CH5N2O','',1,0,1),('+X','CH5N2O','C',0,0,1),('+X','CH5N2O','-',1,0,0)]
        for dummy in dummies:
            self.service.checkFormatOfItem(dummy,(3,))
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItem(('+X','CH5N2O','-','-',1),(3,))

    def test_check_format_of_items(self):
        with self.assertRaises(InvalidInputException):
            self.service.checkFormatOfItems([],knownElements,self.numericals)
        self.service.checkFormatOfItems([('+X','CH5N2O','',1,0,1),('+X-y','CH5N2O','C',0,0,1)],knownElements,self.numericals)
        dummies = [[('+X','CH5N2O','',1,0,1),('+X','CH5N2O','',1,0,1)],
                   [('+X','CxH5N2O','',1,0,1)],
                   [('+X','cCH5N2O','',1,0,1)]]
        for dummy in dummies:
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,self.numericals)
