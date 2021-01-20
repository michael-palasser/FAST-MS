'''
Created on 21 Jul 2020

@author: michael
'''
import re
from multiprocessing import Pool

from src.MolecularFormula import MolecularFormula
from src.entities.Ions import Fragment
from src.entities.IonTemplates import FragItem, ModifiedItem, PrecursorItem
from src.Services import SequenceService, MoleculeService, FragmentIonService, ModificationService

E_MASS = 5.48579909065 * 10 ** (-4)

"""def removeEmptyElements(rawList):
    newList = rawList
    while '' in newList:
        newList.remove('')
    return newList"""


class FragmentLibraryBuilder(object):
    '''
    Creates library for top-down fragments
    '''

    def __init__(self, sequName, fragmentation, modificationPattern, maxMod):
        '''
        Constructor
        :param precName: name of precursor (String)
        :param __sequence: sequenceList (list)
        :param molecule: RNA / DNA ? P (String)
        :param modification: modification of precursor
        :param maxMod: number of modifications on precursor
        forwardDict: dict of forward-fragments types (keys) and formulas
        backwardDict: dict of backward-fragments types (keys) and formulas
        removeList: list of fragments which should be removed
        __fragmentLibrary: list of all fragments
        radicalDict: list of fragments which contain radicals
        '''
        self.__sequence = SequenceService().get(sequName)
        #self.sequenceList = self.__sequence.getSequence()
        self.__monomers = MoleculeService().getItemDict(self.__sequence.getMolecule())
        self.__fragmentation = FragmentIonService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModifiedItem)
        self.__maxMod = maxMod

        self.modificationDict = dict() #ToDelete
        self.removeList = list() #ToDelete
        self.__fragmentLibrary = list()
        self.radicalDict = dict() #ToDelete

    def getFragmentLibrary(self):
        return self.__fragmentLibrary

    def setFragmentLibrary(self, patternReader):
        self.__fragmentLibrary = patternReader.addIsotopePatternFromFile(self.__fragmentLibrary)

    def buildBasicLadder(self, sequ):
        '''
        Builds a sequenceList ladder of a basic fragment type
        :param sequ: sequenceList of precursor (list) (either from 5' or 3')
        :return: the ladder (dict: key=sequenceList(list), val=formula(MolecularFormula))
        '''
        basicLadder = list()
        length = 1
        sumFormula = MolecularFormula(dict())
        for link in sequ:
            if link not in self.__monomers.keys():
                print("problem at", length)
                raise Exception(link)
            sumFormula = sumFormula.addFormula(self.__monomers[link].getFormula())
            basicLadder.append((sequ[:length],sumFormula))
            length += 1
        return basicLadder


    @staticmethod
    def checkForResidue(residue, sequence):
        '''
        Checks if sequenceList contains a corresponding residue for residue-specific fragments
        :param residue: String
        :param sequence: list
        :return: boolean
        '''
        return (residue == '') or (residue == '-') or (residue in sequence)


    def checkForProlines(self, type, sequ, basicLadder):
        '''
        No c- and z-fragments after a proline in sequenceList. Function checks if last amino acid is proline.
        :param type: fragment type of fragment
        :param sequ: sequenceList of fragment
        :param basicLadder: fragment ladder of a basic fragment type (see function buildBasicLadder)
        :return: 1 for c- or z-fragments of proteins if last amino acid in sequenceList is a proline, else: 0
        '''
        if self.__sequence.getMolecule() == 'Protein':
            if type == 'c' and sequ[-1] == 'P':  # ToDo: Hydroxyproline etc.
                return 1
            elif type == 'z' and basicLadder[len(sequ)][0][-1] == 'P':
                return 1
        return 0


    def createFragmentLadder(self, basicLadder, fragTemplates):
        '''
        Creates a fragment ladder
        :param basicLadder: fragment ladder of a basic fragment type (see function buildBasicLadder)
        :param fragTemplates: corresponding fragment dictionary (self.forwardDict, self.backwardDict)
        :return: ladder (list of Fragments)
        '''
        ladder = list()
        for link in basicLadder:
            #precursor ion handled later
            linkSequ = link[0]
            linkFormula = link[1]
            if len(linkSequ) == len(self.__sequence.getSequence()):
                continue
            for template in fragTemplates:
                templateName = template.getName()
                if self.checkForProlines(templateName[0],linkSequ, basicLadder):
                    continue
                sumFormula = linkFormula.addFormula(template.getFormula())
                if self.checkForResidue(template.getResidue(), linkSequ):
                    if (not sumFormula.checkForNegativeValues()) and template.enabled():
                        ladder.append(Fragment(templateName[0], len(linkSequ), templateName[1:], sumFormula, linkSequ))
                        for nrMod in range(1, self.__maxMod + 1):
                            for modif in self.__modifPattern.getItems():
                                if modif.enabled():
                                    modifName = modif.getName()
                                    sumFormula = linkFormula.addFormula(template.getFormula(),
                                                    MolecularFormula(modif.getFormula()).multiplyFormula(nrMod).formulaDict)
                                    if self.checkForResidue(modif.getResidue(), linkSequ) and not sumFormula.checkForNegativeValues()\
                                            and ((modifName+templateName[1:]) not in self.__modifPattern.getExcluded()):
                                            #Constructor: type, number, modification, loss, formula
                                            if self.__maxMod > 1:
                                                newFragment = Fragment(templateName[0],len(linkSequ),
                                                                       modifName[0]+str(nrMod)+modifName[1:] + templateName[1:],
                                                                       sumFormula,linkSequ)
                                            else:
                                                newFragment = Fragment(templateName[0],len(linkSequ),modifName +templateName[1:],
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
        precursorFragments = []
        sequence = self.__sequence.getSequence()
        sequenceName = self.__sequence.getName()
        for precTemplate in self.__fragmentation.getItems2():
            templateName = precTemplate.getName()
            tempFormula = basicFormula.addFormula(precTemplate.getFormula())
            if precTemplate.enabled():
                precursorFragments.append(Fragment(sequenceName, 0, templateName, tempFormula, sequence))
                for nrMod in range(1, self.__maxMod + 1):
                    for modifTemplate in self.__modifPattern.getItems():
                        modifName = modifTemplate.getName()
                        name = modifName + templateName
                        if self.__maxMod > 1:
                            name = modifName[0] + str(nrMod) + modifName[1:] + templateName
                        precursorFragments.append(Fragment(sequenceName, 0, name,
                                       tempFormula.addFormula(MolecularFormula(modifTemplate.getFormula())
                                               .multiplyFormula(nrMod).formulaDict), sequence))
        return precursorFragments
    

    def createFragmentLibrary(self):
        '''
        Creates the final fragment library (list of Fragments). Stored in self.__fragmentLibrary
        :return: void
        '''
        if len(self.__modifPattern.getExcluded())>0:
            print('These nrOfModifications are excluded:')
            for elem in self.__modifPattern.getExcluded():
                print(elem)
        sequence = self.__sequence.getSequence()
        forwardFragments = self.createFragmentLadder(self.buildBasicLadder(sequence), self.__fragmentation.getFragTemplates(1))
        SimpleLadderBack = self.buildBasicLadder(sequence[::-1])
        backwardFragments = self.createFragmentLadder(SimpleLadderBack, self.__fragmentation.getFragTemplates(-1))
        precursorFragments = self.addPrecursor(SimpleLadderBack[len(sequence) - 1][1].addFormula(self.__fragmentation.getFormula()))
        self.__fragmentLibrary = forwardFragments + backwardFragments + precursorFragments
        self.__fragmentLibrary.sort(key=lambda obj:(obj.type , obj.number))
        """for fragment in self.__fragmentLibrary:
            print(fragment.getName(), fragment.formula.toString())"""


    def addNewIsotopePattern(self, flag):
        '''
        Calls calculateIsotopePattern() function (class MolecularFormula) and subtracts electron mass if fragment contains radicals
        :return: void
        '''
        """factor = 1
        if self.__sequence.getMolecule() == 'Protein':
            factor = 0.5
        if len(self.__sequence.getSequence()*factor<25):"""
        #if len(self.__fragmentLibrary)<800:
        if flag == 0:
            for fragment in self.__fragmentLibrary:
                fragment.isotopePattern = fragment.formula.calculateIsotopePattern()
                if fragment.type in self.radicalDict:
                    fragment.isotopePattern['mass'] -= self.radicalDict[fragment.type] * E_MASS
                print(fragment.getName())
        else:
            p = Pool()
            updatedFragmentLibrary = p.map(self.calculateParallel, self.__fragmentLibrary)
            self.__fragmentLibrary = sorted(updatedFragmentLibrary, key=lambda obj:(obj.type , obj.number))
        return self.__fragmentLibrary


    def calculateParallel(self, fragment):
        fragment.isotopePattern = fragment.formula.calculateIsotopePattern()
        if fragment.type in self.radicalDict:
            fragment.isotopePattern['mass'] -= self.radicalDict[fragment.type] * E_MASS
        print(fragment.getName())
        return fragment




    """def getModificationMasses(self):
        '''
        Getter of modificationDict (masses as values, not MolecularFormulas)
        :return: modificationMasses
        '''
        modificationMasses = dict()
        for mod,formula in self.modificationDict.items():
            modificationMasses[mod] = MolecularFormula(formula[0]).calculateMonoIsotopic()
        return modificationMasses"""

    """def getTypes(self): 
        '''
        Getter of the fragment-types
        :return: fragment-types (list)
        '''
        typeSet = set()
        for fragTemplate in self.__fragmentation.getFragTemplates():
            typeSet.add(fragTemplate.getName()[0])
        return list(typeSet)"""


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