import math
from numba import njit
from numba.typed import List
import numpy as np

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
    maxValues = getMaxValues(isotopePeak, isotopeTable)
    """for i in range(10):
        if isotopePeak>isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(isotopePeak)
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak"""
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


@njit
def getMaxValues(isotopePeak, isotopeTable):
    maxValues = []
    for i in range(len(isotopeTable)):
        if isotopePeak>isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(isotopePeak)
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak
    return maxValues

@njit
def calculatePeptFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for elemental composition CHNOS (proteins)
    :param isotopePeak: number of isotope peak (M+x), int
    :param isotopeTable: 2D numpy array
    :return: fine structure [(mass,percentage)]
    '''
    #print(isotopeTable)
    maxValues = getMaxValues(isotopePeak, isotopeTable)
    """maxValues = []
    for i in range(12):
        if isotopePeak>isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(isotopePeak)
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak"""
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
    fineStructure = [(0.,0.)]
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


"""@njit
def calculateFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for molecules with a general elemental composition
    :param isotopePeak: number of isotope peak (M+x), int
    :param isotopeTable: 2D numpy array
    :return: fine structure [(mass,percentage)]
    '''
    global maxValues
    maxValues = getMaxValues(isotopePeak, isotopeTable)
    fineStructure = [(0.,0.)]
    for iFirst in list(range(isotopePeak + 1))[::-1]:
        isotopeTable[1]['nrIso'] = iFirst
        if iFirst == isotopePeak:
            massI, propI = calculatePercentage(isotopeTable)
            fineStructure.append((massI,propI))
        else:
            fineStructure = loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, maxValues, 3)
    return fineStructure[1:]

@njit
def loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, maxValues, index):
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
        for i in range(int((maxValues[index] + isotopeTable[index]['M+']) / isotopeTable[index]['M+'])):
            '''if i>isotopeTable[index]['nr']:
                break'''
            isotopeTable[index]['nrIso'] = i
            loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, maxValues, index + 1)
    return fineStructure"""

