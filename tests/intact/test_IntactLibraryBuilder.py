from unittest import TestCase

from src.Services import SequenceService
from src.intact.IntactLibraryBuilder import IntactLibraryBuilder
from tests.top_down.test_LibraryBuilder import initTestSequences

def initSequences():
    initTestSequences(SequenceService())

class TestIntactLibraryBuilder(TestCase):
    def setUp(self):
        try:
            self.initLibrary()
        except:
            initSequences()
            self.initLibrary()

    def initLibrary(self):
        self.builderRNA = IntactLibraryBuilder('dummyRNA', '-')
        self.builderRNA_CMCT = IntactLibraryBuilder('dummyRNA', 'CMCT')
        self.builderProt = IntactLibraryBuilder('dummyProt', '-')


    """def test_create_library(self):
        self.fail()"""

    def test_get_unmodified_formula(self):
        theoFormula = {'C': 38, 'H':48, 'N':15, 'O':26, 'P':3}
        for key,val in self.builderRNA.getUnmodifiedFormula().getFormulaDict().items():
            self.assertEqual(theoFormula[key],val)
        for key,val in self.builderRNA_CMCT.getUnmodifiedFormula().getFormulaDict().items():
            self.assertEqual(theoFormula[key],val)
        theoFormula = {'C': 16, 'H':24, 'N':6, 'O':5}
        for key,val in self.builderProt.getUnmodifiedFormula().getFormulaDict().items():
            self.assertEqual(theoFormula[key],val)
