from src.entities.AbstractEntities import PatternWithItems, AbstractItem2, AbstractItem3


class FragmentationPattern(PatternWithItems):
    '''
    Class to store top-down fragment templates (including precursor ions)
    '''
    def __init__(self, name, precursor, fragmentTypes, precursorFragments, id):
        '''
        :param (str) name:
        :param (str) precursor: precursor name
        :type fragmentTypes: list[FragItem] | list[tuple[str,str,str,str,int|str,int, int] |
            list[list[str,str,str,str,int|str,int, int]]
        :param fragmentTypes: list of fragment templates
        :type precursorFragments: list[PrecursorItem] | list[tuple[str,str,str,str,int|str,int]] |
            list[list[str,str,str,str,int|str,int]]
        :param precursorFragments: list of precursor templates
        :param (int | None) id:
        '''
        super(FragmentationPattern, self).__init__(name, fragmentTypes,id)
        self.__precursor = precursor
        self.__items2 = precursorFragments

    def getPrecursor(self):
        return self.__precursor

    def getItems2(self):
        return self.__items2

    def setItems2(self, items):
        self.__items2 = items


    def getFragTemplates(self, direction):
        '''
        Returns FragItems for a given direction
        :param (int) direction: 1 for forward or -1 for backward
        :return: (list[FragItem]) filtered FragItems
        '''
        fragTemplates = []
        for item in self._items:
            if not isinstance(item, FragItem):
                item = FragItem(item)
            if item.getDirection() == direction:
                fragTemplates.append(item)
        return fragTemplates

    def toString(self):
        string = ''
        for item in self._items:
            if isinstance(item, FragItem):
                string += '\n\t' + '\t'.join(item.toString())
            else:
                string += '\n\t' + '\t'.join([str(val) for val in item])
        string += '\n\t-Precursor-Fragments:'
        for item in self.__items2:
            if isinstance(item, PrecursorItem):
                string += '\n\t' + '\t'.join(item.toString())
            else:
                string += '\n\t' + '\t'.join([str(val) for val in item])
        return string


class PrecursorItem(AbstractItem3):
    '''
    Template for precursor species
    '''
    def __init__(self, item):
        '''
        :param (tuple[str,str,str,str,int|str,int]) item: name, atomic gain, atomic loss, corresponding residue,
            number of radicals, enabled
        '''
        print(item)
        super(PrecursorItem, self).__init__(name=item[0], gain=item[1], loss=item[2],
                                            residue=item[3], radicals=item[4], enabled=item[5])


class FragItem(AbstractItem3):
    '''
    Template for fragments
    '''
    def __init__(self, item):
        '''
        :param (tuple[str,str,str,str,int|str,int, int] | list[str,str,str,str,int|str,int, int]) item:
            name, atomic gain, atomic loss, corresponding residue, number of radicals, direction of the fragment
            (+1 or -1), enabled
        '''
        item = self.processItem(item)
        super(FragItem, self).__init__(name=item[0], gain=item[1], loss=item[2],
                                            residue=item[3], radicals=item[4], enabled=item[6])
        self.__direct = item[5]

    def getDirection(self):
        return self.__direct

    def toString(self):
        parentVals = super(FragItem, self).toString()
        return parentVals[0:-1]+[str(self.__direct), parentVals[-1]]


class ModificationPattern(PatternWithItems):
    '''
    Class to store modification/ligand templates
    '''
    def __init__(self, name, modification, listOfMod, exclusionList, id):
        '''
        :param (str) name: simple name for storage
        :param (str) modification: name of prime modification
        :type listOfMod: list[ModificationItem] | list[tuple[str,str,str,str,int|str,int|str, int, int] |
            list[list[str,str,str,str,int|str,int|str, int, int]]
        :param listOfMod: list of modification templates
        :param (list[tuple[str]] | list[list[str]]) exclusionList: list of modifications which should be ignored
        :param (int | None) id:
        '''
        super(ModificationPattern, self).__init__(name, listOfMod,id)
        self.__modification = modification
        self.__items2 = exclusionList

    def getModification(self):
        return self.__modification

    def setModification(self, modification):
        self.__modification=modification

    def getItems2(self):
        return self.__items2

    def getExcluded(self):
        excluded = []
        for tuple in self.getItems2():
            excluded.append(tuple[0])
        return excluded

    def toString(self):
        string = self.__modification
        for item in self._items:
            if isinstance(item, ModificationItem):
                string += '\n\t' + '\t'.join(item.toString())
            else:
                string += '\n\t' + '\t'.join([str(val) for val in item])
        string += '\n\t-Excluded:\n\t' + ', '.join([tup[0] for tup in self.__items2])
        return string


class ModificationItem(AbstractItem3):
    '''
    Template for modifications/ligands
    '''
    def __init__(self, item):
        '''
        :param (tuple[str,str,str,str,int|str,int|str, int, int]) item: name, atomic gain, atomic loss,
            corresponding residue, number of radicals, charge shifting effect by modification, flag if modification
            should be ignored when calculating occupancy, enabled
        '''
        item = self.processItem(item)
        super(ModificationItem, self).__init__(name=item[0], gain=item[1], loss=item[2],
                                               residue=item[3], radicals=item[4], enabled=item[7])
        self.__zEffect = item[5]
        self.__calcOccupancy = item[6]

    def getZEffect(self):
        return self.__zEffect

    def getCalcOccupancy(self):
        return self.__calcOccupancy

    def toString(self):
        parentVals = super(ModificationItem, self).toString()
        return parentVals[0:-1]+[str(self.__zEffect), str(self.__calcOccupancy), parentVals[-1]]


class IntactPattern(PatternWithItems):
    '''
    Class to store templates for intact ion search
    '''
    def __init__(self,  name, items, id):
        '''
        :param (str) name: name of the pattern
        :type items: list[IntactModification] | list[tuple[str,str,str,int,int]] | list[list[str,str,str,int,int]]
        :param items: list of modification templates
        :param (int | None) id:
        '''
        super(IntactPattern, self).__init__(name, items, id)


class IntactModification(AbstractItem2):
    '''

    '''
    def __init__(self, item):
        '''
        :param (tuple[str,str,str,int,int] | list[str,str,str,int,int]) item: name, atomic gain, atomic loss,
            nr. of modifications on object, enabled
        '''
        item = self.processItem(item)
        super(IntactModification, self).__init__(name=item[0], enabled=item[4], gain=item[1], loss=item[2])
        self._nrMod = item[3]

    def getNrMod(self):
        return self._nrMod


