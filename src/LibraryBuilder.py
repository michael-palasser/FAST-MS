'''
Created on 21 Jul 2020

@author: michael
'''
import csv
import re
from abc import ABC
from multiprocessing import Pool

import numpy as np
from src.MolecularFormula import MolecularFormula
from src.entities.Fragment import Fragment

eMass = 5.48579909065 * 10**(-4)


def removeEmptyElements(rawList):
    newList = rawList
    while '' in newList:
        newList.remove('')
    return newList


class AbstractLibraryBuilder(ABC):
    '''
    Parent class of all library builders
    '''
    def __init__(self,precName, sequence, molecule, modification):
        '''
        Constructor
        :param precName: name of precursor (String)
        :param sequence: sequence (list)
        :param molecule: RNA / DNA ? P (String)
        :param modification: modification of precursor
        :return: void
        monomeres: dict (keys = monomeres (FASTA), values = formulas)
        precursorModifications: dict (keys = precursor modifications, values = formulas)
        '''
        self.precName = precName
        self.sequence = sequence
        self.molecule = molecule
        self.modification = modification
        self.monomers = dict()
        self.precursorModifications = dict()


    @staticmethod
    def stringToFormula(formulaString, formulaDict, sign):
        '''
        Converts a String to a formula - dict and adds or subtracts it to or from an original formula
        :param formulaString: String which should be converted to a formula
        :param formulaDict: "old" formula (dictionary)
        :param sign: +1 or -1 for addition or subtraction of formula to or from formulaDict
        :return: new formula (dict)
        '''
        for item in re.findall('[A-Z][^A-Z]*', formulaString):
            element = item
            number = 1
            match = re.match(r"([a-z]+)([0-9]+)", item, re.I)   #re.I: ignore case: ?
            if match:
                element = match.group(1)
                number = int(match.group(2))
            elif '-' in item:
                element = item[:item.find('-')]
                number = int(item[item.find('-'):])
                #print(element, number)
            if element in formulaDict:
                formulaDict[element] += number * sign
            else:
                formulaDict[element] = number * sign
        return formulaDict


    def readMoleculeFile(self, moleculeFile):
        '''
        reads and processes file which contains formulas of monomeres and precursor ions
        :param moleculeFile: (RNA.txt, DNA.txt, Protein.txt in Parameters - folder)
        :return: void
        '''
        mode = 'monomers'
        for line in moleculeFile:
            if line.startswith('#precursor ions'):
                mode = 'precIons'
            if line.startswith('#') or line == "\n":
                continue
            lineList = removeEmptyElements(line.rstrip().split('\t'))
            if mode == 'monomers':
                self.monomers[lineList[0]] = self.stringToFormula(lineList[1],dict(),1)
            elif mode == 'precIons':
                print(lineList[0])
                self.precursorModifications[lineList[0]] = self.stringToFormula(lineList[1], dict(), 1)



class FragmentLibraryBuilder(AbstractLibraryBuilder):
    '''
    Creates library for top-down fragments
    '''

    def __init__(self, precName, sequence, molecule, modification, maxMod):

        '''
        Constructor
        :param precName: name of precursor (String)
        :param sequence: sequence (list)
        :param molecule: RNA / DNA ? P (String)
        :param modification: modification of precursor
        :param maxMod: number of modifications on precursor
        forwardDict: dict of forward-fragments types (keys) and formulas
        backwardDict: dict of backward-fragments types (keys) and formulas
        removeList: list of fragments which should be removed
        fragmentLibrary: list of all fragments
        radicalDict: list of fragments which contain radicals
        '''
        super().__init__(precName, sequence, molecule,modification)
        self.maxMod = maxMod
        self.forwardDict = dict()
        self.backwardDict = dict()
        self.modificationDict = dict()
        self.removeList = list()
        self.fragmentLibrary = list()
        self.radicalDict = dict()


    def readFragmentationFile(self, file): #ToDo: what happens when number before mod?
        '''
        reads the fragment-templates and creates dicts
        :param file: file which contain fragment templates
        :return: void
        '''
        for line in file:
            line = line.rstrip()
            if line.startswith('#') or line == "":
                continue
            else:
                if line[0] in ['a','b','c','d']:
                    self.addToFragmentDict(line,self.forwardDict)
                elif line[0] in ['w','x','y','z']:
                    self.addToFragmentDict(line,self.backwardDict)
                elif line.startswith('+'):
                    name, formula, residue, zEffect = self.lineToFormula(line)
                    self.modificationDict[name] = (formula, residue,zEffect)    #ToDo: better solution, radicals in nrOfModifications?
                elif line.startswith('-+'):
                    line = line.rstrip()
                    self.removeList.append(line[1:])
                else:
                    print(line)
                    raise Exception("incorrect format in fragmentation File")


    def lineToFormula(self, line):
        '''
        Processes a correctly formatted line of the fragment-templates
        :param line: line to convert
        :return: name of fragment-type, formula-template (dict), residue, radicals/charge effect (for charged modifications/ligands)
        '''
        lineList= removeEmptyElements(line.split('\t'))
        formulaDict = self.stringToFormula(lineList[2], dict(),1)                   #gain
        formulaDict = self.stringToFormula(lineList[1], formulaDict,-1)                  #loss
        return lineList[0], formulaDict, lineList[3], lineList[4]


    def addToFragmentDict(self, line, fragmentDict):
        '''
        #ToDo Test
        Processes a correctly formatted line and adds it to the fragment-dictionary
        :param line: line of fragment-templates
        :param fragmentDict: processed line added to this dict
        :return: void
        '''
        name, formula, residue, radical = self.lineToFormula(line)
        fragmentDict[name] = (formula, residue, radical)
        if radical.isdigit():
            self.radicalDict[name] = int(radical)


    def buildBasicLadder(self, sequ):
        '''
        Builds a sequence ladder of a basic fragment type
        :param sequ: sequence of precursor (list) (either from 5' or 3')
        :return: the ladder (dict: key=sequence(list), val=formula(MolecularFormula))
        '''
        basicLadder = list()
        length = 1
        sumFormula = MolecularFormula(dict())
        for link in sequ:
            if link not in self.monomers.keys():
                print("problem at", length)
                raise Exception(link)
            sumFormula = sumFormula.addFormula(self.monomers[link])
            basicLadder.append((sequ[:length],sumFormula))
            length += 1
        return basicLadder


    @staticmethod
    def checkForResidue(residue, sequence):
        '''
        Checks if sequence contains a corresponding residue for residue-specific fragments
        :param residue: String
        :param sequence: list
        :return: boolean
        '''
        return (residue == '-') or (residue in sequence)


    def checkForProlines(self, type, sequ, basicLadder):
        '''
        No c- and z-fragments after a proline in sequence. Function checks if last amino acid is proline.
        :param type: fragment type of fragment
        :param sequ: sequence of fragment
        :param basicLadder: fragment ladder of a basic fragment type (see function buildBasicLadder)
        :return: 1 for c- or z-fragments of proteins if last amino acid in sequence is a proline, else: 0
        '''
        if self.molecule in ['protein', 'peptide', 'P']:
            if type == 'c' and sequ[-1] == 'P':  # ToDo: Hydroxyproline etc.
                return 1
            elif type == 'z' and basicLadder[len(sequ)][0][-1] == 'P':
                return 1
        return 0


    def createFragmentLadder(self, basicLadder,fragmentDict):
        '''
        Creates a fragment ladder
        :param basicLadder: fragment ladder of a basic fragment type (see function buildBasicLadder)
        :param fragmentDict: corresponding fragment dictionary (self.forwardDict, self.backwardDict)
        :return: ladder (list of Fragments)
        '''
        ladder = list()
        for link in basicLadder:
            #precursor ion handled later
            linkSequ = link[0]
            linkFormula = link[1]
            if len(linkSequ) == len(self.sequence):
                continue
            for fragmentKey,fragmentVal in fragmentDict.items():
                if self.checkForProlines(fragmentKey[0],linkSequ, basicLadder):
                    continue
                sumFormula = linkFormula.addFormula(fragmentVal[0])
                if self.checkForResidue(fragmentVal[1], linkSequ):
                    if not sumFormula.checkForNegativeValues():
                        ladder.append(Fragment(fragmentKey[0], len(linkSequ), fragmentKey[1:], sumFormula, linkSequ))
                    for nrMod in range(1,self.maxMod+1):
                        for modKey,modVal in self.modificationDict.items():
                            sumFormula = linkFormula.addFormula(
                                fragmentVal[0], MolecularFormula(modVal[0]).multiplyFormula(nrMod).formulaDict)
                            if self.checkForResidue(modVal[1], linkSequ) and not sumFormula.checkForNegativeValues()\
                                    and ((modKey+fragmentKey[1:]) not in self.removeList):
                                    #Constructor: type, number, modification, loss, formula
                                    if self.maxMod > 1:
                                        newFragment = Fragment(fragmentKey[0],len(linkSequ),
                                                               modKey[0]+str(nrMod)+modKey[1:] + fragmentKey[1:],
                                                               sumFormula,linkSequ)
                                    else:
                                        newFragment = Fragment(fragmentKey[0],len(linkSequ),modKey +fragmentKey[1:],
                                                               sumFormula, linkSequ)
                                    ladder.append(newFragment)
        return ladder


    #ToDo: adducts
    def addPrecursor(self, basicFormula):
        '''
        Calculates molecular formulas of precursor ions
        :param basicFormula: template to calculate formula of precursor
        :return: precursorFragments (list of Fragments)
        '''
        precursorFragments = list()
        for ionKey,ionVal in self.precursorModifications.items():
            if ionKey == 'start':
                ionKey = ""
                tempFormula = basicFormula
            elif ionKey[0]=='-':
                tempFormula = basicFormula.subtractFormula(ionVal)
            else:
                tempFormula = basicFormula.addFormula(ionVal)
            precursorFragments.append(Fragment(self.precName, 0, ionKey, tempFormula, self.sequence))
            for nrMod in range(1,self.maxMod+1):
                for modKey,modVal in self.modificationDict.items():
                    if self.maxMod > 1:
                        modName = modKey[0] + str(nrMod) + modKey[1:] + ionKey
                    else:
                        modName = modKey + ionKey
                    precursorFragments.append(Fragment(self.precName, 0, modName,
                                        tempFormula.addFormula(MolecularFormula(modVal[0])
                                                               .multiplyFormula(nrMod).formulaDict),self.sequence))
        return precursorFragments
    

    def createFragmentLibrary(self):
        '''
        Creates the final fragment library (list of Fragments). Stored in self.fragmentLibrary
        :return: void
        '''
        if len(self.removeList)>0:
            print('These nrOfModifications are excluded:')
            for elem in self.removeList:
                print(elem)
        forwardFragments = self.createFragmentLadder(self.buildBasicLadder(self.sequence),self.forwardDict)
        SimpleLadderBack = self.buildBasicLadder(self.sequence[::-1])
        backwardFragments = self.createFragmentLadder(SimpleLadderBack,self.backwardDict)
        precursorFragments = self.addPrecursor(SimpleLadderBack[len(self.sequence)-1][1].addFormula(self.precursorModifications['start']))
        self.fragmentLibrary = forwardFragments + backwardFragments + precursorFragments
        self.fragmentLibrary.sort(key=lambda obj:(obj.type , obj.number))
        """for fragment in self.fragmentLibrary:
            print(fragment.getName(), fragment.formula.toString())"""


    def addIsotopePatternFromFile(self, file):
        '''
        Reads and processes isotope patterns from existing file
        :param file: file with istope patterns (in folder Fragment_lists)
        :return: void
        '''
        isotopePatternDict = dict()
        reader = csv.reader(file)
        next(reader, None)
        isotopePattern = list()
        counter = 0
        for row in reader:
            if counter == 0:
                name = row[0]
                counter = 1
            if row[0] != '':  #ToDo: correct? or elif
                isotopePatternDict[name] = np.array(isotopePattern, dtype=[('mass',np.float64),('relAb', np.float64)])
                name = row[0]
                isotopePattern = list()
            isotopePattern.append((row[1], row[2]))
        isotopePatternDict[name] = np.array(isotopePattern, dtype=[('mass',np.float64),('relAb', np.float64)])
        for fragment in self.fragmentLibrary:
            try:
                fragment.isotopePattern = isotopePatternDict[fragment.getName()]
            except KeyError:
                print(fragment.getName(), "not found in file.")
                raise KeyError


    def addNewIsotopePattern(self):
        '''
        Calls calculateIsotopePattern() function (class MolecularFormula) and subtracts electron mass if fragment contains radicals
        :return: void
        '''
        if len(self.fragmentLibrary)<800:
            for fragment in self.fragmentLibrary:
                fragment.isotopePattern = fragment.formula.calculateIsotopePattern()
                if fragment.type in self.radicalDict:
                    fragment.isotopePattern['mass'] -= self.radicalDict[fragment.type] * eMass
                print(fragment.getName())
        else:
            p = Pool()
            updatedFragmentLibrary = p.map(self.calculateParallel, self.fragmentLibrary)
            self.fragmentLibrary = updatedFragmentLibrary


    def calculateParallel(self, fragment):
        fragment.isotopePattern = fragment.formula.calculateIsotopePattern()
        if fragment.type in self.radicalDict:
            fragment.isotopePattern['mass'] -= self.radicalDict[fragment.type] * eMass
        print(fragment.getName())
        return fragment


    def saveIsotopePattern(self, file):
        '''
        Saves calculated isotope patterns to a file
        :param file: csv-file in folder Fragment_lists
        :return: void
        '''
        np.set_printoptions(suppress=True)
        #M_max = 0
        fieldnames = ['ion', 'mass', 'Intensities']
        f_writer = csv.DictWriter(file, fieldnames=fieldnames)
        f_writer.writeheader()
        for fragment in self.fragmentLibrary:
            counter = 0  # for new rows
            for isotope in fragment.isotopePattern:
                if counter == 0:
                    #if M_max < isotope[0]:
                        #M_max = isotope[0]
                    #print(isotope[0])
                    f_writer.writerow({'ion': fragment.getName(), 'mass': np.around(isotope['mass'], 6), 'Intensities': np.around(isotope['relAb'], 7)})
                    counter += 1
                else:
                    f_writer.writerow({'ion': '', 'mass': np.around(isotope['mass'], 6), 'Intensities': np.around(isotope['relAb'], 7)})


    def getModificationMasses(self):
        '''
        Getter of modificationDict (masses as values, not MolecularFormulas)
        :return: modificationMasses
        '''
        modificationMasses = dict()
        for mod,formula in self.modificationDict.items():
            modificationMasses[mod] = MolecularFormula(formula[0]).calculateMonoIsotopic()
        return modificationMasses

    def getTypes(self):
        '''
        Getter of the fragment-types
        :return: fragment-types (list)
        '''
        typeSet = set()
        for name in self.forwardDict.keys():
            typeSet.add(name[0])
        for name in self.backwardDict.keys():
            typeSet.add(name[0])
        return list(typeSet)


    def getChargedModifications(self):  #ToDo: multiple mod.
        '''
        Finds and returns charged modifications
        :return: dict of chargedModifications (modification:charge)
        '''
        chargedModifications = dict()
        for mod,tup in self.modificationDict.items():
            if tup[2] != '-':
                try:
                    if tup[2][0] == '-':
                        chargedModifications[mod] = (-1) * float(tup[2][1:])
                    else:
                        chargedModifications[mod] = float(tup[2])
                except ValueError:
                    print("Bad formatting in modification file: charge effect of",mod,"=",tup[2])
                    raise ValueError
        #handle duplicates etc.
        for mod in chargedModifications.keys():
            for item in re.split('\+',mod):
                mod2 = '+'+item
                if (mod2 in chargedModifications.keys()) and (mod2 != mod):
                    chargedModifications[mod] -= chargedModifications[mod2]
        return chargedModifications



class ESI_LibraryBuilder(AbstractLibraryBuilder):
    '''
    AbstractLibraryBuilder for intact ion search
    #ToDo: comments
    '''
    def __init__(self,precName, sequence, molecule, modification):
        super().__init__(precName, sequence, molecule,modification)



    def getUnmodifiedFormula(self):
        formula = MolecularFormula(self.precursorModifications['start'])
        for link in self.sequence:
            if link not in self.monomers.keys():
                raise Exception(link, 'unknown')
            formula = formula.addFormula(self.monomers[link])
        return formula


    def createLibrary(self,modificationPattern):
        unmodFormula = self.getUnmodifiedFormula()
        library = {"" : (unmodFormula.calculateMonoIsotopic(),0)}
        for item in modificationPattern.getItems():
            """if line.startswith('#'):
                continue
            lineList = removeEmptyElements(line.rstrip().split('\t'))
            if lineList == []:
                continue
            if lineList[0] == self.modification:
                formulaDict = self.stringToFormula(lineList[3], dict(), 1)  # gain
                formulaDict = self.stringToFormula(lineList[2], formulaDict, -1)  # loss"""
            if item.getEnabeled():
                modFormula = unmodFormula.addFormula(item.getFormula())
                library[item.getName()] = (modFormula.calculateMonoIsotopic(),item.getNrMod())
        return library

