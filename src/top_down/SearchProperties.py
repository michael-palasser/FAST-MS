from src.Services import SequenceService, MoleculeService, FragmentIonService, ModificationService
from src.entities.GeneralEntities import BuildingBlock
from src.entities.IonTemplates import FragItem, ModifiedItem


class PropertyStorage(object):
    def __init__(self, sequName,fragmentation, modificationPattern):
        self.__sequence = SequenceService().get(sequName)
        # self.sequenceList = self.__sequence.getSequenceList()
        self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        # self.__monomers = MoleculeService().getItemDict(self.__sequence.getMolecule())
        self.__fragmentation = FragmentIonService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModifiedItem)

    def getSequence(self):
        return self.__sequence

    def getSequenceList(self):
        return self.__sequence.getSequenceList()

    def getFragmentation(self):
        return self.__fragmentation

    def getModification(self):
        return self.__modifPattern

    def getModificationName(self):
        return self.__modifPattern.getModification()

    def getMolecule(self):
        return self.__molecule

    def getGPBsOfBBs(self, mode):
        return {name:bb.getGB(mode) for name,bb in self.__molecule.getBBDict().items()}

    def getChargedModifications(self):
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
        return fragItemDict

    def getFragmentsByDir(self, dir):
        return [fragTemplate.getName() for fragTemplate in self.__fragmentation.getItems()
                if fragTemplate.getDirection() == dir]

    def filterByDir(self, fragDict, dir):
        return {key: val for key, val in fragDict.items() if key in self.getFragmentsByDir(dir)}