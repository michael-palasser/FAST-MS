'''
Module for calculating isotope patterns
'''

import math
#from numba import njit
#from numba.typed import List
import numpy as np
from scipy.constants import electron_mass, N_A, proton_mass


def getByIndex(isotopeTable, index):
    '''
    Returns all entries in a table which have the corresponding index. Simulates an 3D array
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :param (int) index: index
    :return: ndarray(dtype=[float,float,float,float,float,float]) rows of table with corresponding indices
    '''
    return isotopeTable[np.where(isotopeTable['index'] == index)]

def logFact(x):
    '''
    Calculates the (natural) logarithm of the factorial of x
    :param (int) x:
    :return: ln of x!
    '''
    log_number = 0
    for i in range(1,x+1):
        log_number += math.log(i)
    return log_number


def binomial(k,n,p):
    '''
    Binomial distribution
    :param (int) k: number of successes / nr. of atoms of isotope
    :param (int) n: number of trials / nr. of atoms of the corresponding element
    :param (float) p: success probability for each trial / relative abundance of the isotope
    :return: (float) percentage for the isotopic composition
    '''
    return math.exp(logFact(n)-logFact(k)-logFact(n-k))*p**k*(1-p)**(n-k)

"""
def multinomial(k0, k1, k2, n, p0, p1,p2):
    return math.exp(logFact(n)-(logFact(k1)+logFact(k2)+logFact(k0))) * p1**k1 * p2**k2 * (p0)**(k0)"""


def multinomial(k, n, p):
    '''
    Multinomial distribution
    :param (ndarray(dtype=int)) k: number of successes / nr. of atoms of isotope
    :param (int) n: number of trials / nr. of atoms of the corresponding element
    :param (ndarray(dtype=float)) p: success probability for each trial / relative abundance of the isotope
    :return: (float) percentage for the isotopic composition
    '''
    coeff = logFact(n)
    rest = 1
    for i in range(len(k)):
        coeff -= logFact(k[i])
        rest *= p[i]**k[i]
    return math.exp(coeff) * rest


def calculatePercentage(isotopeTable):
    '''
    Calculates the percentage & mass of a certain isotope composition (isotopic fine structure)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (tuple[float,float]) mass, percentage (rel.abundance)
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


def calculateNuclFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for elemental composition CHNOP (RNA/DNA/proteins without S)
    :param (int) isotopePeak: number of isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (ndarray(dtype=[float,float])) fine structure [(mass,rel.abundance)]
    '''
    maxValues = getMaxValues(isotopePeak, isotopeTable)
    massI, propI = calculatePercentage(isotopeTable)
    fineStructure = [(massI, propI)]
    for i13C in list(range(maxValues[1]))[::-1]:
        for i2H in range(maxValues[3] + 1):
            for i15N in range(maxValues[5] + 1):
                for i17O in range(maxValues[7] + 1):
                    for i18O in range(int((maxValues[8] + 2) / 2)):
                        if (i13C + i2H + i15N + i17O + 2 * i18O == isotopePeak):
                            nrIsoList= np.array([0.,i13C,0.,i2H,0.,i15N,0.,i17O,i18O,0.])
                            for i in range(len(isotopeTable)):
                                isotopeTable[i]['nrIso']=nrIsoList[i]
                            massI, propI = calculatePercentage(isotopeTable)
                            fineStructure.append((massI,propI))
    return fineStructure

def getMaxValues(isotopePeak, isotopeTable):
    '''
    Returns a list of the maximum numbers of atoms of the corresponding isotopes.
    Maximum number is either the nr. of the isotope peak (if it is larger than the number of atoms
    :param (int) isotopePeak: nr. of the isotope peak
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (list[int]) max numbers of atoms of the corresponding isotopes (length = length of isotopeTable)
    '''
    maxValues = []
    for i in range(len(isotopeTable)):
        """if isotopePeak > isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(isotopePeak)"""
        maxVal = isotopePeak
        if isotopeTable[i]['M+']>1:
            maxVal = int(isotopePeak/isotopeTable[i]['M+'])
        if maxVal > isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(maxVal)
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak
    return maxValues


def calculatePeptFineStructure(isotopePeak, isotopeTable):
    '''
    Returns a list of the maximum numbers of atoms of the corresponding isotopes.
    Maximum number is either the nr. of the isotope peak (if it is larger than the number of atoms
    :param (int) isotopePeak: nr. of the isotope peak
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (ndarray(dtype=[float,float])) fine structure [(mass,rel.abundance)]
    '''
    #print(isotopeTable)
    maxValues = getMaxValues(isotopePeak, isotopeTable)
    massI, propI = calculatePercentage(isotopeTable)
    fineStructure = [(massI, propI)]
    for i13C in list(range(maxValues[1]))[::-1]:
        for i2H in range(maxValues[3] + 1):
            for i15N in range(maxValues[5] + 1):
                for i17O in range(maxValues[7] + 1):
                    for i18O in range(int((maxValues[8] + 2) / 2)):
                        for i33S in range(maxValues[10] + 1):
                            for i34S in range(int((maxValues[11] + 2) / 2)):
                                if (i13C + i2H + i15N + i17O + 2 * i18O +i33S + 2*i34S == isotopePeak):
                                    nrIsoList= np.array([0.,i13C,0.,i2H,0.,i15N,0.,i17O,i18O,0.,i33S,i34S])
                                    for i in range(len(isotopeTable)):
                                        isotopeTable[i]['nrIso']=nrIsoList[i]
                                    massI, propI = calculatePercentage(isotopeTable)
                                    fineStructure.append((massI,propI))
    return fineStructure


def setIsotopeTable(isotopeTable):
    '''
    Resets the number of all isotopes to 0 in isotope table
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (ndarray(dtype=[float,float,float,float,float,float])) reset isotopeTable
    '''
    for isotope in isotopeTable:
        isotope['nrIso'] = 0
    return isotopeTable


def calculateFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for molecules with a general elemental composition
    :param (int) isotopePeak: number of isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (ndarray(dtype=[float,float])) fine structure [(mass,rel.abundance)]
    '''
    fineStructure = [(0.,0.)]
    for iFirst in list(range(isotopePeak + 1))[::-1]:
        isotopeTable[1]['nrIso'] = iFirst
        if iFirst == isotopePeak:
            massI, propI = calculatePercentage(isotopeTable)
            fineStructure.append((massI,propI))
        else:
            fineStructure = loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, 3)
    return fineStructure[1:]


def loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, index):
    '''
    Recursive function which loops through molecular formula and calculates isotopic fine structure (recursive function)
    :param (int) isotopePeak: number of isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :param (list[tuple[float,float]]) fineStructure: growing isotopic fineStructure (tuples of (mass,rel.abundance))
    :param (int) index: running index of corresponding element
    :return: (list[tuple[float,float]]) final fineStructure [(mass,rel.abundance)]
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


eMass = electron_mass*N_A*1000
protMass = proton_mass *N_A*1000