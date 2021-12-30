import copy
from unittest import TestCase
from random import randint
import os

from src.resources import path
from src.Exceptions import InvalidIsotopePatternException
from src.MolecularFormula import MolecularFormula
from src.services.DataServices import SequenceService
from src.entities.GeneralEntities import Sequence
from src.entities.Ions import Fragment
from src.entities.SearchSettings import SearchSettings
from src.repositories.IsotopePatternRepository import IsotopePatternRepository
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder


class TestIsotopePatternRepository(TestCase):

    def setUp(self):
        try:
            self.initLibrary()
        except:
            sequences = [Sequence(tup[0], tup[1], tup[2], i) for i, tup in
                         enumerate(self.sequenceService.getSequences())]
            sequences.append(Sequence('dummyRNA', 'GACU', 'RNA', len(sequences) + 1))
            sequences.append(Sequence('dummyProt', 'GAPH', 'Protein', len(sequences) + 1))
            print(sequences)
            self.sequenceService.save(sequences)
            self.initLibrary()

    def initLibrary(self):
        self.sequenceService = SequenceService()
        propertyStorage = SearchSettings('dummyRNA', 'RNA_CAD', 'CMCT')
        self.builderRNA = FragmentLibraryBuilder(SearchSettings('dummyRNA', 'RNA_CAD', '-'), 0)
        self.builderRNA_CMCT0 = FragmentLibraryBuilder(propertyStorage,0)
        self.builderRNA_CMCT1 = FragmentLibraryBuilder(propertyStorage, 1)
        self.builderRNA_CMCT2 = FragmentLibraryBuilder(propertyStorage,2)
        self.builderProt_ECD = FragmentLibraryBuilder(SearchSettings('dummyProt', 'Protein_ECD', '-'), 0)
        self.patternRep = IsotopePatternRepository()

    '''def test_get_file(self):
        self.fail()'''

    def test_find_file(self):
        self.assertFalse(self.patternRep.findFile(('not','stored','in','system')))

    '''def test_add_isotope_pattern_from_file(self):
        self.fail()'''

    def test_check_equality(self):
        for i in range(15):
            fragment = Fragment('c',2,'',MolecularFormula({'C': randint(10, 20), 'H': randint(20, 50),
                                              'N': randint(5, 40), 'O': randint(5, 40), 'P': randint(0, 2)}), [],0)
            isotopePattern = fragment.getFormula().calculateIsotopePattern(0.996)
            fragment.setIsotopePattern(isotopePattern)
            randNr = (randint(-1,+1)/10**5)
            if randNr == 0.:
                isotopePattern1 = copy.deepcopy(isotopePattern)
                isotopePattern1['m/z'][1] += randNr
                self.patternRep.checkEquality(fragment, copy.deepcopy(isotopePattern))
            else:
                with self.assertRaises(InvalidIsotopePatternException):
                    isotopePattern1 = copy.deepcopy(isotopePattern)
                    isotopePattern1['m/z'][1] += randNr
                    self.patternRep.checkEquality(fragment,isotopePattern1)
                with self.assertRaises(InvalidIsotopePatternException):
                    isotopePattern1 = copy.deepcopy(isotopePattern)
                    isotopePattern1['calcInt'][2] += randNr
                    self.assertFalse(self.patternRep.checkEquality(fragment,isotopePattern1))

    def test_all(self):
        self.builderRNA.createFragmentLibrary()
        self.assertFalse(self.patternRep.findFile(('dummyRNA', 'RNA_CAD', '0', '-')))
        self.patternRep.saveIsotopePattern(self.builderRNA.addNewIsotopePattern())
        self.assertTrue(self.patternRep.findFile(('dummyRNA', 'RNA_CAD', '0', '-')))
        self.patternRep.addIsotopePatternFromFile(self.builderRNA.getFragmentLibrary())
        os.remove(os.path.join(path,'Fragment_lists','dummyRNA_RNA_CAD.csv'))

        self.builderRNA_CMCT2.createFragmentLibrary()
        self.assertFalse(self.patternRep.findFile(('dummyRNA', 'RNA_CAD', '2', 'CMCT')))
        self.patternRep.saveIsotopePattern(self.builderRNA_CMCT2.addNewIsotopePattern())
        self.assertTrue(self.patternRep.findFile(('dummyRNA', 'RNA_CAD', '2', 'CMCT')))
        self.patternRep.addIsotopePatternFromFile(self.builderRNA_CMCT2.getFragmentLibrary())
        os.remove(os.path.join(path,'Fragment_lists','dummyRNA_RNA_CAD_2_CMCT.csv'))

    def tearDown(self):
        self.sequenceService.delete('dummyRNA')
        self.sequenceService.delete('dummyProt')