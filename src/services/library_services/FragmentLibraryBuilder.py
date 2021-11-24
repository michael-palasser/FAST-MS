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
from src.entities.SearchSettings import processTemplateName

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
        self.__sequence = properties.getSequence()
        self.__molecule = properties.getMolecule()
        self.__fragmentation = properties.getFragmentation()
        self.__modifPattern = properties.getModification()
        self.__maxMod = maxMod
        self._maxIso = maxIso
        self._accelerate = accelerate
        self.__fragmentLibrary = list()
        self.__precursor = None


    def getFragmentLibrary(self):
        return self.__fragmentLibrary

    def getPrecursor(self):
        return self.__precursor

    def setFragmentLibrary(self, patternReader):
        self.__fragmentLibrary = patternReader.addIsotopePatternFromFile(self.__fragmentLibrary)

    def buildSimpleLadder(self, sequ):
        '''
        Builds a sequenceList ladder of a basic fragment type
        :param (list[str]) sequ: sequenceList of precursor either from 5' or 3')
        :return: (dict[list[str],MolecularFormula]) the ladder (key=sequenceList(list), val=formula(MolecularFormula))
        '''
        simpleLadder = list()
        length = 1
        formula = MolecularFormula(dict())
        monomers = self.__molecule.getBBDict()
        for link in sequ:
            if link not in monomers.keys():
                logging.error("problem at "+ str(length)+', '+link+ ': building block unkown')
                raise InvalidInputException(link, 'building block unkown')
            formula = formula.addFormula(monomers[link].getFormula())
            simpleLadder.append((sequ[:length],formula))
            length += 1
        return simpleLadder


    @staticmethod
    def checkForResidue(residue, sequence):
        '''
        Checks if sequenceList contains a corresponding residue for residue-specific fragments
        :param (str) residue:
        :param (list[str]) sequence:
        :return: (bool)
        '''
        return (residue == '') or (residue == '-') or (residue in sequence)


    def checkForProlines(self, type, sequ, nextBB):
        '''
        No c- and z-fragments at proline. Function checks if corresponding amino acid is proline.
        :param (str) type: fragment type of fragment
        :param (list) sequ: sequenceList of fragment
        :param (str) nextBB: next building block in sequence
        :return: (bool) True for c- or z-fragments of proteins if corresponding amino acid is a proline, else: False
        '''
        if self.__sequence.getMolecule() == 'Protein':
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
        sequLength = len(self.__sequence.getSequenceList())
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
                if self.checkForResidue(template.getResidue(), linkSequ):
                    if (not formula.checkForNegativeValues()) and template.isEnabled():
                        ladder.append(Fragment(species, len(linkSequ), rest, formula, linkSequ,
                                               templateRadicals))
                        for nrMod in range(1, self.__maxMod + 1):
                            for modif in self.__modifPattern.getItems():
                                if modif.isEnabled():
                                    modifName = modif.getName()
                                    formula = linkFormula.addFormula(template.getFormula(),
                                                MolecularFormula(modif.getFormula()).multiplyFormula(nrMod).getFormulaDict())
                                    if self.checkForResidue(modif.getResidue(), linkSequ) and not formula.checkForNegativeValues()\
                                            and ((modifName+rest) not in self.__modifPattern.getExcluded()):
                                            #Constructor: type, number, modification, loss, formula
                                            if self.__maxMod > 1:
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
        sequence = self.__sequence.getSequenceList()
        sequenceName = self.__sequence.getName()
        species, mod = processTemplateName(self.__fragmentation.getPrecursor())
        precName=sequenceName
        if self.__maxMod == 1:
            precName += self.__modifPattern.getModification()
        elif self.__maxMod > 1:
            precName += self.__modifPattern.getModification()[0] +  str(self.__maxMod) + self.__modifPattern.getModification()[1:]
        precName+=mod
        basicFormula = simpleFormula.addFormula(self.__molecule.getFormula())
        for precTemplate in self.__fragmentation.getItems2():
            if precTemplate.isEnabled():
                #templateName = precTemplate.getName()
                species, templateName = processTemplateName(precTemplate.getName())
                #print(species, templateName)
                tempFormula = basicFormula.addFormula(precTemplate.getFormula())
                templateRadicals = precTemplate.getRadicals()
                newFragment = Fragment(sequenceName, 0, templateName, tempFormula, sequence, templateRadicals)
                precursorFragments.append(newFragment)
                if (sequenceName+templateName == precName):  #ToDo: check no Modification
                    self.__precursor = newFragment
                for nrMod in range(1, self.__maxMod + 1):
                    for modifTemplate in self.__modifPattern.getItems():
                        if modifTemplate.isEnabled():
                            modifName = modifTemplate.getName()
                            name = modifName + templateName
                            if self.__maxMod > 1:
                                name = modifName[0] + str(nrMod) + modifName[1:] + templateName
                            newFragment = Fragment(sequenceName, 0, name,tempFormula.addFormula(
                                    MolecularFormula(modifTemplate.getFormula()).multiplyFormula(nrMod).getFormulaDict()),
                                    sequence, templateRadicals+modifTemplate.getRadicals())
                            precursorFragments.append(newFragment)
                            #print(sequenceName+name,precName,sequenceName+name == precName)
                            if (sequenceName+name == precName):
                                self.__precursor = newFragment
        #[print(frag.getName(),frag.getRadicals()) for frag in precursorFragments]
        return precursorFragments
    

    def createFragmentLibrary(self):
        '''
        Creates the final fragment library (list of Fragments). Stored in self.__fragmentLibrary
        '''
        logging.info("********** Creating fragment library **********")
        if len(self.__modifPattern.getExcluded())>0:
            #print('These nrOfModifications are excluded:')
            logging.info('These nrOfModifications are excluded: '
                         +', '.join([elem for elem in self.__modifPattern.getExcluded()]))
            '''for elem in self.__modifPattern.getExcluded():
                print(elem)'''
        sequence = self.__sequence.getSequenceList()
        forwardFragments = self.createFragmentLadder(self.buildSimpleLadder(sequence), self.__fragmentation.getFragTemplates(1))
        simpleLadderBack = self.buildSimpleLadder(sequence[::-1])
        backwardFragments = self.createFragmentLadder(simpleLadderBack, self.__fragmentation.getFragTemplates(-1))
        precursorFragments = self.addPrecursor(simpleLadderBack[len(sequence) - 1][1])
        #for frag in precursorFragments:
        #    print(frag.getName(),frag.formula.toString())
        self.__fragmentLibrary = forwardFragments + backwardFragments + precursorFragments
        self.__fragmentLibrary.sort(key=lambda obj:(obj.getType() , obj.getNumber()))
        [logging.debug(fragment.getName()+': '+fragment.getFormula().toString()) for fragment in self.__fragmentLibrary]
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
        if self.__sequence.getMolecule() == 'Protein':
            criticalLength = 60
        if len(self.__sequence.getSequenceList())<criticalLength: #flag == 0:
            #self._bar = tqdm(total=len(self.__fragmentLibrary))
            logging.debug('Normal calculation')
            for fragment in self.__fragmentLibrary:
                #fragment.setIsotopePattern(fragment.getFormula().calculateIsotopePattern(self._maxIso))
                fragment.setIsotopePattern(fragment.getFormula().calculateIsotopePatternFFT(self._maxIso,self._accelerate))
                #print(fragment.getName())
                logging.info('\t'+fragment.getName())
                #self._bar.update(1)
                #self._fun()
        else:
            logging.debug('Parallel calculation')
            p = Pool()
            updatedFragmentLibrary = p.map(self.calculateParallel, self.__fragmentLibrary)
            self.__fragmentLibrary = sorted(updatedFragmentLibrary, key=lambda obj:(obj.getType() , obj.getNumber()))
        return self.__fragmentLibrary


    def calculateParallel(self, fragment):
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

