from src.resources import processTemplateName
from src.services.DataServices import SequenceService, MoleculeService, FragmentationService, ModificationService
from src.entities.GeneralEntities import BuildingBlock
from src.entities.IonTemplates import FragItem, ModificationItem


class SearchSettings(object):
    '''
    Container class for storage of search properties (sequence, molecule, fragmentation pattern, modification pattern)
    '''
    def __init__(self, sequName,fragmentation, modificationPattern):
        '''
        Class to store several entities (sequence, fragmentation, modification-pattern)
        :param (str) sequName: name of the sequence
        :param (str) fragmentation: name of the fragmentation pattern
        :param (str) modificationPattern: name of the modification pattern
        '''
        self.__sequence = SequenceService().get(sequName)
        # self.sequenceList = self.__sequence.getSequenceList()
        self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        # self.__monomers = MoleculeService().getItemDict(self.__sequence.getMolecule())
        self.__fragmentation = FragmentationService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModificationItem)

    def getSequence(self):
        return self.__sequence

    def getSequenceList(self):
        return self.__sequence.getSequenceList()

    def getFragmentation(self):
        return self.__fragmentation

    def getModifPattern(self):
        return self.__modifPattern

    def getModificationName(self):
        return self.__modifPattern.getModification()

    def getMolecule(self):
        return self.__molecule

    def getP_chargedOfBBs(self, mode):
        return {name:bb.getP_charged(mode) for name,bb in self.__molecule.getBBDict().items()}

    def getChargedModifications(self):
        '''
        Finds and returns charged modifications
        :return: (dict[str,float]) chargedModifications (modification:charge)
        '''
        chargedModifications = dict()
        for modification in self.__modifPattern.getItems():
            if modification.getZEffect() != 0 and modification.getZEffect() != '-':
                chargedModifications[modification.getName()] = modification.getZEffect()
        return chargedModifications

    def getUnimportantModifs(self):
        '''
        Finds and returns modifications where the occupancy should be calculated
        :return: list[str] unimportant modifications
        '''
        return [modification.getName() for modification in self.__modifPattern.getItems()
                if not modification.getCalcOccupancy()]

    def getFragItemDict(self):
        '''
        Converts the list of fragment templates to a dict
        :return: (dict[str:FragItem]) dict of fragment templates {name:template}
        '''
        fragItemDict = dict()
        for fragTemplate in self.__fragmentation.getItems():
            fragItemDict[fragTemplate.getName()] = fragTemplate
        return fragItemDict

    def getFragmentsByDir(self, dir):
        '''
        Filters fragment templates by their direction
        :param (int) dir: desired direction of the fragment templates (1 for forward, -1 for backward)
        :return: (list[FragItem]) list of filtered fragment templates
        '''
        return {processTemplateName(fragTemplate.getName())[0] for fragTemplate in self.__fragmentation.getItems()
                if fragTemplate.getDirection() == dir}

    def filterByDir(self, fragDict, dir):
        '''
        Filters keys (fragment types) and their values (e.g. occupancies,...) by the direction of the fragment type
        :param (dict[str:Any]) fragDict: dict of {fragment-type: values}
        :param (int) dir: desired direction of the fragment templates (1 for forward, -1 for backward)
        :return: (dict[str:Any]) filtered dict of {fragment-type: values}
        '''
        return {key: val for key, val in fragDict.items() if key in self.getFragmentsByDir(dir)}

"""class IntactSearchSettings(object):
    '''
    Container class for storage of search properties (sequence, molecule, fragmentation pattern, modification pattern)
    '''
    def __init__(self, sequName, modificationPattern):
        '''
        Class to store several entities (sequence, fragmentation, modification-pattern)
        :param (str) sequName: name of the sequence
        :param (str) fragmentation: name of the fragmentation pattern
        :param (str) modificationPattern: name of the modification pattern
        '''
        self.__sequence = SequenceService().get(sequName)
        # self.sequenceList = self.__sequence.getSequenceList()
        self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        # self.__monomers = MoleculeService().getItemDict(self.__sequence.getMolecule())
        self.__modifPattern = IntactIonService().getPatternWithObjects(modificationPattern, IntactModification)

    def getSequence(self):
        return self.__sequence

    def getSequenceList(self):
        return self.__sequence.getSequenceList()

    def getModification(self):
        return self.__modifPattern

    def getModificationName(self):
        return self.__modifPattern.getModification()

    def getMolecule(self):
        return self.__molecule

    def getGPBsOfBBs(self, mode):
        return {name:bb.getGB(mode) for name,bb in self.__molecule.getBBDict().items()}"""