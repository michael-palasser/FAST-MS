import copy

from src.FormulaFunctions import stringToFormula
from src.fastFunctions import *
import src.simpleFunctions as sf
from src.Services import PeriodicTableService

'''
Created on 3 Jul 2020

@author: michael
'''

periodicTableService = PeriodicTableService()

class MolecularFormula(object):
    '''
    Class that represents a molecular formula
    '''
    def __init__(self, formula):
        '''
        :param (dict[str,int] | str) formula: formula (if dict: {element:quantity})
        '''
        if type(formula) == str:
            formula = stringToFormula(formula, {}, 1)
        self._formulaDict = formula
        self._periodicTable = periodicTableService.getElements(list(self._formulaDict.keys()))


    def getFormulaDict(self):
        return self._formulaDict

    def addFormula(self, *args):
        '''
        Adds formula to formula
        :param (dict[str,int]) args: formulas to be added
        :return: (MolecularFormula) new formula
        '''
        newFormula = copy.deepcopy(self._formulaDict)
        for addedFormula in args:
            for element, number in addedFormula.items():
                if element in newFormula.keys():
                    newFormula[element] += number
                else:
                    newFormula[element] = number
        return MolecularFormula(newFormula)


    def subtractFormula(self, *args):
        '''
        Adds formula to formula
        :param (dict[str,int]) args: subtrahend (dict)
        :return: (MolecularFormula) new formula
        '''
        newFormula = copy.deepcopy(self._formulaDict)
        for addedFormula in args:
            for element, number in addedFormula.items():
                if element in newFormula.keys():
                    newFormula[element] -= number
                else:
                    newFormula[element] = -number
        return MolecularFormula(newFormula)


    def multiplyFormula(self, factor):
        '''
        Multiplies formula with a factor
        :param (int) args: factor
        :return: (MolecularFormula) new formula
        '''
        newFormula = copy.deepcopy(self._formulaDict)
        for element, number in newFormula.items():
            newFormula[element] *= factor
        return MolecularFormula(newFormula)

    def checkForNegativeValues(self):
        '''
        checks if one value of formulaDict is negative
        :return: (bool)
        '''
        for val in self._formulaDict.values():
            if val < 0:
                return True
        return False


    def toString(self):
        '''
        :return: (str) String representation of molecular formula
        '''
        #returnedString = 'C' + str(self.formulaDict['C']) + 'H' + str(self.formulaDict['H'])
        returnedString = ''
        for element in sorted(list(self._formulaDict.keys())):
            #if element in ['C','H']:
            #    continue
            #else:
            if self._formulaDict[element] > 0:
                returnedString += element + str(self._formulaDict[element])
        return returnedString

    def determineSystem(self, elements, theElements):
        for elem in elements:
            if elem not in theElements:
                return False
        return True

    def calculateIsotopePattern(self):
        '''
        Calculates isotope patterns based on molecular formulas
        :return: (ndarray(dtype=[float,float])) isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        mostAbundant=10**(-10)
        prop = 1
        isoPeak=0
        isotope_pattern = list()
        elements = [key for key,val in self._formulaDict.items() if val>0]
        if self.determineSystem(elements, {'C', 'H', 'N', 'O', 'P'}):
            calculate = calculateNuclFineStructure
            isotopeTable = self.makeNucIsotopeTable()
        elif self.determineSystem(elements, {'C', 'H', 'N', 'O', 'S'}):
            calculate = calculatePeptFineStructure
            isotopeTable = self.makeProteinIsotopeTable()
        else:
            calculate = calculateFineStructure
            isotopeTable = self.makeIsotopeTable()
            #print(isotopeTable)
        while(prop/mostAbundant>0.02):              #ToDo:Parameter
            setIsotopeTable(isotopeTable)
            ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
            prop = np.sum(ultrafineStruct[:,1])
            M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
            isotope_pattern.append((M_iso,prop))
            isoPeak += 1
            if prop > mostAbundant:
                mostAbundant = prop
            """if args and args[0]:
                if isoPeak == args[0]:
                    return np.array(isotope_pattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])"""
        """iso = np.array(isotope_pattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])
        print(np.sum(iso['calcInt']))"""
        return np.array(isotope_pattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])


    def makeNucIsotopeTable(self):
        '''
        Creates an isotope table for elemental composition CHNOP (RNA/DNA/proteins without S)
        :return: (ndarray(dtype=[float,float,float,float,float,float])) isotope table:
            isotope table for nucleic acids (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance
            of isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
        '''
        isotopeTable = list()
        for index, elem in enumerate(['C','H','N','O','P']):
            if elem in self._periodicTable:
                mono = self._periodicTable[elem][0][0]
                for isotope in self._periodicTable[elem]:
                    isotopeTable.append((index, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - mono))
        return np.array(isotopeTable,dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.float64)])


    def makeProteinIsotopeTable(self):
        '''
        Creates an isotope table for elemental composition CHNOS (proteins)
        :return: (ndarray(dtype=[float,float,float,float,float,float])) isotope table:
            isotope table for peptides (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance
            of isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
        '''
        isotopeTable = list()
        for index, elem in enumerate(['C','H','N','O','S']):
            if elem in self._periodicTable:
                mono = self._periodicTable[elem][0][0]
                for isotope in self._periodicTable[elem]:
                    isotopeTable.append((index, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - mono))
        return np.array(isotopeTable,dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.float64)])


    def makeIsotopeTable(self):
        '''
        Creates an isotope table for universal elemental composition
        :return: (ndarray(dtype=[float,float,float,float,float,float])) isotope table:
            isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of isotope,
            mass of isotope, nominal mass shift compared to isotope with lowest m/z)
        '''
        isotopeTable = list()
        elements = [elem for elem,val in self._periodicTable.items() if self._formulaDict[elem] > 0]
        #for index, elem in enumerate(sorted(list(self._periodicTable.keys()))):
        for index, elem in enumerate(sorted(elements)):
            mono = self._periodicTable[elem][0][0]
            for isotope in self._periodicTable[elem]:
                #if self._formulaDict[elem] != 0:
                isotopeTable.append((index, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - mono))
        isotopeTable = np.array(sorted(isotopeTable,key=lambda tup: tup[1], reverse=True)
                                , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                         ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])
        """isotopeTable = np.array(isotopeTable
                                , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                         ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])"""
        if len(getByIndex(isotopeTable, isotopeTable['index'][0])) != 2:
            match = None
            for isotope in isotopeTable:
                if len(getByIndex(isotopeTable, isotope['index'])) == 2:
                    match = isotope
                    break
            isotopeTable = np.concatenate((getByIndex(isotopeTable, match['index']),
                                          isotopeTable[np.where(isotopeTable['index'] != match['index'])]))
            index = -1
            oldIndex = None
            for row in isotopeTable:
                if oldIndex != row['index']:
                    oldIndex = row['index']
                    index += 1
                row['index'] = index
        return isotopeTable

    def calculateMonoIsotopic(self):
        '''
        Calculates monoisotopic mass
        :return: (float) monoisotopic mass
        '''
        monoisotopic = 0
        for elem,val in self._formulaDict.items():
            #print(elem, val, self._periodicTable[elem][0][1])
            monoisotopic += val*self._periodicTable[elem][0][1]
            """arr = np.array(self._periodicTable[elem])
            monoMass = arr[np.where(arr[:,3] == np.max(arr[:,3]))][0][2]
            monoisotopic += val*monoMass"""
        return monoisotopic

    def calcIsotopePatternSlowly(self, *args):
        '''
        Calculates isotope patterns based on molecular formulas without using the numba library
        :return: (ndarray(dtype=[float,float])) isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        self._periodicTable = periodicTableService.getElements(list(self._formulaDict.keys()))
        isotope_pattern = list()
        if self._formulaDict.keys() == {'C', 'H', 'N', 'O', 'P'}:
            calculate = sf.calculateNuclFineStructure
            isotopeTable = self.makeNucIsotopeTable()
        elif self._formulaDict.keys() == {'C', 'H', 'N', 'O', 'S'}:
            calculate = sf.calculatePeptFineStructure
            isotopeTable = self.makeProteinIsotopeTable()
        else:
            calculate = sf.calculateFineStructure
            isotopeTable = self.makeIsotopeTable()
        isotopeTable = isotopeTable.astype([('index',np.int32), ('nr',np.int32), ('nrIso',np.int32),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.int32)])
        if args and args[0]:
            for isoPeak in range(args[0]):
                sf.setIsotopeTable(isotopeTable)
                ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
                prop = np.sum(ultrafineStruct[:,1])
                M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
                isotope_pattern.append((M_iso,prop))
        else:
            mostAbundant=10**(-10)
            prop = 1
            isoPeak=0
            while (prop / mostAbundant > 0.02):  # ToDo:Parameter
                setIsotopeTable(isotopeTable)
                ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
                prop = np.sum(ultrafineStruct[:, 1])
                M_iso = np.sum(ultrafineStruct[:, 0] * ultrafineStruct[:, 1]) / prop
                isotope_pattern.append((M_iso, prop))
                isoPeak += 1
                if prop > mostAbundant:
                    mostAbundant = prop
        return np.array(isotope_pattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])