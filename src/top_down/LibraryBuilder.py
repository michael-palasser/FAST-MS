'''
Created on 21 Jul 2020

@author: michael
'''
import re
from multiprocessing import Pool

from src.MolecularFormula import MolecularFormula
from src.entities.Ions import Fragment





class FragmentLibraryBuilder(object):
    '''
    Creates library for top-down fragments
    '''

    def __init__(self, properties, maxMod):
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
        '''self.__sequence = SequenceService().get(sequName)
        #self.sequenceList = self.__sequence.getSequenceList()
        self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        #self.__monomers = MoleculeService().getItemDict(self.__sequence.getMolecule())
        self.__fragmentation = FragmentIonService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModifiedItem)'''
        self.__sequence = properties.getSequence()
        self.__molecule = properties.getMolecule()
        self.__fragmentation = properties.getFragmentation()
        self.__modifPattern = properties.getModification()
        self.__maxMod = maxMod
        self.__fragmentLibrary = list()
        self.__precursor = None

    '''def getSequence(self):
        return self.__sequence

    def getSequenceList(self):
        return self.__sequence.getSequenceList()'''

    def getFragmentLibrary(self):
        return self.__fragmentLibrary

    def getPrecursor(self):
        return self.__precursor

    '''def getModification(self):
        return self.__modifPattern.getModification()'''

    def setFragmentLibrary(self, patternReader):
        self.__fragmentLibrary = patternReader.addIsotopePatternFromFile(self.__fragmentLibrary)

    '''def getMolecule(self):
        return self.__molecule'''

    def buildSimpleLadder(self, sequ):
        '''
        Builds a sequenceList ladder of a basic fragment type
        :param sequ: sequenceList of precursor (list) (either from 5' or 3')
        :return: the ladder (dict: key=sequenceList(list), val=formula(MolecularFormula))
        '''
        simpleLadder = list()
        length = 1
        formula = MolecularFormula(dict())
        monomers = self.__molecule.getBBDict()
        for link in sequ:
            if link not in monomers.keys():
                print("problem at", length)
                raise Exception(link)
            formula = formula.addFormula(monomers[link].getFormula())
            simpleLadder.append((sequ[:length],formula))
            length += 1
        return simpleLadder


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
        :param basicLadder: fragment ladder of a basic fragment type (see function buildSimpleLadder)
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
        :param basicLadder: fragment ladder of a basic fragment type (see function buildSimpleLadder)
        :param fragTemplates: corresponding fragment dictionary (self.forwardDict, self.backwardDict)
        :return: ladder (list of Fragments)
        '''
        ladder = list()
        for link in basicLadder:
            #precursor ion handled later
            linkSequ = link[0]
            linkFormula = link[1]
            if len(linkSequ) == len(self.__sequence.getSequenceList()):
                continue
            for template in fragTemplates:
                templateName = template.getName()
                templateRadicals = template.getRadicals()
                if self.checkForProlines(templateName[0],linkSequ, basicLadder):
                    continue
                formula = linkFormula.addFormula(template.getFormula())
                if self.checkForResidue(template.getResidue(), linkSequ):
                    if (not formula.checkForNegativeValues()) and template.enabled():
                        ladder.append(Fragment(templateName[0], len(linkSequ), templateName[1:], formula, linkSequ,
                                               templateRadicals))
                        for nrMod in range(1, self.__maxMod + 1):
                            for modif in self.__modifPattern.getItems():
                                if modif.enabled():
                                    modifName = modif.getName()
                                    formula = linkFormula.addFormula(template.getFormula(),
                                                    MolecularFormula(modif.getFormula()).multiplyFormula(nrMod).formulaDict)
                                    if self.checkForResidue(modif.getResidue(), linkSequ) and not formula.checkForNegativeValues()\
                                            and ((modifName+templateName[1:]) not in self.__modifPattern.getExcluded()):
                                            #Constructor: type, number, modification, loss, formula
                                            if self.__maxMod > 1:
                                                modifName = modifName[0]+str(nrMod)+modifName[1:]
                                            newFragment = Fragment(templateName[0],len(linkSequ),modifName+templateName[1:],
                                                           formula, linkSequ, templateRadicals+modif.getRadicals())
                                            ladder.append(newFragment)
        return ladder



    #ToDo: adducts
    def addPrecursor(self, simpleFormula):
        '''
        Calculates molecular formulas of precursor ions
        :param basicFormula: template to calculate formula of precursor
        :return: precursorFragments (list of Fragments)
        '''
        precursorFragments = []
        sequence = self.__sequence.getSequenceList()
        sequenceName = self.__sequence.getName()
        precName = "+" + self.__modifPattern.getModification()
        if self.__maxMod > 1:
            precName = "+" +  str(self.__maxMod) + self.__modifPattern.getModification()
        print(self.__molecule.getFormula())
        #return
        basicFormula = simpleFormula.addFormula(self.__molecule.getFormula())
        for precTemplate in self.__fragmentation.getItems2():
            if precTemplate.enabled():
                templateName = precTemplate.getName()
                tempFormula = basicFormula.addFormula(precTemplate.getFormula())
                templateRadicals = precTemplate.getRadicals()
                newFragment = Fragment(sequenceName, 0, templateName, tempFormula, sequence, templateRadicals)
                precursorFragments.append(newFragment)
                if (templateName == precName):  #ToDo: check no Modification
                    self.__precursor = newFragment
                for nrMod in range(1, self.__maxMod + 1):
                    for modifTemplate in self.__modifPattern.getItems():
                        if modifTemplate.enabled():
                            modifName = modifTemplate.getName()
                            name = modifName + templateName
                            if self.__maxMod > 1:
                                name = modifName[0] + str(nrMod) + modifName[1:] + templateName
                            newFragment = Fragment(sequenceName, 0, name,tempFormula.addFormula(
                                    MolecularFormula(modifTemplate.getFormula()).multiplyFormula(nrMod).formulaDict),
                                    sequence, templateRadicals+modifTemplate.getRadicals())
                            precursorFragments.append(newFragment)
                            if (name == precName):  #ToDo: check no Modification
                                self.__precursor = newFragment
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
        sequence = self.__sequence.getSequenceList()
        forwardFragments = self.createFragmentLadder(self.buildSimpleLadder(sequence), self.__fragmentation.getFragTemplates(1))
        SimpleLadderBack = self.buildSimpleLadder(sequence[::-1])
        backwardFragments = self.createFragmentLadder(SimpleLadderBack, self.__fragmentation.getFragTemplates(-1))
        precursorFragments = self.addPrecursor(SimpleLadderBack[len(sequence) - 1][1])
        for frag in precursorFragments:
            print(frag.getName(),frag.formula.toString())
        self.__fragmentLibrary = forwardFragments + backwardFragments + precursorFragments
        self.__fragmentLibrary.sort(key=lambda obj:(obj.type , obj.number))
        #for fragment in self.__fragmentLibrary:
            #print(fragment.getName(), fragment.formula.toString())


    def addNewIsotopePattern(self):
        '''
        Calls calculateIsotopePattern() function (class MolecularFormula) and subtracts electron mass if fragment contains radicals
        :return: void
        '''
        """factor = 1
        if self.__sequence.getMolecule() == 'Protein':
            factor = 0.5
        if len(self.__sequence.getSequenceList()*factor<25):"""
        #if len(self.__fragmentLibrary)<800:
        criticalLength = 30
        if self.__sequence.getMolecule() == 'Protein':
            criticalLength = 60
        if len(self.__sequence.getSequenceList())<criticalLength: #flag == 0:
            for fragment in self.__fragmentLibrary:
                fragment.isotopePattern = fragment.formula.calculateIsotopePattern()
                #if fragment.type in self.radicalDict:
                #fragment.isotopePattern['mass'] -= fragment.radicals * (E_MASS)
                print(fragment.getName())
        else:
            p = Pool()
            updatedFragmentLibrary = p.map(self.calculateParallel, self.__fragmentLibrary)
            self.__fragmentLibrary = sorted(updatedFragmentLibrary, key=lambda obj:(obj.type , obj.number))
        return self.__fragmentLibrary


    def calculateParallel(self, fragment):
        fragment.isotopePattern = fragment.formula.calculateIsotopePattern()
        #if fragment.type in self.radicalDict:
        #fragment.isotopePattern['mass'] -= fragment.radicals * E_MASS
        print(fragment.getName())
        return fragment


    """def getChargedModifications(self):
        '''
        Finds and returns charged modifications
        :return: dict of chargedModifications (modification:charge)
        '''
        chargedModifications = dict()
        for modification in self.__modifPattern.getItems():
            if modification.getZEffect() != 0:
                chargedModifications[modification.getName()] = modification.getZEffect()
        return chargedModifications

    
    def getImportantModifications(self):
        '''
        Finds and returns modifications where the occupancy should be calculated
        :return: dict of chargedModifications (modification:charge)
        '''
        importantModifications = []
        for modification in self.__modifPattern.getItems():
            if modification.getCalcOccupancy() == True:
                importantModifications.append(modification.getName())
        return importantModifications

    def getFragItemDict(self):
        fragItemDict = dict()
        for fragTemplate in self.__fragmentation.getItems():
            fragItemDict[fragTemplate.getName()] = fragTemplate
        return fragItemDict"""

    #ToDo
    """def selectFragmentsByDir(self, fragDict, dir):
        forwardFrags = [fragTemplate.getName() for fragTemplate in self.__fragmentation.getItems()
                            if fragTemplate.getDirection()==dir]
        return {key:val for key,val in fragDict.items() if key in forwardFrags}"""


    '''def getFragmentsByDir(self, dir):
        return [fragTemplate.getName() for fragTemplate in self.__fragmentation.getItems()
                            if fragTemplate.getDirection()==dir]

    def filterByDir(self, fragDict, dir):
        return {key: val for key, val in fragDict.items() if key in self.getFragmentsByDir(dir)}'''