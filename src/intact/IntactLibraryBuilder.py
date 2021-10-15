'''
Created on 21 Jul 2020

@author: michael
'''
from multiprocessing import Pool

from src.MolecularFormula import MolecularFormula
from src.Services import IntactIonService, SequenceService, MoleculeService
from src.entities.IonTemplates import IntactModification
from src.entities.Ions import FragmentIon, Fragment, IntactNeutral


class IntactLibraryBuilder(object):
    '''
    Responsible for creating list of theoretical values of intact ions
    '''
    def __init__(self, sequName, modificationName):
        '''

        :param (str) sequName: Name of the Sequence
        :param (str) modificationName: Name of the Modification
        '''
        self._sequence = SequenceService().get(sequName)
        self._sequenceList = self._sequence.getSequenceList()
        self._molecule = MoleculeService().get(self._sequence.getMolecule())
        self._modifications = IntactIonService().getPatternWithObjects(modificationName, IntactModification)
        self._neutralLibrary = None


    def createLibrary(self, patternCalc=False):
        '''
        creates a library of modified ions
        :return: (list[IntactNeutral]) library of neutral molecules
        '''
        unmodFormula = self.getUnmodifiedFormula()
        sequName = self._sequence.getName()
        library = [IntactNeutral(sequName, '', 0, formula=unmodFormula)]
        for item in self._modifications.getItems():
            if item.isEnabled():
                modFormula = unmodFormula.addFormula(item.getFormula())
                library.append(IntactNeutral(sequName, item.getName(), item.getNrMod(), modFormula))
                #library[modName] = (modFormula.calculateMonoIsotopic(), nrOfMods)
        if patternCalc:
            p = Pool()
            p.map(self.calculateParallel, library)
            #library = sorted(updatedFragmentLibrary, key=lambda obj:(obj.getType() , obj.getNumber()))
        return library


    def getUnmodifiedFormula(self):
        '''
        Calculates molecular formula of unmodified intact ion
        :return: (MolecularFormula) formula of unmodified intact ion
        '''
        formula = MolecularFormula(self._molecule.getFormula())
        buildingBlocks = self._molecule.getBBDict()
        for link in self._sequenceList:
            formula = formula.addFormula(buildingBlocks[link].getFormula())
        return formula


    def addNewIsotopePattern(self):
        '''
        Calls calculateIsotopePattern() function (class MolecularFormula). Calculation is parallelized if length of
        (precursor) sequence is longer than criticalLength (depends on type of molecule)
        :param (Callable) fun:
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
        if len(self._sequence.getSequenceList())<criticalLength: #flag == 0:
            #self._bar = tqdm(total=len(self.__fragmentLibrary))
            #logging.debug('Normal calculation')
            for fragment in self.__fragmentLibrary:
                fragment.setIsotopePattern(fragment.getFormula().calculateIsotopePattern())
                #print(fragment.getName())
                #logging.info('\t'+fragment.getName())
                #self._bar.update(1)
                #self._fun()
        else:
            #logging.debug('Parallel calculation')
            p = Pool()
            updatedFragmentLibrary = p.map(self.calculateParallel, self.__fragmentLibrary)
            self.__fragmentLibrary = sorted(updatedFragmentLibrary, key=lambda obj:(obj.getType() , obj.getNumber()))
        return self.__fragmentLibrary


    def calculateParallel(self, neutral):
        '''
        Calculates the isotope pattern
        :type fragment: Fragment
        :param fragment: fragment without isotopePattern
        :return: (Fragment) fragment with isotopePattern
        '''
        neutral.setIsotopePattern(neutral.getFormula().calculateIsotopePattern())
        #print(fragment.getName())
        #logging.info('\t'+fragment.getName())
        #self._bar.update(1) does not work in python 3.8
        #self._fun()
        #return neutral