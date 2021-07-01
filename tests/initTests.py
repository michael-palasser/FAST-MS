import unittest

from tests.test_fastFunctions import fastFunctions_Test
from tests.test_FormulaFunctions import TestFormulaFunctions
from tests.test_MolecularFormula import MolecularFormulaTest
from tests.top_down.test_LibraryBuilder import TestFragmentLibraryBuilder
from tests.top_down.test_IsotopePatternRepository import TestIsotopePatternRepository
from tests.top_down.test_SpectrumHandler import TestSpectrumHandler
from tests.top_down.test_IntensityModeller import TestIntensityModeller
from tests.top_down.test_Analyser import TestAnalyser
from tests.intact.test_IntactLibraryBuilder import IntactLibraryBuilder
from tests.intact.test_IntactFinder import TestFinder
from tests.intact.test_IntactAnalyser import TestIntactAnalyser
from tests.test_IsotopePatternLogics import TestIsotopePatternLogics
from tests.test_Services import *

if __name__ == '__main__':
    unittest.main()