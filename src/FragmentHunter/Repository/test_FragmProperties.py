from unittest import TestCase
import os

from src.FragmentHunter.Repository.FragmProperties import *

pattern1 = FragmentationPattern("CAD_CMCT", "CMCT",
                                [FragItem("a", 1, "", "H1O3P1", "", 0), FragItem("c", 1, "", "", "", 0)],
                                [ModifiedItem("CMCT", 1, "C14H25N3O","","",0,0.5)], [])
pattern2 = FragmentationPattern("CAD_CMCT", "CMCT",
                                [FragItem("a", 0, "", "H1O3P1", "", 0), FragItem("c", 1, "", "", "", 0)],
                                [ModifiedItem("CMCT", 1, "C14H25N3O","","",0,0.5)], [])

pattern3 = FragmentationPattern("CAD_NMIA", "NMIA",
                                [FragItem("a", 1, "", "H1O3P1", "", 0), FragItem("c", 1, "", "", "", 0)],
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
        self.repository.createFragPattern(pattern1)
        self.repository.createFragPattern(pattern3)

    def test_createPattern(self):
        self.createPatternForTest()
        self.assertEqual(self.repository.getFragPattern("CAD_CMCT").name, pattern1.name)

    def test_createItem(self):
        self.createPatternForTest()
        for item, readItem in zip(self.repository.getFragPattern("CAD_CMCT").fragmentTypes, pattern1.fragmentTypes):
            self.assertEqual(item.getAll(),readItem.getAll())
        self.repository.close()

    def test_createModItem(self):
        self.createPatternForTest()
        for item, readItem in zip(self.repository.getFragPattern("CAD_CMCT").listOfMod, pattern1.listOfMod, ):
            self.assertEqual(item.getAll(),readItem.getAll())
        self.repository.close()

    def test_get_pattern(self):
        self.setUp()
        self.assertEqual(self.repository.getFragPattern("CAD_CMCT").name, pattern1.name)

    def test_get_items(self):
        for item, readItem in zip(self.repository.getFragPattern("CAD_CMCT").fragmentTypes, pattern1.fragmentTypes):
            self.assertEqual(item.getAll(),readItem.getAll())

    def test_get_mod_items(self):
        for item, readItem in zip(self.repository.getFragPattern("CAD_CMCT").listOfMod, pattern1.listOfMod, ):
            self.assertEqual(item.getAll(),readItem.getAll())


    def test_updatePattern(self):
        self.createPatternForTest()
        self.repository.updateModPattern(pattern2)
        for item, readItem in zip(self.repository.getFragPattern(pattern2.name).fragmentTypes, pattern2.fragmentTypes):
            self.assertEqual(item.getAll(),readItem.getAll())

    def test_deletePattern(self):
        self.createPatternForTest()
        self.repository.getFragPattern("CAD_CMCT")
        self.repository.deleteModPattern(pattern1)
        #self.Repository.getModPattern("CAD_CMCT")
        with self.assertRaises(IndexError):
            self.repository.getFragPattern("CAD_CMCT")



