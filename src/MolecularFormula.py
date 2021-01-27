import numpy as np
import copy
import math
from numba import njit
from numba.typed import List
from src.PeriodicTable import periodicTable

'''
Created on 3 Jul 2020

@author: michael
'''

@njit
def getByIndex(isotopeTable, index):
    '''
    Gets all entries with index. Simulates an 3D pattern structure
    :param isotopeTable: numpy array (2D)
    :param index: int
    :return: numpy array
    '''
    return isotopeTable[np.where(isotopeTable['index'] == index)]


@njit
def logFact(x):
    '''
    Calculates the log10 of x!
    :param x: int
    :return: log10 of x!
    '''
    log_number = 0
    for i in range(1,x+1):
        log_number += math.log(i)
    return log_number

@njit
def binomial(k,n,p):
    '''
    Binomial distribution
    :param k:
    :param n:
    :param p:
    :return: percentage
    '''
    return math.exp(logFact(n)-logFact(k)-logFact(n-k))*p**k*(1-p)**(n-k)

"""@njit
def multinomial(k0, k1, k2, n, p0, p1,p2):
    return math.exp(logFact(n)-(logFact(k1)+logFact(k2)+logFact(k0))) * p1**k1 * p2**k2 * (p0)**(k0)"""

@njit
def multinomial(k, n, p):
    '''
    Multinomial distribution
    :param k:
    :param n:
    :param p:
    :return: percentage
    '''
    coeff = logFact(n)
    rest = 1
    for i in range(len(k)):
        coeff -= logFact(k[i])
        rest *= p[i]**k[i]
    return math.exp(coeff) * rest


@njit
def calculatePercentage(isotopeTable):
    '''
    Calculates the percentage & mass of a certain isotope composition (isotopic fine structure)
    :param isotopeTable: numpy array
    :return: mass and percentage
    '''
    propI = 1.
    massI = 0.
    finishedIndizes = list()
    #print(massI,'\n')
    for isotope in isotopeTable:
        if isotope['index'] not in finishedIndizes:
            finishedIndizes.append(isotope['index'])
            isotopes = getByIndex(isotopeTable,isotope['index'])
            if len(isotopes) == 1:
                massI += isotope['nr'] * isotope['mass']
            elif len(isotopes) == 2:
                propI *= binomial(isotopes[1]['nrIso'], isotope['nr'], isotopes[1]['relAb'])
                massI += (isotopes[0]['mass']*(isotope['nr']-isotopes[1]['nrIso'])
                          +isotopes[1]['mass']*isotopes[1]['nrIso'])
                x=isotopes               #array changed otherwise for unkown reasons
            elif len(isotopes) == 3:
                propI *= multinomial(k=np.array([isotope['nr'] - np.sum(isotopes['nrIso']),
                                          isotopes[1]['nrIso'], isotopes[2]['nrIso']]),
                                         n=isotope['nr'],
                                         p=np.array([isotopes[0]['relAb'], isotopes[1]['relAb'],
                                            isotopes[2]['relAb']]))
                massI += (isotopes[0]['mass'] * (isotope['nr'] - np.sum(isotopes['nrIso']))
                          + isotopes[1]['mass'] * (isotopes[1]['nrIso'])
                          + isotopes[2]['mass'] * (isotopes[2]['nrIso']))
                x = isotopes               #array changed otherwise for unkown reasons
            else:       #ToDo: Test
                massI += isotopes[0]['mass'] * (isotope['nr'] - np.sum(isotopes['nrIso']))
                kList = [isotope['nr'] - np.sum(isotopes['nrIso'])]
                pList = [isotopes[0]['relAb']]
                for i in range(1, len(isotopes)):
                    massI += isotopes[i]['mass'] * (isotopes[i]['nrIso'])
                    kList.append(isotopes[i]['nrIso'])
                    pList.append(isotopes[i]['relAb'])
                propI *= multinomial(k=np.array(kList),
                                     n=isotope['nr'],
                                     p=np.array(pList))
                x = isotopes  # array changed otherwise for unkown reasons
    return massI,propI


@njit
def calculateNuclFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for elemental composition CHNOP (RNA/DNA/proteins without S)
    :param isotopePeak: number of isotope peak (M+x), int
    :param isotopeTable: 2D numpy array
    :return: fine structure [(mass,percentage)]
    '''
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak
    massI, propI = calculatePercentage(isotopeTable)
    fineStructure = [(massI, propI)]
    for i13C in list(range(isotopePeak))[::-1]:
        for i2H in range(isotopePeak + 1):
            for i15N in range(isotopePeak + 1):
                for i17O in range(isotopePeak + 1):
                    for i18O in range(int((isotopePeak + 2) / 2)):
                        if (i13C + i2H + i15N + i17O + 2 * i18O == isotopePeak):
                            nrIsoList= np.array([0.,i13C,0.,i2H,0.,i15N,0.,i17O,i18O,0.])
                            for i in range(len(isotopeTable)):
                                isotopeTable[i]['nrIso']=nrIsoList[i]
                            massI, propI = calculatePercentage(isotopeTable)
                            fineStructure.append((massI,propI))
    return fineStructure


@njit
def calculatePeptFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for elemental composition CHNOS (proteins)
    :param isotopePeak: number of isotope peak (M+x), int
    :param isotopeTable: 2D numpy array
    :return: fine structure [(mass,percentage)]
    '''
    #print(isotopeTable)
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak
    massI, propI = calculatePercentage(isotopeTable)
    fineStructure = [(massI, propI)]
    for i13C in list(range(isotopePeak))[::-1]:
        for i2H in range(isotopePeak + 1):
            for i15N in range(isotopePeak + 1):
                for i17O in range(isotopePeak + 1):
                    if i17O > isotopeTable[7]['nr']:
                        break
                    for i18O in range(int((isotopePeak + 2) / 2)):
                        if i18O > isotopeTable[8]['nr']:
                            break
                        for i33S in range(isotopePeak + 1):
                            if i33S > isotopeTable[10]['nr']:
                                break
                            for i34S in range(int((isotopePeak + 2) / 2)):
                                if i34S > isotopeTable[11]['nr']:
                                    break
                                if (i13C + i2H + i15N + i17O + 2 * i18O +i33S + 2*i34S == isotopePeak):
                                    nrIsoList= np.array([0.,i13C,0.,i2H,0.,i15N,0.,i17O,i18O,0.,i33S,i34S])
                                    for i in range(len(isotopeTable)):
                                        isotopeTable[i]['nrIso']=nrIsoList[i]
                                    massI, propI = calculatePercentage(isotopeTable)
                                    fineStructure.append((massI,propI))
    return fineStructure




@njit
def setIsotopeTable(isotopeTable):
    '''
    Resets the number of all isotopes to 0 in isotope table
    :param isotopeTable:
    :return: isotopeTable
    '''
    for isotope in isotopeTable:
        isotope['nrIso'] = 0
    return isotopeTable


@njit
def calculateFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for molecules with a general elemental composition
    :param isotopePeak: number of isotope peak (M+x), int
    :param isotopeTable: 2D numpy array
    :return: fine structure [(mass,percentage)]
    '''
    fineStructure = List()
    for iFirst in list(range(isotopePeak + 1))[::-1]:
        isotopeTable[1]['nrIso'] = iFirst
        if iFirst == isotopePeak:
            massI, propI = calculatePercentage(isotopeTable)
            fineStructure.append((massI,propI))
        else:
            fineStructure = loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, 3)
    return fineStructure[1:]


@njit
def loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, index):
    '''
    Loops through molecular formula and calculates isotopic fine structure (recursive function)
    :param isotopePeak: number of isotope peak (M+x), int
    :param isotopeTable: 2D numpy array
    :param fineStructure: isotopic fineStructure (list)
    :param index: running index of corresponding element
    :return: fineStructure [(mass,percentage)]
    '''
    if (np.sum(isotopeTable['nrIso']*isotopeTable['M+']) == isotopePeak):
        massI, propI = calculatePercentage(isotopeTable)
        fineStructure.append((massI, propI))
        return fineStructure
    elif index < len(isotopeTable):
        while (isotopeTable[index]['M+'] == 0):
            index+=1
            if index >= len(isotopeTable):
                return fineStructure
        for i in range(int((isotopePeak + isotopeTable[index]['M+']) / isotopeTable[index]['M+'])):
            if i>isotopeTable[index]['nr']:
                break
            isotopeTable[index]['nrIso'] = i
            loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, index + 1)
    return fineStructure


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


    def calculateIsotopePattern(self, *args):
        '''
        Calculates isotope patterns based on molecular formulas
        :return: isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        mostAbundant=10**(-10)
        prop = 1
        isoPeak=0
        isotope_pattern = list()
        if (len(self.formulaDict.keys()-{'C','H','N','O','P'}) == 0):
            mode = 'NA'
            isotopeTable = self.makeNucleicIsotopeTable()
        elif (len(self.formulaDict.keys()-{'C','H','N','O','S'}) == 0):
            mode = 'peptide'
            isotopeTable = self.makeProteinIsotopeTable()
        else:
            mode = 'general'
            isotopeTable = self.makeIsotopeTable()
        while(prop/mostAbundant>0.02):              #ToDo:Parameter
            setIsotopeTable(isotopeTable)
            if mode == 'NA':
                ultrafineStruct = calculateNuclFineStructure(isoPeak, isotopeTable)
            elif mode == 'peptide':
                ultrafineStruct = calculatePeptFineStructure(isoPeak, isotopeTable)
            else:
                ultrafineStruct = calculateFineStructure(isoPeak, isotopeTable)
            ultrafineStruct = np.array(ultrafineStruct)
            prop = np.sum(ultrafineStruct[:,1])
            M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
            isotope_pattern.append((M_iso,prop))
            isoPeak += 1
            if prop > mostAbundant:
                mostAbundant = prop
            if args and args[0]:
                if isoPeak == args[0]:
                    return np.array(isotope_pattern, dtype=[('mass', np.float64), ('relAb', np.float64)])
        return np.array(isotope_pattern, dtype=[('mass',np.float64),('relAb', np.float64)])


    def makeNucleicIsotopeTable(self):
        '''
        Creates an isotope table for elemental composition CHNOP (RNA/DNA/proteins without S)
        :return: isotope table (structured numpy array: [(index, quantity)]
        x = number of isotope (M+x)
        '''
        isotopeTable = list()
        index =0
        for elem in ['C','H','N','O','P']:
            x=0
            while x<len(periodicTable[elem]):
                nr = 0
                if elem in self.formulaDict.keys():
                    nr = self.formulaDict[elem]
                isotopeTable.append((index, nr,0, periodicTable[elem][x][3],
                                     periodicTable[elem][x][2],x))
                x+=1
            index+=1
        # ToDo: aussortieren
        return np.array(isotopeTable,dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.float64)])


    def makeProteinIsotopeTable(self):
        '''
        Creates an isotope table for elemental composition CHNOS (proteins)
        :return: isotope table (structured numpy array: [(index, quantity)]
        x = number of isotope (M+x)
        '''
        isotopeTable = list()
        index =0
        for elem in ['C','H','N','O','S']:
            x=0
            while x<len(periodicTable[elem]):
                nr = 0
                if elem in self.formulaDict.keys():
                    nr = self.formulaDict[elem]
                isotopeTable.append((index, nr,0, periodicTable[elem][x][3],
                                     periodicTable[elem][x][2],x))
                x+=1
            index+=1
        # ToDo: aussortieren
        return np.array(isotopeTable,dtype = [('index',np.float64), ('nr',np.float64), ('nrIso',np.float64),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.float64)])


    def makeIsotopeTable(self):
        '''
        Creates an isotope table for general elemental composition
        :return: isotope table (structured numpy array: [(index, quantity)]
        '''
        isotopeTable = list()
        index = 1
        for key, isotopes in periodicTable.items():
            if key in self.formulaDict:
                for isotope in isotopes:
                    if len(isotopes) > 3:
                        raise Exception('element ', key, 'has too many isotopes')
                    elif self.formulaDict[key] != 0:
                        isotopeTable.append((index, self.formulaDict[key], 0, isotope[3], isotope[2], isotope[1]))
                index += 1
        isotopeTable = np.array(sorted(isotopeTable,key=lambda tup: tup[1], reverse=True)
                                , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                         ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])
        if len(getByIndex(isotopeTable, 1)) != 2:
            match = None
            for isotope in isotopeTable:
                if len(getByIndex(isotopeTable, isotope['index'])) == 2:
                    match = isotope
                    break
            isotopeTable = np.concatenate((getByIndex(isotopeTable, match['index']),
                                          isotopeTable[np.where(isotopeTable['index'] != match['index'])]))
        return isotopeTable



    def calculateMonoIsotopic(self):
        '''
        Calculates monoisotopic mass
        :return: monoisotopic mass
        '''
        monoisotopic = 0
        for elem,val in self.formulaDict.items():
            monoisotopic += val*periodicTable[elem][0][2]
            """arr = np.array(periodicTable[elem])
            monoMass = arr[np.where(arr[:,3] == np.max(arr[:,3]))][0][2]
            monoisotopic += val*monoMass"""
        return monoisotopic
