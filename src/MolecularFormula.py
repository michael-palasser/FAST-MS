import numpy as np
import copy

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
    Represents a molecular formula
    '''
    def __init__(self, formulaDict):
        '''
        Constructor
        :param formulaDict: key = element, value = quantity
        '''
        self.formulaDict = formulaDict


    def addFormula(self, *args):
        '''
        Adds formula to formula
        :param args: formula to be added (dict)
        :return: new formula (MolecularFormula)
        '''
        newFormula = copy.deepcopy(self.formulaDict)
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
        :param args: subtrahend (dict)
        :return: new formula (MolecularFormula)
        '''
        newFormula = copy.deepcopy(self.formulaDict)
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
        :param args: factor (int)
        :return: new formula (MolecularFormula)
        '''
        newFormula = copy.deepcopy(self.formulaDict)
        for element, number in newFormula.items():
            newFormula[element] *= factor
        return MolecularFormula(newFormula)

    def checkForNegativeValues(self):
        '''
        checks if one value of formulaDict is negative
        :return: boolean
        '''
        for val in self.formulaDict.values():
            if val < 0:
                return True
        return False


    def toString(self):
        '''
        :return: String of molecular formula
        '''
        returnedString = 'C' + str(self.formulaDict['C']) + 'H' + str(self.formulaDict['H'])
        for element in sorted(list(self.formulaDict.keys())):
            if element in ['C','H']:
                continue
            else:
                if self.formulaDict[element] > 0:
                    returnedString += element + str(self.formulaDict[element])
        return returnedString


    def calculateIsotopePattern(self):
        '''
        Calculates isotope patterns based on molecular formulas
        :return: isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        self._periodicTable = periodicTableService.getElements(self.formulaDict.keys())
        mostAbundant=10**(-10)
        prop = 1
        isoPeak=0
        isotope_pattern = list()
        if self.formulaDict.keys() == {'C','H','N','O','P'}:
            calculate = calculateNuclFineStructure
            isotopeTable = self.makeNucIsotopeTable()
        elif self.formulaDict.keys() == {'C', 'H', 'N', 'O', 'S'}:
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
        :return: isotope table (structured numpy array: [(index, quantity)]
        '''
        isotopeTable = list()
        for index, elem in enumerate(['C','H','N','O','P']):
            if elem in self._periodicTable:
                mono = self._periodicTable[elem][0][0]
                for isotope in self._periodicTable[elem]:
                    isotopeTable.append((index, self.formulaDict[elem],0, isotope[2], isotope[1], isotope[0] - mono))
        return np.array(isotopeTable,dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.float64)])


    def makeProteinIsotopeTable(self):
        '''
        Creates an isotope table for elemental composition CHNOS (proteins)
        :return: isotope table (structured numpy array: [(index, quantity)]
        x = number of isotope (M+x)
        '''
        isotopeTable = list()
        for index, elem in enumerate(['C','H','N','O','S']):
            if elem in self._periodicTable:
                mono = self._periodicTable[elem][0][0]
                for isotope in self._periodicTable[elem]:
                    isotopeTable.append((index, self.formulaDict[elem],0, isotope[2], isotope[1], isotope[0] - mono))
        return np.array(isotopeTable,dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.float64)])


    def makeIsotopeTable(self):
        '''
        Creates an isotope table for general elemental composition
        :return: isotope table (structured numpy array: [(index, quantity)]
        '''
        isotopeTable = list()
        for index, elem in enumerate(sorted(list(self._periodicTable.keys()))):
            mono = self._periodicTable[elem][0][0]
            for isotope in self._periodicTable[elem]:
                if self.formulaDict[elem] != 0:
                    isotopeTable.append((index, self.formulaDict[elem], 0, isotope[2], isotope[1], isotope[0]-mono))
        isotopeTable = np.array(sorted(isotopeTable,key=lambda tup: tup[1], reverse=True)
                                , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                         ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])
        """isotopeTable = np.array(isotopeTable
                                , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                         ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])"""
        if len(getByIndex(isotopeTable, 0)) != 2:
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
        :return: monoisotopic mass
        '''
        monoisotopic = 0
        for elem,val in self.formulaDict.items():
            monoisotopic += val*self._periodicTable[elem][0][2]
            """arr = np.array(self._periodicTable[elem])
            monoMass = arr[np.where(arr[:,3] == np.max(arr[:,3]))][0][2]
            monoisotopic += val*monoMass"""
        return monoisotopic

    def calcIsotopePatternSlowly(self, *args): #ToDo
        '''
        Calculates isotope patterns based on molecular formulas
        :return: isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        self._periodicTable = periodicTableService.getElements(self.formulaDict.keys())
        isotope_pattern = list()
        if self.formulaDict.keys() == {'C','H','N','O','P'}:
            calculate = sf.calculateNuclFineStructure
            isotopeTable = self.makeNucIsotopeTable()
        elif self.formulaDict.keys() == {'C', 'H', 'N', 'O', 'S'}:
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