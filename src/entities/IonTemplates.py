from src.entities.AbstractEntities import PatternWithItems, AbstractItem2, AbstractItem3


class FragmentationPattern(PatternWithItems):
    def __init__(self, name, fragmentTypes, precursorFragments, id):
        super(FragmentationPattern, self).__init__(name, fragmentTypes,id)
        #self.__initGain = gain
        #self.__initLoss = loss
        self.__items2 = precursorFragments


    '''def getInitGain(self):
        return self.__initGain

    def getInitLoss(self):
        return self.__initLoss'''

    '''def getFormula(self):
        formulaDict = AbstractItem2.stringToFormula(self.__initGain, dict(), 1)
        return AbstractItem2.stringToFormula(self.__initLoss, formulaDict, -1)'''

    def getItems2(self):
        return self.__items2

    def setItems2(self, items):
        self.__items2 = items

    """def getAttributes(self):
        return self._name, self.__initGain, self.__initLoss"""

    def getFragTemplates(self, direction):
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
            string += '\n\t' + ', '.join(item.toString())
        string += '\n\t-Precursor-Fragments:'
        for item in self.__items2:
            string += '\n\t' + ', '.join(item.toString())
        return string


class PrecursorItem(AbstractItem3):
    def __init__(self, item):
        super(PrecursorItem, self).__init__(name=item[0], gain=item[1], loss=item[2],
                                            residue=item[3], radicals=item[4], enabled=item[5])



    '''def check(self, elements, monomeres):
        for key in self.getFormula().keys():
            if key not in elements:
                raise UnvalidInputException(self.getName(), "Element: " + key + " unknown")
        # self._residue = residue  unchecked!
        try:
            self._radicals = int(self._radicals)
        except ValueError:
            raise UnvalidInputException(self.getName(), "Number required: " + str(self._radicals))'''


class FragItem(AbstractItem3):
    def __init__(self, item):
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
    def __init__(self, name, modification, listOfMod, exclusionList, id):
        super(ModificationPattern, self).__init__(name, listOfMod,id)
        self.__modification = modification
        self.__items2 = exclusionList

    def getModification(self):
        return self.__modification

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
            string += '\n\t' + ', '.join(item.toString())
        string += '\n\t-Excluded:\n\t' + ', '.join(self.__items2)
        return string


class ModifiedItem(AbstractItem3):
    def __init__(self, item):
        item = self.processItem(item)
        super(ModifiedItem, self).__init__(name=item[0], gain=item[1], loss=item[2],
                                            residue=item[3], radicals=item[4], enabled=item[7])
        self.__zEffect = item[5]
        self.__calcOccupancy = item[6]

    def getZEffect(self):
        return self.__zEffect

    def getCalcOccupancy(self):
        return self.__calcOccupancy

    def toString(self):
        parentVals = super(ModifiedItem, self).toString()
        return parentVals[0:-1]+[str(self.__zEffect), str(self.__calcOccupancy), parentVals[-1]]



class IntactPattern(PatternWithItems):
    def __init__(self,  name, items, id):
        super(IntactPattern, self).__init__(name, items, id)
        '''self.__initGain = gain
        self.__initLoss = loss'''

    '''def getInitGain(self):
        return self.__initGain

    def getInitLoss(self):
        return self.__initLoss'''

    '''def getFormula(self):
        formulaDict = AbstractItem2.stringToFormula(self.__initGain, dict(), 1)
        return AbstractItem2.stringToFormula(self.__initLoss, formulaDict, -1)
'''

class IntactModification(AbstractItem2):
    def __init__(self, item):
        item = self.processItem(item)
        super(IntactModification, self).__init__(name=item[0], enabled=item[4], gain=item[1], loss=item[2])
        self._nrMod = item[3]

    def getNrMod(self):
        return self._nrMod


