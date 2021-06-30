from unittest import TestCase

from src.Exceptions import InvalidInputException
from src.Services import *
from src.entities.GeneralEntities import Element


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
        self.fail()

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
            print(dummy)
            with self.assertRaises(InvalidInputException):
                self.service.checkFormatOfItems(dummy,knownElements,numericals)

    def test_check_name(self):
        self.service.checkName('Arg')
        for name in ['arg','Arg1','A1rg','1Arg','ARg','ArG', 'Ar_g']:
            with self.assertRaises(InvalidInputException):
                self.service.checkName(name)

class TestSequenceService(TestCase):
    def test_save(self):
        self.fail()

    def test_check_format_of_item(self):
        self.fail()


class TestFragmentationService(TestCase):

    def test_save(self):
        self.fail()

    def test_check_format_of_item(self):
        service = PeriodicTableService()

    def test_check_format_of_items(self):
        self.fail()


    def test_check_name(self):
        self.fail()

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