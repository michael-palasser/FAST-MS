'''
Module for calculating isotope patterns using numba library
'''

import math
from numba import njit
import numpy as np


@njit
def getByIndex(isotopeTable, index):
    '''
    Returns all entries in a table which have the corresponding index. Simulates an 3D array
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :param (int) index: index
    :return: ndarray(dtype=[float,float,float,float,float,float]) rows of table with corresponding indices
    '''
    '''if len(isotopeTable[np.where(isotopeTable['index'] == index)]) == 0:
        print(index)
        raise Exception(str(index))'''
    return isotopeTable[np.where(isotopeTable['index'] == index)]


@njit
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

@njit
def binomial(k,n,p):
    '''
    Binomial distribution
    :param (int) k: number of successes / nr. of atoms of isotope
    :param (int) n: number of trials / nr. of atoms of the corresponding element
    :param (float) p: success probability for each trial / relative abundance of the isotope
    :return: (float) percentage for the isotopic composition
    '''
    return math.exp(logFact(n)-logFact(k)-logFact(n-k))*p**k*(1-p)**(n-k)

"""@njit
def multinomial(k0, k1, k2, n, p0, p1,p2):
    return math.exp(logFact(n)-(logFact(k1)+logFact(k2)+logFact(k0))) * p1**k1 * p2**k2 * (p0)**(k0)"""

@njit
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


@njit
def calculateSpecies(isotopeTable):
    '''
    Calculates the mass & abundance of an isotope composition
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, no. of atoms of the element, no. of atoms of the isotope,
        rel. abundance of the isotope, mass of the isotope,
        nominal mass shift compared to the isotope with the lowest m/z)
    :return: (tuple[float,float]) mass, rel. abundance
    '''
    abundance = 1.
    mass = 0.
    finishedIndizes = list()
    #print(mass,'\n')
    for isotope in isotopeTable:
        if isotope['index'] not in finishedIndizes:
            finishedIndizes.append(isotope['index'])
            isotopes = getByIndex(isotopeTable,isotope['index'])
            if len(isotopes) == 1:
                mass += isotope['nr'] * isotope['mass']
            elif len(isotopes) == 2:
                abundance *= binomial(isotopes[1]['nrIso'], isotope['nr'], isotopes[1]['relAb'])
                mass += (isotopes[0]['mass']*(isotope['nr']-isotopes[1]['nrIso'])
                          +isotopes[1]['mass']*isotopes[1]['nrIso'])
                x=isotopes               #array changed otherwise for unkown reasons
            elif len(isotopes) == 3:
                abundance *= multinomial(k=np.array([isotope['nr'] - np.sum(isotopes['nrIso']),
                                          isotopes[1]['nrIso'], isotopes[2]['nrIso']]),
                                         n=isotope['nr'],
                                         p=np.array([isotopes[0]['relAb'], isotopes[1]['relAb'],
                                            isotopes[2]['relAb']]))
                mass += (isotopes[0]['mass'] * (isotope['nr'] - np.sum(isotopes['nrIso']))
                          + isotopes[1]['mass'] * (isotopes[1]['nrIso'])
                          + isotopes[2]['mass'] * (isotopes[2]['nrIso']))
                x = isotopes               #array changed otherwise for unkown reasons
            else:       #ToDo: Test
                mass += isotopes[0]['mass'] * (isotope['nr'] - np.sum(isotopes['nrIso']))
                '''k_arr = np.empty(len(isotopes), dtype=np.int16)
                p_arr = np.empty(len(isotopes), dtype=np.float32)
                k_arr[0] = isotope['nr'] - np.sum(isotopes['nrIso'])
                p_arr[0] = isotopes[0]['relAb']'''
                kList = [isotope['nr'] - np.sum(isotopes['nrIso'])]
                pList = [isotopes[0]['relAb']]
                for i in range(1, len(isotopes)):
                    mass += isotopes[i]['mass'] * (isotopes[i]['nrIso'])
                    kList.append(isotopes[i]['nrIso'])
                    pList.append(isotopes[i]['relAb'])
                    '''k_arr[i] = isotopes[i]['nrIso']
                    p_arr[i] = isotopes[i]['relAb']'''
                abundance *= multinomial(k=np.array(kList), n=isotope['nr'], p=np.array(pList))
                #abundance *= multinomial(k=k_arr, n=isotope['nr'], p=p_arr)
                x = isotopes  # array changed otherwise for unkown reasons
    return mass,abundance



@njit
def calculateNuclFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for elemental composition CHNOP (RNA/DNA/proteins without S)
    :param (int) isotopePeak: number of isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, no. of atoms of the element, no. of atoms of the isotope,
        rel. abundance of the isotope, mass of the isotope,
        nominal mass shift compared to the isotope with the lowest m/z)
    :return: (ndarray(dtype=[float,float])) fine structure [(mass,rel.abundance)]
    '''
    #print(isotopePeak)
    maxValues = getMaxValues(isotopePeak, isotopeTable)
    """for i in range(10):
        if isotopePeak>isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(isotopePeak)
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak"""
    #print(isotopeTable['nrIso'])
    massI, propI = calculateSpecies(isotopeTable)
    fineStructure = [(massI, propI)]
    for i13C in list(range(maxValues[1]))[::-1]:
        for i2H in range(maxValues[3] + 1):
            for i15N in range(maxValues[5] + 1):
                for i17O in range(maxValues[7] + 1):
                    for i18O in range(maxValues[8] + 1):
                        if (i13C + i2H + i15N + i17O + 2 * i18O == isotopePeak) and \
                                not (i17O + i18O > isotopeTable[6]['nr']) :
                            nrIsoList= np.array([0.,i13C,0.,i2H,0.,i15N,0.,i17O,i18O,0.])
                            #print(nrIsoList)
                            for i in range(len(isotopeTable)):
                                isotopeTable[i]['nrIso']=nrIsoList[i]
                            #massI, propI = calculatePercentage(isotopeTable)
                            #fineStructure.append((massI,propI))
                            fineStructure.append(calculateSpecies(isotopeTable))
    return fineStructure


@njit
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
    #maxValues = np.empty(len(isotopeTable))
    maxValues = list()
    for i in range(len(isotopeTable)):
        """if isotopePeak > isotopeTable[i]['nr']:
            maxValues.append(isotopeTable[i]['nr'])
        else:
            maxValues.append(isotopePeak)"""
        maxVal = isotopePeak
        if isotopeTable[i]['M+']>1:
            maxVal = int(isotopePeak/isotopeTable[i]['M+'])
        if maxVal > isotopeTable[i]['nr']:
            maxValues.append(int(isotopeTable[i]['nr']))
            #maxValues[i] = isotopeTable[i]['nr']
        else:
            maxValues.append(maxVal)
            #maxValues[i] = maxVal
    if isotopePeak > 0:
        isotopeTable[1]['nrIso'] = isotopePeak
    #print('maxValues',isotopePeak,maxValues)
    return maxValues

@njit
def calculatePeptFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates isotopic fine structure of isotope peak for elemental composition CHNOS (proteins)
    :param (int) isotopePeak: number of isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, no. of atoms of the element, no. of atoms of the isotope,
        rel. abundance of the isotope, mass of the isotope,
        nominal mass shift compared to the isotope with the lowest m/z)
    :return: (ndarray(dtype=[float,float])) fine structure [(mass,percentage)]
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
    #print(isotopeTable['nrIso'])
    massI, propI = calculateSpecies(isotopeTable)
    fineStructure = [(massI, propI)]
    for i13C in list(range(maxValues[1]))[::-1]:
        for i2H in range(maxValues[3] + 1):
            for i15N in range(maxValues[5] + 1):
                for i17O in range(maxValues[7] + 1):
                    for i18O in range(int(maxValues[8] + 1)):
                        if not (i17O + i18O > isotopeTable[6]['nr']):
                            for i33S in range(maxValues[10] + 1):
                                for i34S in range(maxValues[11] +1):
                                    if (i13C + i2H + i15N + i17O + 2 * i18O +i33S + 2*i34S == isotopePeak) and  \
                                            not (i33S + i34S > isotopeTable[9]['nr']):
                                        nrIsoList= np.array([0.,i13C,0.,i2H,0.,i15N,0.,i17O,i18O,0.,i33S,i34S])
                                        for i in range(len(isotopeTable)):
                                            isotopeTable[i]['nrIso']=nrIsoList[i]
                                        massI, propI = calculateSpecies(isotopeTable)
                                        fineStructure.append((massI,propI))
    return fineStructure




@njit
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



@njit
def calculateFineStructure(isotopePeak, isotopeTable):
    '''
    Calculates the isotopic fine structure of an isotope peak for molecules with an unspecific elemental composition
    :param (int) isotopePeak: number of the isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, no. of atoms of the element, no. of atoms of the isotope,
        rel. abundance of the isotope, mass of the isotope,
        nominal mass shift compared to the isotope with the lowest m/z)
    :return: (ndarray(dtype=[float,float])) final fine structure [(mass,percentage)]
    '''
    fineStructure = [(0.,0.)]
    for iFirst in list(range(isotopePeak + 1))[::-1]:
        isotopeTable[1]['nrIso'] = iFirst
        if iFirst == isotopePeak:
            massI, propI = calculateSpecies(isotopeTable)
            fineStructure.append((massI,propI))
        else:
            fineStructure = loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, 3)
    return fineStructure[1:]


@njit
def checkIsotopeTable(isotopeTable):
    for i in range(int(np.max(isotopeTable['index'])+1)):
        currentElements = getByIndex(isotopeTable,i)
        if np.sum(currentElements['nrIso'])> currentElements['nr'][0]:
            #print('no',isotopeTable)
            return False
    return True

@njit
def loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, index):
    '''
    Recursive function which loops through all possible isotope compositions for an isotope peak and calculates the
    isotopic fine structure:
    :param (int) isotopePeak: number of the isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, no. of atoms of the element, no. of atoms of the isotope,
        rel. abundance of the isotope, mass of the isotope,
        nominal mass shift compared to the isotope with the lowest m/z)
    :param (list[tuple[float,float]]) fineStructure: isotopic fine structure (tuples of (mass, rel. ab.))
    :param (int) index: current row index in the table
    :return: (list[tuple[float,float]]) final fineStructure [(mass,rel.abundance)]
    '''
    #if the isotope table for one isotope composition is finished
    if (np.sum(isotopeTable['nrIso']*isotopeTable['M+']) == isotopePeak):
        #check if the total no. of atoms of each element in the table is not higher than the ones in the molecular
        #formula
        if checkIsotopeTable(isotopeTable):
            massI, propI = calculateSpecies(isotopeTable)
            fineStructure.append((massI, propI))
        return fineStructure
    #if the isotope table is unfinished
    elif index < len(isotopeTable):
        '''for i in range(int((isotopePeak + isotopeTable[index]['M+']) / isotopeTable[index]['M+'])):
            if i>isotopeTable[index]['nr']:
                break
            isotopeTable[index]['nrIso'] = i
            loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, index + 1)'''
        #loop until the current row in the table does not correspond to a monoisotopic isotope
        while (isotopeTable[index]['M+'] == 0):
            index+=1
            #if the end of the table is reached
            if index >= len(isotopeTable):
                return fineStructure
        currentIso = isotopeTable[index]
        #loop over all possible isotope combinations
        for nrIso in range(int((isotopePeak + currentIso['M+']) / currentIso['M+'])):
            #break if the no. of the atoms of the current isotope is higher than the ones of the corresponding element
            if nrIso>currentIso['nr']:
                break
            #set no. of atoms of the current isotope in table
            isotopeTable[index]['nrIso'] = nrIso
            #loop to next isotope in the table
            loopThroughIsotopes(isotopePeak, isotopeTable, fineStructure, index + 1)
    return fineStructure

"""@njit
def calculatePoissonFineStructure(isotopePeak, isotopeTable, poissonElement):
    '''
    Calculates isotopic fine structure of isotope peak for molecules with a general elemental composition
    :param (int) isotopePeak: number of isotope peak (M+x)
    :type isotopeTable: ndarray(dtype=[float,float,float,float,float,float])
    :param isotopeTable: isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of
        isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
    :return: (ndarray(dtype=[float,float])) fine structure [(mass,percentage)]
    '''
    #print(isotopePeak)
    fineStructure = [(0.,0.)]
    oldIndex= 1
    monoVals = calculatePercentage(isotopeTable)
    for iFirst in list(range(isotopePeak + 1))[::-1]:
        #isotopeTable[1]['nrIso'] = iFirst
        #print('first',iFirst)
        if iFirst == isotopePeak:
            poissonVals = calculatePoissonPercentage(poissonElement, iFirst)
            #vals = calculatePercentage(isotopeTable)
            #val = np.array(calculatePercentage(isotopeTable))*calculatePoissonPercentage(poissonElement, iFirst)
            #print(isotopeTable['nrIso'])

            fineStructure.append((poissonVals[0]+monoVals[0], poissonVals[1]*monoVals[1]))
            print('hey',fineStructure[-1])
            oldIndex+= 1
        else:
            fineStructure = loopThroughIsotopes(isotopePeak-iFirst, isotopeTable, fineStructure, 0)
            #elements = isotopeTable[np.where(isotopeTable['M+']>1)]
            #fineStructure = loopThroughIsotopesNew(isotopePeak, isotopeTable, fineStructure, elements)
        val = calculatePoissonPercentage(poissonElement, iFirst)
        size = len(fineStructure)
        print('hey',val,iFirst,oldIndex,size)
        #fineStructure2 = [(0.,0.)]
        for i in range(oldIndex+1,size):
            print('vorher',fineStructure[i], monoVals[0])
            fineStructure[i] = (fineStructure[i][0] + val[0], fineStructure[i][1] * val[1])
            print('nachher',fineStructure[i], iFirst)
            '''if i>oldIndex:
                fineStructure2.append(fineStructure[i])
            else:
                fineStructure2.append((fineStructure[i][0] + val[0]))
                
            fineStructure[i][0] + val[0]
            fineStructure[i][1] += val[1]'''
        #print('hoho', fineStructure)
        oldIndex= size
    return fineStructure[1:]


@njit
def calculatePoissonPercentage(poissonElement, k):
    prop = poissonElement['lambda']**k / fact(k) * math.exp(-poissonElement['lambda'])
    return poissonElement['deltaMass']*k+poissonElement['monoMass'], prop

@njit
def fact(k):
    fact = 1
    for i in range(1,k+1):
        fact *= i
    return fact"""


"""def calculateFFTFineStructure(abundanceTable, formula):
    MAX_ELEMENTS = abundanceTable.shape[0]
    MAX_MASS = abundanceTable.shape[1]
    abundanceTable_trans = fft(abundanceTable, axis=1)
    ptA = np.ones(MAX_MASS, dtype=complex)
    for i in range(MAX_ELEMENTS):
        ptA *= (abundanceTable_trans[i, :] ** formula[i])
    riptA = ifft(ptA).real
    riptA/=np.sum(riptA)
    '''massTable_trans = fft(massTable, axis=1)
    ptM = np.zeros(MAX_MASS, dtype=complex)
    for i in range(MAX_ELEMENTS):
        ptM += (massTable_trans[i, :] ** formula[i])
    riptM = ifft(ptM).real'''

    masses = np.arange(1.0, MAX_MASS + 1, 1)#+riptM
    notZero = np.where(riptA >= 10e-10)
    #print(riptM[notZero])
    '''final = np.array([(mass_i, riptA_i) for mass_i, riptA_i in zip(masses[notZero],riptA[notZero])])
    print('j',[(mass_i, riptA_i) for mass_i, riptA_i in zip(masses[notZero],riptA[notZero])])
    #final.reshape((final.shape[0],2))'''
    return [(mass_i, riptA_i) for mass_i, riptA_i in zip(masses[notZero],riptA[notZero])]
    #return np.stack((masses[notZero], riptA[notZero]), axis = 1)"""

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

