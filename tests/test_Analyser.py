from unittest import TestCase

from src.top_down.Analyser import Analyser
from tests.test_SpectrumHandler import initTestLibraryBuilder


class TestAnalyser(TestCase):
    def setUp(self):
        configs, settings, props, builder = initTestLibraryBuilder()
        self.fragments = builder.getFragmentLibrary()
        self.analyser = Analyser([],props.getSequenceList(),settings['charge'],props.getModification().getName())


    def test_calculate_rel_abundance_of_species(self):
        self.fail()

    def test_get_modification_loss(self):
        self.fail()

    def test_calculate_occupancies(self):
        self.fail()

    def test_get_nr_of_modifications(self):
        self.fail()

    def test_calculate_proportions(self):
        self.fail()

    def test_analyse_charges(self):
        self.fail()

    def test_to_table(self):
        self.fail()
