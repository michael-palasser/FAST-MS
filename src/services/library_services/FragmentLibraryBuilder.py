'''
Created on 21 Jul 2020

@author: michael
'''
from multiprocessing import Pool
import logging
#from tqdm import tqdm

from src.Exceptions import InvalidInputException
from src.MolecularFormula import MolecularFormula
from src.entities.Ions import Fragment
from src.resources import processTemplateName

logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename='logfile_LibraryBuilder.log',level=logging.INFO)


class FragmentLibraryBuilder(object):
    '''
    Creates library for top-down fragments

    Attributes:
        fragmentLibrary: list of fragments
            :type list[Fragment]
        molecule:
    '''

    def __init__(self, properties, maxMod, maxIso=0.996, accelerate=20):
        '''
        :type properties: SearchSettings
        :param properties: propertyStorage of search
        :param (int) maxMod: number of modifications on precursor
        fragmentLibrary: list of all fragments
        precursor: Precursor fragment (type Fragment)
        '''
        self._sequence = properties.getSequence()
        self._molecule = properties.getMolecule()
        self._fragmentation = properties.getFragmentation()
        self._modifPattern = properties.getModifPattern()
        self._maxMod = maxMod
        self._maxIso = maxIso
        self._accelerate = accelerate
        self._fragmentLibrary = list()
        self._precursor = None


    def getFragmentLibrary(self):
        return self._fragmentLibrary

    def getPrecursor(self):
        if self._precursor.getIsotopePattern() is None:
            self._precursor.setIsotopePattern(self._precursor.getFormula().calculateIsotopePatternFFT(self._maxIso, 5))
        return self._precursor

    def setFragmentLibrary(self, patternReader):
        self._fragmentLibrary = patternReader.addIsotopePatternFromFile(self._fragmentLibrary)

    def buildSimpleLadder(self, sequ):
        '''
        Builds a sequenceList ladder of a basic fragment type
        :param (list[str]) sequ: sequenceList of precursor either from 5' or 3')
        :return: (dict[list[str],MolecularFormula]) the ladder (key=sequenceList(list), val=formula(MolecularFormula))
        '''
        simpleLadder = list()
        length = 1
        formula = MolecularFormula(dict())
        monomers = self._molecule.getBBDict()
        for link in sequ:
            if link not in monomers.keys():
                logging.error("problem at "+ str(length)+', '+link+ ': building block unkown')
                raise InvalidInputException(link, 'building block unkown')
            formula = formula.addFormula(monomers[link].getFormula())
            simpleLadder.append((sequ[:length],formula))
            length += 1
        return simpleLadder

    #ToDo: and or (momentan nur or)
    def checkForResidue(self, residues, sequence, forward=True):
        '''
        Checks if sequenceList contains a corresponding residue for residue-specific fragments
        :param (list[str]) residues: list of residue/building blocks that must be included
        :param (list[str]) sequence: list of bb strings
        :return: (bool)
        '''
        checked = False
        for residue in residues:
            if residue in ('', '-'):
                return True
            elif residue[-1]=='!':
                if residue[:-1] == sequence[-1]:
                    checked = True
            elif residue[-1]=='+':
                fullSequence = self._sequence.getSequenceList()
                if forward:
                    fullSequence = fullSequence[::-1]
                if residue[:-1] == fullSequence[len(fullSequence)-len(sequence)-1]:
                    checked = True
            elif residue in sequence:
                checked = True
        return checked
        #return (residue == '') or (residue == '-') or (residue in sequence)


    def checkForProlines(self, type, sequ, nextBB):
        '''
        No c- and z-fragments at proline. Function checks if corresponding amino acid is proline.
        :param (str) type: fragment type of fragment
        :param (list) sequ: sequenceList of fragment
        :param (str) nextBB: next building block in sequence
        :return: (bool) True for c- or z-fragments of proteins if corresponding amino acid is a proline, else: False
        '''
        if self._sequence.getMolecule() == 'Protein':
            if type == 'c' and nextBB == 'P':  # ToDo: Hydroxyproline etc.
                return True
            elif type == 'z' and sequ[-1]  == 'P':
                return True
        return False


    def createFragmentLadder(self, basicLadder, fragTemplates):
        '''
        Creates a fragment ladder in one direction (forward or backward)
        :param (list) basicLadder: fragment ladder of a basic fragment type (see function buildSimpleLadder)
        :type fragTemplates: FragItem
        :param fragTemplates: corresponding fragmentTemplate
        :return: (list[Fragment]) fragment ladder
        '''
        ladder = list()
        sequLength = len(self._sequence.getSequenceList())
        for link in basicLadder:
            #precursor ion handled later
            linkSequ = link[0]
            linkFormula = link[1]
            if len(linkSequ) == sequLength:
                continue
            for template in fragTemplates:
                #templateName = template.getName()
                species, rest = processTemplateName(template.getName())
                templateRadicals = template.getRadicals()
                #if self.checkForProlines(templateName[0],linkSequ, basicLadder):
                if self.checkForProlines(species,linkSequ, basicLadder[len(linkSequ)][0][-1]):
                    continue
                formula = linkFormula.addFormula(template.getFormula())
                forward = template.getDirection()==1
                if self.checkForResidue(template.getListOfResidues(), linkSequ,forward):
                    if (not formula.checkForNegativeValues()) and template.isEnabled():
                        ladder.append(Fragment(species, len(linkSequ), rest, formula, linkSequ,
                                               templateRadicals))
                        for nrMod in range(1, self._maxMod + 1):
                            for modif in self._modifPattern.getItems():
                                if modif.isEnabled():
                                    modifName = modif.getName()
                                    formula = linkFormula.addFormula(template.getFormula(),
                                                MolecularFormula(modif.getFormula()).multiplyFormula(nrMod).getFormulaDict())
                                    if self.checkForResidue(modif.getListOfResidues(), linkSequ,forward) and not formula.checkForNegativeValues()\
                                            and ((modifName+rest) not in self._modifPattern.getExcluded()):
                                            #Constructor: type, number, modification, loss, formula
                                            if self._maxMod > 1:
                                                modifName = modifName[0]+str(nrMod)+modifName[1:]
                                            #print(templateRadicals,modif.getRadicals())
                                            newFragment = Fragment(species,len(linkSequ),modifName+rest,
                                                           formula, linkSequ, templateRadicals+modif.getRadicals())
                                            '''if modif.getCalcOccupancy():
                                                self.__importantModifications.add(modifName+rest)'''
                                            ladder.append(newFragment)
        return ladder



    def addPrecursor(self, simpleFormula):
        '''
        Calculates molecular formulas of precursor ions
        :type simpleFormula: MolecularFormula
        :param simpleFormula: template to calculate formula of precursor
        :return: (list[Fragment]) precursorFragments (list of Fragments)
        '''
        precursorFragments = []
        sequence = self._sequence.getSequenceList()
        sequenceName = self._sequence.getName()
        species, mod = processTemplateName(self._fragmentation.getPrecursor())
        precName=sequenceName
        if self._maxMod == 1:
            precName += self._modifPattern.getModification()
        elif self._maxMod > 1:
            precName += self._modifPattern.getModification()[0] + str(self._maxMod) + self._modifPattern.getModification()[1:]
        precName+=mod
        basicFormula = simpleFormula.addFormula(self._molecule.getFormula())
        for precTemplate in self._fragmentation.getItems2():
            if precTemplate.isEnabled():
                #templateName = precTemplate.getName()
                species, templateName = processTemplateName(precTemplate.getName())
                #print(species, templateName)
                tempFormula = basicFormula.addFormula(precTemplate.getFormula())
                templateRadicals = precTemplate.getRadicals()
                newFragment = Fragment(sequenceName, 0, templateName, tempFormula, sequence, templateRadicals)
                precursorFragments.append(newFragment)
                if (sequenceName+templateName == precName):  #ToDo: check no Modification
                    self._precursor = newFragment
                for nrMod in range(1, self._maxMod + 1):
                    for modifTemplate in self._modifPattern.getItems():
                        if modifTemplate.isEnabled():
                            modifName = modifTemplate.getName()
                            name = modifName + templateName
                            if self._maxMod > 1:
                                name = modifName[0] + str(nrMod) + modifName[1:] + templateName
                            newFragment = Fragment(sequenceName, 0, name,tempFormula.addFormula(
                                    MolecularFormula(modifTemplate.getFormula()).multiplyFormula(nrMod).getFormulaDict()),
                                    sequence, templateRadicals+modifTemplate.getRadicals())
                            precursorFragments.append(newFragment)
                            #print(sequenceName+name,precName,sequenceName+name == precName)
                            if (sequenceName+name == precName):
                                self._precursor = newFragment
        #[print(frag.getName(),frag.getRadicals()) for frag in precursorFragments]
        return precursorFragments
    

    def createFragmentLibrary(self):
        '''
        Creates the final fragment library (list of Fragments). Stored in self.__fragmentLibrary
        '''
        logging.info("********** Creating fragment library **********")
        if len(self._modifPattern.getExcluded())>0:
            #print('These nrOfModifications are excluded:')
            logging.info('These nrOfModifications are excluded: '
                         +', '.join([elem for elem in self._modifPattern.getExcluded()]))
            '''for elem in self.__modifPattern.getExcluded():
                print(elem)'''
        sequence = self._sequence.getSequenceList()
        forwardFragments = self.createFragmentLadder(self.buildSimpleLadder(sequence), self._fragmentation.getFragTemplates(1))
        simpleLadderBack = self.buildSimpleLadder(sequence[::-1])
        backwardFragments = self.createFragmentLadder(simpleLadderBack, self._fragmentation.getFragTemplates(-1))
        precursorFragments = self.addPrecursor(simpleLadderBack[len(sequence) - 1][1])
        #for frag in precursorFragments:
        #    print(frag.getName(),frag.formula.toString())
        self._fragmentLibrary = forwardFragments + backwardFragments + precursorFragments
        self._fragmentLibrary.sort(key=lambda obj:(obj.getType() , obj.getNumber()))
        [logging.debug(fragment.getName()+': '+fragment.getFormula().toString()) for fragment in self._fragmentLibrary]
        #for fragment in self.__fragmentLibrary:
            #print(fragment.getName(), fragment.formula.toString())


    def addNewIsotopePattern(self):
        '''
        Calls calculateIsotopePattern() function (class MolecularFormula). Calculation is parallelized if length of
        (precursor) sequence is longer than criticalLength (depends on type of molecule)
        :return (list[Fragment]) list of fragments with isotope patterns
        '''
        """factor = 1
        if self.__sequence.getMolecule() == 'Protein':
            factor = 0.5
        if len(self.__sequence.getSequenceList()*factor<25):"""
        #self._fun = fun
        criticalLength = 30
        if self._sequence.getMolecule() == 'Protein':
            criticalLength = 60
        #criticalLength=10000
        if len(self._sequence.getSequenceList())<criticalLength: #flag == 0:
            logging.debug('Normal calculation')
            for fragment in self._fragmentLibrary:
                self.setIsotopePattern(fragment)
        else:
            logging.debug('Parallel calculation')
            p = Pool()
            updatedFragmentLibrary = p.map(self.setIsotopePattern, self._fragmentLibrary)
            self._fragmentLibrary = sorted(updatedFragmentLibrary, key=lambda obj:(obj.getType() , obj.getNumber()))
        return self._fragmentLibrary


    def setIsotopePattern(self, fragment):
        '''
        Calculates the isotope pattern
        :type fragment: Fragment
        :param fragment: fragment without isotopePattern
        :return: (Fragment) fragment with isotopePattern
        '''
        #fragment.setIsotopePattern(fragment.getFormula().calculateIsotopePattern(self._maxIso))
        fragment.setIsotopePattern(fragment.getFormula().calculateIsotopePatternFFT(self._maxIso,self._accelerate))
        logging.info('\t'+fragment.getName())
        #self._bar.update(1) does not work in python 3.8
        #self._fun()
        return fragment
