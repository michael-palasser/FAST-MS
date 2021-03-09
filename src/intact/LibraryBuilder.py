'''
Created on 21 Jul 2020

@author: michael
'''

from src.MolecularFormula import MolecularFormula
from src.Services import IntactIonService, SequenceService, MoleculeService
from src.entities.IonTemplates import IntactModification


class IntactLibraryBuilder(object):
    '''
    LibraryBuilder for intact ion search
    '''
    def __init__(self, sequName, modificationName):
        '''

        :param sequName: Name of the Sequence
        :param modificationName: Name of the Modification
        '''
        self.sequence = SequenceService().get(sequName)
        self.sequenceList = self.sequence.getSequenceList()
        self._molecule = MoleculeService().get(self.sequence.getMolecule())
        self.modifications = IntactIonService().getPatternWithObjects(modificationName, IntactModification)
        print('here')


    def createLibrary(self):
        '''
        creates a library of modified ions
        :return: dict of ions
        '''
        unmodFormula = self.getUnmodifiedFormula()
        library = {"" : (unmodFormula.calculateMonoIsotopic(),0)}
        for item in self.modifications.getItems():
            if item.enabled():
                modFormula = unmodFormula.addFormula(item.getFormula())
                print(item.getName(), modFormula.toString(), modFormula.calculateMonoIsotopic())
                library[item.getName()] = (modFormula.calculateMonoIsotopic(),item.getNrMod())
        return library


    def getUnmodifiedFormula(self):
        '''

        :return: unmodified intact ion
        '''
        formula = MolecularFormula(self._molecule.getFormula())
        buildingBlocks = self._molecule.getBBDict()
        for link in self.sequenceList:
            formula = formula.addFormula(buildingBlocks[link].getFormula())
        return formula