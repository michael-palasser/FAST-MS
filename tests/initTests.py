import os
from unittest import TestCase

from tests.test_fastFunctions import fastFunctions_Test
from tests.test_FormulaFunctions import TestFormulaFunctions
from tests.test_IsotopePatternRepository import TestIsotopePatternRepository
from tests.test_LibraryBuilder import TestFragmentLibraryBuilder
from tests.test_MolecularFormula import MolecularFormulaTest


os.system('python -m unittest /Users/eva-maria/Data_exchange_folder/SAUSAGE_beta1/tests/test_fastFunctions.py')
os.system('python -m unittest /Users/eva-maria/Data_exchange_folder/SAUSAGE_beta1/tests/test_FormulaFunctions.py')
os.system('python -m unittest /Users/eva-maria/Data_exchange_folder/SAUSAGE_beta1/tests/test_IsotopePatternRepository.py')
os.system('python -m unittest /Users/eva-maria/Data_exchange_folder/SAUSAGE_beta1/tests/test_LibraryBuilder.py')
os.system('python -m unittest /Users/eva-maria/Data_exchange_folder/SAUSAGE_beta1/tests/test_MolecularFormula.py')