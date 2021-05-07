from unittest import TestCase

from src.MolecularFormula import MolecularFormula
from src.entities.GeneralEntities import Sequence
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.entities.SearchProperties import PropertyStorage
from src.Services import *


class TestFragmentLibraryBuilder(TestCase):
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
        #self.fragmentationService = FragmentationService
        #self.modificationService = ModificationService()
        '''print(self.sequenceService.getSequences())
        sequences = [Sequence(tup[0], tup[1], tup[2],i) for i,tup in enumerate(self.sequenceService.getSequences())]
        sequences.append(Sequence('dummyRNA','GACU','RNA', len(sequences)+1))
        sequences.append(Sequence('dummyProt','GAPH','Protein', len(sequences)+1))
        print(sequences)
        self.sequenceService.save(sequences)'''
        self.propertyStorageRNA = PropertyStorage('dummyRNA','RNA_CAD','CMCT')
        self.builderRNA = FragmentLibraryBuilder(PropertyStorage('dummyRNA','RNA_CAD','-'),0)
        self.builderRNA_CMCT0 = FragmentLibraryBuilder(self.propertyStorageRNA,0)
        self.builderRNA_CMCT1 = FragmentLibraryBuilder(self.propertyStorageRNA,1)
        self.builderRNA_CMCT2 = FragmentLibraryBuilder(self.propertyStorageRNA,2)
        self.builderProt_CAD = FragmentLibraryBuilder(PropertyStorage('dummyProt','Protein_CAD','-'),0)
        self.builderProt_ECD = FragmentLibraryBuilder(PropertyStorage('dummyProt','Protein_ECD','-'),0)


    def test_build_simple_ladder(self):
        self.initLibrary()
        sequ = ['G','A','C','U', 'Unkown']
        with self.assertRaises(InvalidInputException):
            self.builderRNA.buildSimpleLadder(sequ)

    def test_check_for_residue(self):
        self.assertTrue(self.builderRNA.checkForResidue('G',['A','G','U']))
        self.assertTrue(self.builderRNA.checkForResidue('-',['A','G','U']))
        self.assertTrue(self.builderRNA.checkForResidue('',['A','G','U']))
        self.assertFalse(self.builderRNA.checkForResidue('C',['A','G','U']))

    def test_check_for_prolines(self):
        self.assertFalse(self.builderRNA.checkForProlines('c',['G','A'],'P'))
        self.assertFalse(self.builderProt_ECD.checkForProlines('c',['G'],'A'))
        self.assertTrue(self.builderProt_ECD.checkForProlines('c',['G','A'],'P'))
        self.assertFalse(self.builderProt_ECD.checkForProlines('c',['G','A','P'],'H'))
        self.assertTrue(self.builderProt_ECD.checkForProlines('z',['H','P'],'A'))

    def test_create_fragment_ladder(self):
        self.fail()

    def test_process_template_name(self):
        tup = self.builderRNA.processTemplateName('c14-G')
        self.assertEqual('c14', tup[0])
        self.assertEqual('-G', tup[1])
        tup = self.builderRNA.processTemplateName('c03+CMCT+Na-Eth-G')
        self.assertEqual('c03', tup[0])
        self.assertEqual('+CMCT+Na-Eth-G', tup[1])

    def test_add_precursor(self):
        sequenceList = self.propertyStorageRNA.getSequenceList()
        modifications = self.propertyStorageRNA.getModification().getItems()
        precFrags = [precFrag for precFrag in self.propertyStorageRNA.getFragmentation().getItems2() if precFrag.enabled()]
        simpleLadderBack = self.builderRNA.buildSimpleLadder(sequenceList[::-1])
        self.assertEqual(len(precFrags),
                         len(self.builderRNA_CMCT0.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))
        self.assertEqual((len(modifications)+1)*len(precFrags),
                         len(self.builderRNA_CMCT1.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))
        self.assertEqual((len(modifications)+2)*len(precFrags),
                         len(self.builderRNA_CMCT2.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))


    def test_create_fragment_library(self):
        self.fail()

    def test_add_new_isotope_pattern(self):
        self.fail()


    def test_get_precursor(self):
        self.fail()

    '''def tearDown(self):
        self.sequenceService.delete('dummyRNA')
        self.sequenceService.delete('dummyProt')'''