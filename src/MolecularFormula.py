import copy

from src.FormulaFunctions import stringToFormula
from src.fastFunctions import *
#import src.simpleFunctions as sf
from src.Services import PeriodicTableService

'''
Created on 3 Jul 2020

@author: michael
'''

periodicTableService = PeriodicTableService()
isoTableDtype= np.dtype([('index', float), ('nr', float), ('nrIso', float),('relAb',float), ('mass',float), ('M+',float)])
isoPatternDtype = np.dtype([('m/z',float),('calcInt', float)])

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

    def checkSystem(self, elements, theoElements):
        for elem in elements:
            if elem not in theoElements:
                return False
        return True

    def determineSystem(self):
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

    def calculateIsotopePattern(self, maxIso=-1):
        '''
        Calculates isotope patterns based on molecular formulas
        :return: (ndarray(dtype=[float,float])) isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        #mostAbundant=10**(-10)
        #prop = 1
        isoPeak=0
        isotope_pattern = list()
        calculate, isotopeTable = self.determineSystem()
        sumInt = 0
        while(sumInt <0.996 and isoPeak!=maxIso):              #ToDo:Parameter
            setIsotopeTable(isotopeTable)
            #print(isoPeak, isotopeTable)
            ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
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
        """iso = np.array(isotope_pattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])
        print(np.sum(iso['calcInt']))"""
        #[print(row[0],row[1]) for row in isotope_pattern]
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
            '''match = None
            for isotope in isotopeTable:
                if len(getByIndex(isotopeTable, isotope['index'])) == 2:
                    match = isotope
                    break
            if match is None:
                for isotope in isotopeTable:
                    if len(getByIndex(isotopeTable, isotope['index']))>1:
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
                row['index'] = index'''

        return isotopeTable

    @staticmethod
    def reorderTable(isotopeTable):
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



    def calculatePoissonIsotopePattern(self, accelerate):
        '''
        Calculates isotope patterns based on molecular formulas
        :param (int) accelerate: isotopePeak from which the calculation should be accelerated
        :return: (ndarray(dtype=[float,float])) isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
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
        while(sumInt <0.996):              #ToDo:Parameter
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
        return isotopeTable, poissonElement



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
        #self._periodicTable = periodicTableService.getElements(list(self._formulaDict.keys()))
        isotope_pattern = list()
        '''if self._formulaDict.keys() == {'C', 'H', 'N', 'O', 'P'}:
            print('normal')
            #calculate = sf.calculateNuclFineStructure
            calculate = calculateNuclFineStructure
            isotopeTable = self.makeNucIsotopeTable()
        elif self._formulaDict.keys() == {'C', 'H', 'N', 'O', 'S'}:
            #calculate = sf.calculatePeptFineStructure
            calculate = calculatePeptFineStructure
            isotopeTable = self.makeProteinIsotopeTable()
        else:
            #calculate = sf.calculateFineStructure
            calculate = calculateFineStructure
            isotopeTable = self.makeIsotopeTable()
        isotopeTable = isotopeTable.astype([('index',np.int32), ('nr',np.int32), ('nrIso',np.int32),
             ('relAb',np.float64), ('mass',np.float64), ('M+',np.int32)])'''
        calculate, isotopeTable = self.determineSystem()
        if args and args[0]:
            for isoPeak in range(args[0]):
                #sf.setIsotopeTable(isotopeTable)
                setIsotopeTable(isotopeTable)
                ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
                prop = np.sum(ultrafineStruct[:,1])
                M_iso = np.sum(ultrafineStruct[:,0]*ultrafineStruct[:,1])/prop
                isotope_pattern.append((M_iso,prop))
        else:
            #mostAbundant=10**(-10)
            #prop = 1
            isoPeak=0
            sumInt = 0
            while(sumInt <0.996):                           #ToDo:Parameter# ToDo:Parameter
                setIsotopeTable(isotopeTable)
                ultrafineStruct = np.array(calculate(isoPeak, isotopeTable))
                prop = np.sum(ultrafineStruct[:, 1])
                M_iso = np.sum(ultrafineStruct[:, 0] * ultrafineStruct[:, 1]) / prop
                isotope_pattern.append((M_iso, prop))
                isoPeak += 1
                sumInt += prop
                #if prop > mostAbundant:
                #    mostAbundant = prop
        #[print(row[0],row[1]) for row in isotope_pattern]
        return np.array(isotope_pattern, dtype=isoPatternDtype)


    def makeFFTTable(self,monoMass):
        '''
                Creates an isotope table for universal elemental composition
                :return: (ndarray(dtype=[float,float,float,float,float,float])) isotope table:
                    isotope table (index, nr. of atoms of element, nr. of atoms of isotope, rel. abundance of isotope,
                    mass of isotope, nominal mass shift compared to isotope with lowest m/z)
                '''
        maxMass = int(monoMass)+100
        elements = [elem for elem, val in self._periodicTable.items() if self._formulaDict[elem] > 0]
        numElements = len(elements)
        abundanceTable = np.zeros((numElements,maxMass))
        #massTable = np.zeros((numElements,maxMass))
        elemNrs = np.zeros(numElements)
        #averageMasses = np.zeros(numElements)
        #stdDevs = np.zeros(numElements)
        dm = []
        for i,elem in enumerate(elements):
            mono = self._periodicTable[elem][0]
            elemNrs[i] = self._formulaDict[elem]
            #averageMasses[i] = np.sum(self._periodicTable[elem][:,1]*self._periodicTable[elem][:,2])
            #stdDevs[i] =
            for isotope in self._periodicTable[elem]:
                # if self._formulaDict[elem] != 0:
                abundanceTable[i][isotope[0]] = isotope[2]
                if isotope[0]-mono[0] != 0:
                    dm_i = isotope[1]-mono[1]
                    dm.append((dm_i/round(dm_i)*elemNrs[i]*isotope[2],elemNrs[i]*isotope[2]))
                #massTable[i][isotope[0]] = isotope[1] - mono
        #print('av',averageMasses, np.sqrt(np.sum(elemNrs*averageMasses))/np.sqrt(np.sum(elemNrs*averageMasses.astype(int))))
        #sigmaFactor = np.sqrt(np.sum(elemNrs*averageMasses))/np.sqrt(np.sum(elemNrs*averageMasses.astype(int)))
        #avM = np.sum(elemNrs*averageMasses)
        dm =np.array(dm)
        return abundanceTable, elemNrs, np.sum(dm[:,0])/np.sum(dm[:,1])#, sigmaFactor, avM

    def calculateIsotopePatternFFT(self, accelerate):
        '''
        Calculates isotope patterns based on molecular formulas
        :return: (ndarray(dtype=[float,float])) isotope pattern1 (structured numpy array: [(mass,relative Abundance)])
        '''
        #mostAbundant=10**(-10)
        #prop = 1
        exactPattern= self.calculateIsotopePattern(accelerate)
        abundanceTable, elemNrs, dm = self.makeFFTTable(exactPattern['m/z'][0])
        #isotope_pattern = calculateFFTFineStructure(abundanceTable, elemNrs)
        isotope_pattern =  np.array(calculateFFTFineStructure(abundanceTable, elemNrs), dtype=isoPatternDtype)
        #print(calculateFFTFineStructure(abundanceTable, elemNrs))
        #isotope_pattern['m/z'] = (isotope_pattern['m/z']+(monoMass-isotope_pattern['m/z'][0]))
        #isotope_pattern['m/z'] = sigmaFactor*isotope_pattern['m/z'] + sigmaFactor*()
        sumInt=np.sum(exactPattern['calcInt'])
        isoPeak = len(exactPattern)
        print(exactPattern['m/z'][-1])
        isotope_pattern['m/z'] =(isotope_pattern['m/z']-isotope_pattern['m/z'][isoPeak-1])*dm+exactPattern['m/z'][-1]
        finalPattern = [row for row in exactPattern]
        while sumInt <0.996:
            print('hey',isotope_pattern[isoPeak])
            finalPattern.append(isotope_pattern[isoPeak])
            sumInt+=isotope_pattern[isoPeak]['calcInt']
            isoPeak+=1
        return np.array(finalPattern, dtype=isoPatternDtype)


