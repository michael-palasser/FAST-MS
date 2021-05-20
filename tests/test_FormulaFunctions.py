from unittest import TestCase

from src.FormulaFunctions import *

string1 = 'C5H5N5O'
string2 = 'C5H5N5OS10Se1'
string3 = '(C5H5N5O)10S10Se'
dict1= {'C':5,'H':5,'N':5, 'O':1}
dict1_0={'C':0,'H':0,'N':0, 'O':0}
dict2= {'C':5,'H':5,'N':5, 'O':1, 'S': 10, 'Se':1}
dict3= {'C':50,'H':50,'N':50, 'O':10, 'S': 10, 'Se':1}


class TestFormulaFunctions(TestCase):
    def test_string_to_formula2(self):
        self.assertEqual(stringToFormula2(string1, {}, 1), dict1)
        self.assertEqual(stringToFormula2(string1, stringToFormula2(string1, {}, 1), -1), dict1_0)
        self.assertEqual(stringToFormula2(string2, {}, 1), dict2)

    def test_string_to_formula(self):
        self.assertEqual(stringToFormula(string1, {}, 1), stringToFormula2(string1, {}, 1))
        self.assertEqual(stringToFormula(string1, stringToFormula(string1, {}, 1), -1), dict1_0)
        self.assertEqual(stringToFormula(string3, {}, 1), dict3)

