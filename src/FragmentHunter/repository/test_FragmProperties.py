from unittest import TestCase
import os

from src.FragmentHunter.repository.FragmProperties import *

pattern1 = FragmentationPattern("CAD_CMCT", "CMCT",
                                [Item("a",1,"","H1O3P1","",0), Item("c",1,"","","",0)],
                                [ModifiedItem("CMCT", 1, "C14H25N3O","","",0,0.5)], [])
pattern2 = FragmentationPattern("CAD_CMCT", "CMCT",
                                [Item("a",0,"","H1O3P1","",0), Item("c",1,"","","",0)],
                                [ModifiedItem("CMCT", 1, "C14H25N3O","","",0,0.5)], [])

pattern3 = FragmentationPattern("CAD_NMIA", "NMIA",
                                [Item("a",1,"","H1O3P1","",0), Item("c",1,"","","",0)],
                                [ModifiedItem("NMIA", 1, "C5H10N3O","","",0,0.5)], [])


class TestFragmentationRepository(TestCase):
    def setUp(self):
        self.file = "Fragmentation_test.db"
        self.repository = FragmentationRepository(self.file)

    def makeTables(self):
        self.setUp()
        if os.path.isfile(self.file):
            os.remove(self.file)
        self.repository = FragmentationRepository(self.file)
        self.repository.makeTables()

    def createPatternForTest(self):
        self.makeTables()
        self.repository.createPattern(pattern1)
        self.repository.createPattern(pattern3)

    def test_createPattern(self):
        self.createPatternForTest()
        self.assertEqual(self.repository.getPattern("CAD_CMCT").name, pattern1.name)

    def test_createItem(self):
        self.createPatternForTest()
        for item, readItem in zip(self.repository.getPattern("CAD_CMCT").listOfUnmod, pattern1.listOfUnmod):
            self.assertEqual(item.getAll(),readItem.getAll())
        self.repository.close()

    def test_createModItem(self):
        self.createPatternForTest()
        for item, readItem in zip(self.repository.getPattern("CAD_CMCT").listOfMod, pattern1.listOfMod, ):
            self.assertEqual(item.getAll(),readItem.getAll())
        self.repository.close()

    def test_get_pattern(self):
        self.setUp()
        self.assertEqual(self.repository.getPattern("CAD_CMCT").name, pattern1.name)

    def test_get_items(self):
        for item, readItem in zip(self.repository.getPattern("CAD_CMCT").listOfUnmod, pattern1.listOfUnmod):
            self.assertEqual(item.getAll(),readItem.getAll())

    def test_get_mod_items(self):
        for item, readItem in zip(self.repository.getPattern("CAD_CMCT").listOfMod, pattern1.listOfMod, ):
            self.assertEqual(item.getAll(),readItem.getAll())


    def test_updatePattern(self):
        self.createPatternForTest()
        self.repository.updatePattern(pattern2)
        for item, readItem in zip(self.repository.getPattern(pattern2.name).listOfUnmod, pattern2.listOfUnmod):
            self.assertEqual(item.getAll(),readItem.getAll())

    def test_deletePattern(self):
        self.createPatternForTest()
        self.repository.getPattern("CAD_CMCT")
        self.repository.deletePattern(pattern1)
        #self.repository.getPattern("CAD_CMCT")
        with self.assertRaises(IndexError):
            self.repository.getPattern("CAD_CMCT")



