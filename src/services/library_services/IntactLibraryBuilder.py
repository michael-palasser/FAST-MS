'''
Created on 21 Jul 2020

@author: michael
'''
from multiprocessing import Pool

from src.MolecularFormula import MolecularFormula
from src.services.DataServices import IntactIonService, MoleculeService
from src.entities.IonTemplates import IntactModification
from src.entities.Ions import IntactNeutral


class IntactLibraryBuilder(object):
    '''
    Responsible for creating list of theoretical values of intact ions
    '''
    def __init__(self, sequence, modificationName, maxIso=0.996, accelerate=20):
        '''

        :param (str) sequName: Name of the Sequence
        :param (str) modificationName: Name of the Modification
        '''
        self._sequence = sequence
        self._sequenceList = self._sequence.getSequenceList()
        self._molecule = MoleculeService().get(self._sequence.getMolecule())
        self._modifications = IntactIonService().getPatternWithObjects(modificationName, IntactModification)
        self._maxIso = maxIso
        self._accelerate = accelerate
        self._neutralLibrary = None

    def getNeutralLibrary(self):
        return self._neutralLibrary
    def getSequence(self):
        self._sequence.getSequenceList()

    def createLibrary(self, patternCalc=False):
        '''
        creates a library of modified ions
        :param (bool) patternCalc: True if the isotope pattern should be calculated
        :return: (list[IntactNeutral]) library of neutral molecules
        '''
        unmodFormula = self.getUnmodifiedFormula()
        sequName = self._sequence.getName()
        self._neutralLibrary = [IntactNeutral(sequName, '', 0, unmodFormula, 0)]
        for item in self._modifications.getItems():
            if item.isEnabled():
                modFormula = unmodFormula.addFormula(item.getFormula())
                self._neutralLibrary.append(IntactNeutral(sequName, item.getName(), item.getNrMod(), modFormula, item.getRadicals()))
                #library[modName] = (modFormula.calculateMonoIsotopic(), nrOfMods)
        if patternCalc:
            p = Pool()
            p.map(self.calculateParallel, self._neutralLibrary)
            #library = sorted(updatedFragmentLibrary, key=lambda obj:(obj.getType() , obj.getNumber()))
        return self._neutralLibrary


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
        :return (list[IntactNeutral]) list of neutral species with isotope patterns
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
            for neutral in self._neutralLibrary:
                neutral.setIsotopePattern(neutral.getFormula().calculateIsotopePatternFFT(self._maxIso,self._accelerate))
                #neutral.setIsotopePattern(neutral.getFormula().calculateIsotopePattern(self._maxIso))
                #print(fragment.getName())
                #logging.info('\t'+fragment.getName())
                #self._bar.update(1)
                #self._fun()
        else:
            #logging.debug('Parallel calculation')
            p = Pool()
            updatedNeutralLibrary = p.map(self.calculateParallel, self._neutralLibrary)

            print(updatedNeutralLibrary)
            self._neutralLibrary = sorted(updatedNeutralLibrary, key=lambda obj:(obj.getName()))
        return self._neutralLibrary


    def calculateParallel(self, neutral):
        '''
        Calculates the isotope pattern
        :type neutral: IntactNeutral
        :param fragment: neutral species without isotopePattern
        :return: (IntactNeutral)  neutral species with isotopePattern
        '''
        neutral.setIsotopePattern(neutral.getFormula().calculateIsotopePatternFFT(self._maxIso,self._accelerate))
        #print(fragment.getName())
        #logging.info('\t'+fragment.getName())
        #self._bar.update(1) does not work in python 3.8
        #self._fun()
        return neutral

