from unittest import TestCase

from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.entities.SearchSettings import SearchSettings, processTemplateName
from src.services.DataServices import *


def initTestSequences(sequenceService=SequenceService()):
    sequences = [(tup[0], tup[1], tup[2]) for tup in sequenceService.getSequences()]
    names = [tup[0] for tup in sequences]
    [sequences.append(sequ) for sequ in [('dummyRNA', 'GACU', 'RNA'),('dummyProt', 'GAPH', 'Protein')]
            if sequ[0] not in names]
    sequenceService.save(sequences)


def deleteTestSequences(sequenceService=SequenceService()):
    sequenceService.delete('dummyRNA')
    sequenceService.delete('dummyProt')
    sequenceService.close()


class TestFragmentLibraryBuilder(TestCase):
    def setUp(self):
        try:
            self.initLibrary()
        except:
            initTestSequences(self.sequenceService)
            self.initLibrary()

    def initLibrary(self):
        self.sequenceService = SequenceService()
        self.propertyStorageRNA = SearchSettings('dummyRNA', 'RNA_CAD', 'CMCT')
        self.builderRNA = FragmentLibraryBuilder(SearchSettings('dummyRNA', 'RNA_CAD', '-'), 0)
        self.builderRNA_CMCT0 = FragmentLibraryBuilder(self.propertyStorageRNA, 0)
        self.builderRNA_CMCT1 = FragmentLibraryBuilder(self.propertyStorageRNA, 1)
        self.builderRNA_CMCT2 = FragmentLibraryBuilder(self.propertyStorageRNA, 2)
        self.propertyStorageProtCAD = SearchSettings('dummyProt', 'Protein_CAD', '-')
        self.builderProt_CAD = FragmentLibraryBuilder(self.propertyStorageProtCAD, 0)
        self.builderProt_ECD = FragmentLibraryBuilder(SearchSettings('dummyProt', 'Protein_ECD', '-'), 0)

    def test_build_simple_ladder(self):
        self.initLibrary()
        sequ = ['G', 'A', 'C', 'U', 'Unkown']
        with self.assertRaises(InvalidInputException):
            self.builderRNA.buildSimpleLadder(sequ)

    def test_check_for_residue(self):
        self.assertTrue(self.builderRNA.checkForResidue('G', ['A', 'G', 'U']))
        self.assertTrue(self.builderRNA.checkForResidue('-', ['A', 'G', 'U']))
        self.assertTrue(self.builderRNA.checkForResidue('', ['A', 'G', 'U']))
        self.assertFalse(self.builderRNA.checkForResidue('C', ['A', 'G', 'U']))

    def test_check_for_prolines(self):
        self.assertFalse(self.builderRNA.checkForProlines('c', ['G', 'A'], 'P'))
        self.assertFalse(self.builderProt_ECD.checkForProlines('c', ['G'], 'A'))
        self.assertTrue(self.builderProt_ECD.checkForProlines('c', ['G', 'A'], 'P'))
        self.assertFalse(self.builderProt_ECD.checkForProlines('c', ['G', 'A', 'P'], 'H'))
        self.assertTrue(self.builderProt_ECD.checkForProlines('z', ['H', 'P'], 'A'))

    def test_create_fragment_ladder(self):
        sequenceList, modifications, frags = self.getValues(self.propertyStorageRNA,
                                                            self.propertyStorageRNA.getFragmentation().getItems())
        fragsForw = [frag for frag in frags if frag.getDirection() == 1]
        simpleLadder = self.builderRNA.buildSimpleLadder(sequenceList)
        fragListLength = len(fragsForw) * (len(sequenceList) - 1) - 6
        self.assertEqual(fragListLength,
                         len(self.builderRNA_CMCT0.createFragmentLadder(simpleLadder,
                                                                        self.propertyStorageRNA.getFragmentation().getFragTemplates(
                                                                            1))))
        self.assertEqual((len(modifications) + 1) * fragListLength,
                         len(self.builderRNA_CMCT1.createFragmentLadder(simpleLadder,
                                                                        self.propertyStorageRNA.getFragmentation().getFragTemplates(
                                                                            1))))
        self.assertEqual((len(modifications) + 2) * fragListLength,
                         len(self.builderRNA_CMCT2.createFragmentLadder(simpleLadder,
                                                                        self.propertyStorageRNA.getFragmentation().getFragTemplates(
                                                                            1))))
        fragsBack = [frag for frag in frags if frag.getDirection() == -1]
        simpleLadderBack = self.builderRNA.buildSimpleLadder(sequenceList[::-1])
        fragListLength = len(fragsBack) * (len(sequenceList) - 1) - 11
        self.assertEqual(fragListLength,
                         len(self.builderRNA_CMCT0.createFragmentLadder(simpleLadderBack,
                                                                        self.propertyStorageRNA.getFragmentation().getFragTemplates(
                                                                            -1))))
        self.assertEqual((len(modifications) + 1) * fragListLength,
                         len(self.builderRNA_CMCT1.createFragmentLadder(simpleLadderBack,
                                                                        self.propertyStorageRNA.getFragmentation().getFragTemplates(
                                                                            -1))))
        self.assertEqual((len(modifications) + 2) * fragListLength,
                         len(self.builderRNA_CMCT2.createFragmentLadder(simpleLadderBack,
                                                                        self.propertyStorageRNA.getFragmentation().getFragTemplates(
                                                                            -1))))

    def getValues(self, storage, fragItems):
        sequenceList = self.propertyStorageRNA.getSequenceList()
        modifications = [mod for mod in storage.getModifPattern().getItems() if mod.isEnabled()]
        frags = [frag for frag in fragItems if frag.isEnabled()]
        return sequenceList, modifications, frags

    def test_process_template_name(self):
        tup = processTemplateName('c14-G')
        self.assertEqual('c14', tup[0])
        self.assertEqual('-G', tup[1])
        tup = processTemplateName('c03+CMCT+Na-Eth-G')
        self.assertEqual('c03', tup[0])
        self.assertEqual('+CMCT+Na-Eth-G', tup[1])

    def test_add_precursor(self):
        # RNA
        sequenceList, modifications, precFrags = self.getValues(self.propertyStorageRNA,
                                                                self.propertyStorageRNA.getFragmentation().getItems2())
        simpleLadderBack = self.builderRNA.buildSimpleLadder(sequenceList[::-1])
        self.assertEqual(len(precFrags),
                         len(self.builderRNA_CMCT0.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))
        self.assertEqual((len(modifications) + 1) * len(precFrags),
                         len(self.builderRNA_CMCT1.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))
        self.assertEqual((len(modifications) + 2) * len(precFrags),
                         len(self.builderRNA_CMCT2.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))
        self.assertEqual('dummyRNA', self.builderRNA_CMCT0.getPrecursor().getName())
        self.assertEqual('dummyRNA+CMCT', self.builderRNA_CMCT1.getPrecursor().getName())
        self.assertEqual('dummyRNA+2CMCT', self.builderRNA_CMCT2.getPrecursor().getName())

        # Protein
        sequenceList, modifications, precFrags = self.getValues(self.propertyStorageProtCAD,
                                                                self.propertyStorageProtCAD.getFragmentation().getItems2())
        simpleLadderBack = self.builderProt_CAD.buildSimpleLadder(sequenceList[::-1])
        self.assertEqual(len(precFrags),
                         len(self.builderProt_CAD.addPrecursor(simpleLadderBack[len(sequenceList) - 1][1])))
        self.assertEqual('dummyProt', self.builderProt_CAD.getPrecursor().getName())

    '''def test_create_fragment_library(self):
        self.fail()'''

    '''def test_add_new_isotope_pattern(self):
        self.fail()'''

    '''def test_get_precursor(self):
        self.test_add_precursor()'''

    """def tearDown(self):
        deleteTestSequences(self.sequenceService)"""


