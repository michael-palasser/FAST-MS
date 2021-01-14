from src.Entities.AbstractEntities import PatternWithItems, AbstractItem2
from src.Exceptions import InvalidInputException


class FragmentationPattern(PatternWithItems):
    def __init__(self, name, fragmentTypes, precursorFragments, id):
        super(FragmentationPattern, self).__init__(name, fragmentTypes,id)
        self.__items2 = precursorFragments

    def getItems2(self):
        return self.__items2


class FragItem(AbstractItem2):
    """def __init__(self, name, gain, loss, residue, radicals, enabled):
        super(FragItem, self).__init__(name, gain, loss, enabled)
        print("hey", name, gain, loss, residue, radicals, enabled)
        self._residue = residue
        self._radicals = radicals"""
    def __init__(self, item):
        print("hey",item)
        super(FragItem, self).__init__(name=item[0], gain=item[1], loss=item[2], enabled=item[5])
        self._residue = item[3]
        self._radicals = item[4]

    def getResidue(self):
        return self._residue

    def getRadicals(self):
        return self._radicals


    def check(self, elements, monomeres):
        for key in self.getFormula().keys():
            if key not in elements:
                raise InvalidInputException(self.getName(), "Element: "+ key + " unknown")
        #self._residue = residue  unchecked!
        try:
            self._radicals = int(self._radicals)
        except ValueError:
            raise InvalidInputException(self.getName(),"Number required: " +str(self._radicals))


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
