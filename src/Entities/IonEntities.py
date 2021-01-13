from src.Entities.AbstractEntities import PatternWithItems, AbstractItem2


class FragmentationPattern(PatternWithItems):
    def __init__(self, name, fragmentTypes, precursorFragments, id):
        super(FragmentationPattern, self).__init__(name, fragmentTypes,id)
        self.__items2 = precursorFragments

    def getItems2(self):
        return self.__items2


class FragItem(AbstractItem2):
    def __init__(self, name, gain, loss, residue, radicals, enabled):
        super(FragItem, self).__init__(name, gain, loss, enabled)
        self._residue = residue
        self._radicals = radicals

    def getResidue(self):
        return self._residue

    def getRadicals(self):
        return self._radicals



class ModificationPattern(PatternWithItems):
    def __init__(self, name, modification, listOfMod, exclusionList, id):
        super(ModificationPattern, self).__init__(name, listOfMod,id)
        self.__modification = modification
        self.__items2 = exclusionList

    def getModification(self):
        return self.__modification

    def getItems2(self):
        return self.__items2


class ModifiedItem(FragItem):
    def __init__(self,name, gain, loss, residue, radicals, zEffect, calcOccupancy, enabled):
        super(ModifiedItem, self).__init__(name, gain, loss, residue, radicals, enabled)
        self._calcOccupancy = calcOccupancy
        self.__zEffect = zEffect

    def getZEffect(self):
        return self.__zEffect



class IntactPattern(PatternWithItems):
    def __init__(self,  name, items, id):
        super(IntactPattern, self).__init__(name, items, id)

"""def getItemsAsList(self):
        _itemDict = dict()
        #_itemDict = {"Name":[], "Gain":[], "Loss":[], "NrOfMod":[], "enabled":[]}
        for item in self.__modifications:
            for key, val in item.items()
                if item not in
        return {"Name":[], "Gain", "Loss", "NrOfMod", "enabled"}"""


class IntactModification(AbstractItem2):
    def __init__(self, name, gain, loss, nrMod, enabled):
        super(IntactModification, self).__init__(name, enabled, gain, loss)
        self._nrMod = nrMod

    def getNrMod(self):
        return self._nrMod
