'''
Created on 21 Jul 2020

@author: michael
'''

from src.MolecularFormula import MolecularFormula
from src.Services import IntactIonService, SequenceService, MoleculeService
from src.entities.IonTemplates import IntactModification


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


    def createLibrary(self):
        '''
        creates a library of modified ions
        :return: (dict[str,MolecularFormula]) library of formulas {name:formula}
        '''
        unmodFormula = self.getUnmodifiedFormula()
        library = {"" : (unmodFormula.calculateMonoIsotopic(),0)}
        for item in self._modifications.getItems():
            if item.enabled():
                modFormula = unmodFormula.addFormula(item.getFormula())
                library[item.getName()] = (modFormula.calculateMonoIsotopic(),item.getNrMod())
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