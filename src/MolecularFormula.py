import copy

from src.FormulaFunctions import stringToFormula
from src.fastFunctions import *
#import src.simpleFunctions as sf
from src.services.DataServices import PeriodicTableService
from scipy.fft import fft, ifft

'''
Created on 3 Jul 2020

@author: michael
'''

periodicTableService = PeriodicTableService()
isoTableDtype= np.dtype([('index', float), ('nr', float), ('nrIso', float),('relAb',float), ('mass',float), ('M+',float)])
isoPatternDtype = np.dtype([('m/z',float),('calcInt', float)])
#MIN_SUM = 0.996

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

    def getPeriodicTable(self):
        return self._periodicTable

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


    def checkSystem(self, elements, theoElements):
        for elem in elements:
            if elem not in theoElements:
                return False
        return True


    def determineSystem(self):
        '''
        Determines the correct method for isotope pattern calculation and corresponding isotope table based on the formula
        :return: (Callable) method,  (ndarray(dtype=[float,float,float,float,float,float])) isotopeTable
        '''
        #elements = [key for key,val in self._formulaDict.items() if val>0]
        #if self.checkSystem(elements, {'C', 'H', 'N', 'O', 'P'}):
        if self._formulaDict.keys() == {'C', 'H', 'N', 'O', 'P'} or self._formulaDict.keys() == {'C', 'H', 'N', 'O'}:
            calculate = calculateNuclFineStructure
            isotopeTable = self.makeNucIsotopeTable()
        #elif self.checkSystem(elements, {'C', 'H', 'N', 'O', 'S'}):
        elif self._formulaDict.keys() == {'C', 'H', 'N', 'O', 'S'}:
            calculate = calculatePeptFineStructure
            isotopeTable = self.makeProteinIsotopeTable()
        else:
            calculate = calculateFineStructure
            isotopeTable = self.makeIsotopeTable()
        return calculate, isotopeTable


    def calculateIsotopePattern(self, minSum, maxIso=-1):
        '''
        Calculates isotope patterns based on molecular formulas
        :param (float) minSum: algorithm stops when sum of abundances reaches minSum
        :param (int) maxIso: maximum isotope peak that is calculated
        :return: (ndarray(dtype=[float,float])) isotope pattern (structured numpy array: [(mass,relative Abundance)])
        '''
        #mostAbundant=10**(-10)
        #prop = 1
        isoPeak=0
        isotope_pattern = list()
        calculate, isotopeTable = self.determineSystem()
        sumInt = 0
        while(sumInt < minSum and isoPeak != maxIso):
            setIsotopeTable(isotopeTable)
            #print(isoPeak, isotopeTable)
            ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
            #print(isoPeak,len(ultrafineStruct))
            prop = np.sum(ultrafineStruct[:,1])
            M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
            isotope_pattern.append((M_iso,prop))
            isoPeak += 1
            sumInt += prop
            #if prop > mostAbundant:
                #mostAbundant = prop
            """if args and args[0]:
                if isoPeak == args[0]:
                    return np.array(isotope_pattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])"""
        return np.array(isotope_pattern, dtype=isoPatternDtype)



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
        return np.array(isotopeTable, dtype = isoTableDtype)


    def makeProteinIsotopeTable(self):
        '''
        Creates an isotope table for elemental composition CHNOS (proteins)
        :return: (ndarray(dtype=[float,float,float,float,float,float])) isotope table:
            isotope table for peptides (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance
            of isotope, mass of isotope, nominal mass shift compared to isotope with lowest m/z)
        '''
        isotopeTable = list()
        for index, elem in enumerate(['C','H','N','O','S']):
            if elem in self._periodicTable.keys():
                mono = self._periodicTable[elem][0][0]
                for isotope in self._periodicTable[elem]:
                    isotopeTable.append((index, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - mono))
        return np.array(isotopeTable, dtype = isoTableDtype)


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
                                , dtype=isoTableDtype)
        """isotopeTable = np.array(isotopeTable
                                , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                         ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])"""
        if len(getByIndex(isotopeTable, isotopeTable['index'][0])) != 2:
            isotopeTable = self.reorderTable(isotopeTable)
        return isotopeTable

    @staticmethod
    def reorderTable(isotopeTable):
        '''
        Reorders isotopeTable such that first element is a M+1 element
        :param (ndarray(dtype=[float,float,float,float,float,float])) isotopeTable: "raw" isotopeTable
        :return: (ndarray(dtype=[float,float,float,float,float,float])) reordered isotopeTable
        '''
        match = None
        for isotope in isotopeTable:
            if len(getByIndex(isotopeTable, isotope['index'])) == 2:
                match = isotope
                break
        if match is None:
            for isotope in isotopeTable:
                if len(getByIndex(isotopeTable, isotope['index'])) > 1:
                    match = isotope
                    break
        if match is None:
            return isotopeTable
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
            monoisotopic += val*self._periodicTable[elem][0][1]
        return monoisotopic


    def makeFFTTables(self,monoMass):
        '''
        Creates an array with the abundances of each isotope, an array with the nrs of each element and estimates the
        spacing between the isotope peaks (in Da). For universal elemental composition.
        :param (float) monoMass: monoisotopic mass of the molecule
        :return:
            (ndarray(dtype=[float,])) abundance table (2D array, each row represents an element, column index represents
                the number of nucleons;
            (ndarray(dtype=[float])) nr. of each element in the formula (1D array, each row represents an element);
            (float) estimated spacing between the isotope peaks
        '''
        maxMass = int(monoMass)+100
        elements = [elem for elem, val in self._periodicTable.items() if self._formulaDict[elem] > 0]
        numElements = len(elements)
        abundanceTable = np.zeros((numElements,maxMass))
        elemNrs = np.zeros(numElements)
        dm = []
        for i,elem in enumerate(elements):
            mono = self._periodicTable[elem][0]
            elemNrs[i] = self._formulaDict[elem]
            for isotope in self._periodicTable[elem]:
                if self._formulaDict[elem] != 0:
                    abundanceTable[i][isotope[0]] = isotope[2]
                    if isotope[0]-mono[0] != 0:
                        dm_i = isotope[1]-mono[1]
                        dm.append((dm_i/round(dm_i)*elemNrs[i]*isotope[2],elemNrs[i]*isotope[2]))
                        #intDm = round(dm_i)
                        #dm.append(((dm_i-intDm)*elemNrs[i]*isotope[2]/intDm,  elemNrs[i]*isotope[2]/intDm))
                        #print('dm',intDm,dm_i/round(dm_i), 1+(dm_i-intDm))
        dm =np.array(dm)
        return abundanceTable, elemNrs, np.sum(dm[:,0])/np.sum(dm[:,1])


    def calculateIsotopePatternFFT(self, minSum, accelerate, exactPattern=None):#, minSumCorrection=0):
        '''
        Calculates isotope patterns based on molecular formulas using a combination of the usual polynomial and the
        fast fourier transform method
        :param (float) minSum: algorithm stops when sum of abundances reaches minSum
        :param (int) accelerate: maximum isotope peak that is exactly calculated
        :param (ndarray(dtype=[float,float])) exactPattern: optional, exactly calculated isotope pattern (structured numpy array: [(mass,relative Abundance)])
        :return: (ndarray(dtype=[float,float])) isotope pattern (structured numpy array: [(mass,relative Abundance)])
        '''
        #assert minSumCorrection+MIN_SUM<1
        #print('new',self.calculateIsotopePattern(accelerate)[0])
        if exactPattern is None:
            exactPattern= self.calculateIsotopePattern(minSum, accelerate)
        if np.sum(exactPattern['calcInt']) > minSum:#+minSumCorrection:
            return np.array(exactPattern, dtype=isoPatternDtype)
        abundanceTable, elemNrs, dm = self.makeFFTTables(exactPattern['m/z'][0])
        isotope_pattern =  np.array(self.calculateAbundancesFFT(abundanceTable, elemNrs), dtype=isoPatternDtype)
        sumInt=np.sum(exactPattern['calcInt'])
        isoPeak = len(exactPattern)
        isotope_pattern['m/z'] =(isotope_pattern['m/z']-isotope_pattern['m/z'][isoPeak-1])*dm+exactPattern['m/z'][-1]
        finalPattern = [row for row in exactPattern]
        while sumInt <minSum:#+minSumCorrection:
            finalPattern.append(isotope_pattern[isoPeak])
            sumInt+=isotope_pattern[isoPeak]['calcInt']
            isoPeak+=1
        return np.array(finalPattern, dtype=isoPatternDtype)

    @staticmethod
    def calculateAbundancesFFT(abundanceTable, elemNrs):
        '''
        Calculates the relative abundances of the isotope distribution based on molecular formulas using the fast
        fourier transform method
        :param (ndarray(dtype=[float,])) abundanceTable: 2D array, each row represents an element, column index
            represents the number of nucleons;
        :param (ndarray(dtype=[float])) elemNrs: nr. of each element in the formula (1D array, each row represents an
            element);
        :return: (list[(float,float)]) 2D list of (integer) masses and abundances
        '''
        MAX_ELEMENTS = abundanceTable.shape[0]
        MAX_MASS = abundanceTable.shape[1]
        transformedTable = fft(abundanceTable, axis=1)
        transformedAbundances = np.ones(MAX_MASS, dtype=complex)
        for i in range(MAX_ELEMENTS):
            transformedAbundances *= (transformedTable[i, :] ** elemNrs[i])
        abundances = ifft(transformedAbundances).real
        abundances/=np.sum(abundances)
        notZero = np.where(abundances >= 10e-10)
        return [(mass_i, riptA_i) for mass_i, riptA_i in zip(notZero[0]+1,abundances[notZero])]


    def calcIsotopePatternPart(self, nrIsoPeaks):
        '''
        Calculates a number of isotope peaks based on molecular formulas
        :param (int) nrIsoPeaks: nr of isotope peaks which should be calculated
        :return: (ndarray(dtype=[float,float])) isotope pattern (structured numpy array: [(mass,relative Abundance)])
        '''
        isotope_pattern = list()
        calculate, isotopeTable = self.determineSystem()
        for isoPeak in range(nrIsoPeaks):
            #sf.setIsotopeTable(isotopeTable)
            setIsotopeTable(isotopeTable)
            ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
            prop = np.sum(ultrafineStruct[:,1])
            M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
            isotope_pattern.append((M_iso,prop))
        return np.array(isotope_pattern, dtype=isoPatternDtype)


    """CIsotopes = np.array([(12,12.0, 0.98938), (13, 13.0033548350723, 0.01078)])
    OIsotopes = np.array([(16,15.9949146195717,0.9975716),(17,16.9991317565069,0.000381),(18,17.9991596128676,0.0020514)])
    elements = [CIsotopes,OIsotopes]
    elementNrs = [20,30]
    for currentElement, N in zip(elements, elementNrs):
        print(N)
        I= len(currentElement)
    
        #if I>2:
        dimensionality = tuple([N+1 for i in range(I-1)])
        #else:
        #    dimensionality=(1,N+1)
        print('dim',dimensionality)
        E=np.zeros(dimensionality)
        dimList = [0 for dim in dimensionality]
        E[tuple(dimList)]=currentElement[0,2]
        for i in range(1,I):
            index = deepcopy(dimList)
            '''if len(index)==1:
                E[tuple(index)]=currentElement[i,2]
            else:'''
            index[-i]=1
            print('index1',index)
            print(index,currentElement[i,2])
            E[tuple(index)]=currentElement[i,2]
            print(E[tuple(index)])
        #E[0, 1] = currentElement[1, 2]
        print('E',E)
        #E_N = np.zeros(dimensionality)
        #E_N[tuple(dimList)]=currentElement[0,2]
        fftArrs = []
        if I==2:
            result = ifft(fft(E) ** N).real
            result /= np.sum(result)
            print('result',result)
            continue
        elif I==3:
            result1= np.zeros(dimensionality, dtype=complex)
            for i,row in enumerate(E):
                result1[i,:] = fft(row)
            result2= np.zeros(dimensionality, dtype=complex)
            result= np.zeros(dimensionality, dtype=complex)
            for i,col in enumerate(result1.T):
                result2[i,:] = ifft(fft(col)**N)
            for i,row in enumerate(result2.T):
                result[i,:] = ifft(row)
            result = result.real
            result /= np.sum(result)
            print('result',result.real)
            continue"""

    """def makeFFTCorrectionTable(self,neutralPattern):
        '''
        Creates an array with the abundances of each isotope, an array with the nrs of each element and estimates the
        spacing between the isotope peaks (in Da). For universal elemental composition.
        :param (float) monoMass: monoisotopic mass of the molecule
        :return:
            (ndarray(dtype=[float,])) abundance table (2D array, each row represents an element, column index represents
                the number of nucleons;
            (ndarray(dtype=[float])) nr. of each element in the formula (1D array, each row represents an element);
            (float) estimated spacing between the isotope peaks
        '''
        maxMass = int(np.max(neutralPattern['m/z']))+2
        abundanceTable = np.zeros((2,maxMass))
        for i,line in enumerate(sorted(neutralPattern['calcInt'])):
            abundanceTable[0][100+i] = line
        abundanceTable[1][1] = self._periodicTable['H'][2]
        return abundanceTable 
    
    def correctNeutralIsotopePattern(self, neutralPattern, charge):
        abundanceTable=self.makeFFTCorrectionTable(neutralPattern)
        self.calculateAbundancesFFT(neutralPattern, )"""






    '''def makePoissonTable(self):
        lamdaHNOS = 0
        massShiftHNOS = 0
        isotopeTable = list()
        index = 1
        for elem in ['C','H','N','O','S','P']:
            if elem in self._periodicTable.keys():
                mono = self._periodicTable[elem][0][0]
                if elem in ('H','N','O','S'):
                    monoMass = self._periodicTable[elem][0][1]
                    nr = self._formulaDict[elem]

                    for isotope in self._periodicTable[elem]:
                        if isotope[0]-mono==1:
                            isotope = 
                    p=isotope[2]
                    new_p = nr * p
                    lamdaHNOS += new_p
                    massShiftHNOS += new_p * (isotope[0] - monoMass)
                else:    
                    for isotope in self._periodicTable[elem]:
                        isotopeTable.append((index, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - mono))'''



    """def calculatePoissonIsotopePattern(self, accelerate):
        '''
        Calculates isotope patterns based on molecular formulas
        :param (int) accelerate: isotopePeak from which the calculation should be accelerated
        :return: (ndarray(dtype=[float,float])) isotope pattern (structured numpy array: [(mass,relative Abundance)])
        '''
        #mostAbundant=10**(-10)
        #prop = 1
        np.set_printoptions(suppress=True)
        isoPeak=0
        isotope_pattern = list()
        calculate, isotopeTable = self.determineSystem()
        reducedTable, poissonElement = self.makePoissonTable()
        if poissonElement['nr']==0:
            return self.calculateIsotopePattern()
        sumInt = 0
        while(sumInt <MIN_SUM):              #ToDo:Parameter
            setIsotopeTable(isotopeTable)
            #print(isoPeak, isotopeTable)
            if isoPeak<accelerate:
                print('not now',isoPeak)
                ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
            else:
                ultrafineStruct = np.array(calculatePoissonFineStructure(isoPeak, reducedTable,poissonElement))
                print('MolForm',ultrafineStruct)
            prop = np.sum(ultrafineStruct[:,1])
            M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
            isotope_pattern.append((M_iso,prop))
            isoPeak += 1
            sumInt += prop
        return np.array(isotope_pattern, dtype=isoPatternDtype)


    def makePoissonTable(self):
        isotopeTable = list()
        elements = [elem for elem,val in self._periodicTable.items() if self._formulaDict[elem] > 0]
        lambda1 = 0
        massShift1 = 0
        nr1 = 0
        monoIsoMass = 0
        for index, elem in enumerate(sorted(elements)):
            monoNuc = self._periodicTable[elem][0][0]
            monoMassElem = self._periodicTable[elem][0][1]
            nr = self._formulaDict[elem]
            isotope1 = self._periodicTable[elem][1]
            if (nr>50) and (len(self._periodicTable[elem])==2) and (isotope1[0]-monoNuc==1) and (isotope1[2]<0.05): #isotope1[2]*15000<nr:# and (maxIso<3):
                #for isotope in self._periodicTable[elem]:
                #p=isotope1[2]
                #if (isotope[0]-monoNuc==1) and (p<0.05):
                monoIsoMass += monoMassElem*nr
                new_p = nr*isotope1[2]
                lambda1 += new_p
                massShift1 +=new_p*(isotope1[1]-monoMassElem)
                nr1 += nr
                    #else:
                    #    isotopeTable.append((index+1, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - monoNuc))
            else:
                for isotope in self._periodicTable[elem]:
                    #if self._formulaDict[elem] != 0:
                    isotopeTable.append((index+1, self._formulaDict[elem], 0, isotope[2], isotope[1], isotope[0] - monoNuc))
        #lastIndex = index+1
        #isotopeTable.append((lastIndex, 0, 0, lambda1, massShift1, -100))
        '''isotopeTable = np.array([(index+1, nr1, 0, lambda1, massShift1, -100)]
                                +sorted(isotopeTable,key=lambda tup: tup[1], reverse=True), dtype=isoTableDtype)'''
        '''isotopeTable = np.array(sorted(isotopeTable,key=lambda tup: tup[1], reverse=True)
                                , dtype=isoTableDtype)'''
        '''if len(getByIndex(isotopeTable, isotopeTable['index'][0])) != 2:
            isotopeTable = self.reorderTable(isotopeTable)'''
        '''isotopeTable = np.concatenate((isotopeTable, np.array([(lastIndex+1, nr1, 0, lambda1, massShift1, -100)], dtype=
                                                             isoTableDtype)), axis=0)'''

        isotopeTable = np.array(sorted(isotopeTable,key=lambda tup: tup[1], reverse=True)
                                , dtype=isoTableDtype)
        if len(getByIndex(isotopeTable, isotopeTable['index'][0])) != 2:
            isotopeTable = self.reorderTable(isotopeTable)
        poissonElement = np.array((nr1,monoIsoMass, lambda1,massShift1/lambda1),
                                  dtype=[('nr', float),('monoMass', float),('lambda',float), ('deltaMass',float)])
        return isotopeTable, poissonElement"""


