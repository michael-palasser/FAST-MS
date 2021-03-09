from re import findall

from src.entities.AbstractEntities import PatternWithItems, AbstractItem1, AbstractPattern, AbstractItem2


class Makromolecule(PatternWithItems):
    def __init__(self, name, moleculeGain, moleculeLoss, monomeres, id):
        super(Makromolecule, self).__init__(name, monomeres, id)
        self.__gain = moleculeGain
        self.__loss = moleculeLoss

    def getGain(self):
        return self.__gain

    def getLoss(self):
        return self.__loss

    def getFormula(self):
        formula = AbstractItem2.stringToFormula(self.__gain, dict(), 1)
        return AbstractItem2.stringToFormula(self.__loss, formula, -1)

    def getBBDict(self):
        itemDict = dict()
        for item in self._items:
            if isinstance(item, BuildingBlock):
                itemDict[item.getName()] = item
            else:
                itemDict[item[0]] = BuildingBlock(item)
        return itemDict

class BuildingBlock(AbstractItem1):
    #def __init__(self, name, formulaString, acidity):
    def __init__(self, item):
        super(BuildingBlock, self).__init__(item[0])
        self.__formulaString = item[1]
        self.__gbP = item[2]
        self.__gbN = item[3]

    def getFormulaString(self):
        return self.__formulaString

    def getFormula(self):
        return self.stringToFormula(self.__formulaString,dict(),1)

    def getGbP(self):
        return self.__gbP

    def getGbN(self):
        return self.__gbN

    def getGB(self, mode):
        if mode == 1:
            return self.__gbP
        return self.__gbN


class Element(PatternWithItems):
    def __init__(self, name, isotopes, id):
        """

        :param name:
        :param isotopes: vorerst 2D list, dann (ToDo) 2D numpy array
        :param id:
        """
        super(Element, self).__init__(name, isotopes, id)


class Isotope(object):
    """
    wahrsch zu umstaendlich
    """
    def __init__(self, nucNr, mass, relAb):
        """

        :param nucNr: number of nucleons
        :param mass:
        :param relAb:
        """
        self.__nucNr = nucNr
        #self.__isoNr = isoNr
        self.__mass = mass
        self.__relAb = relAb

    def getPNr(self):
        return self.__nucNr

    """def getNr(self):
        return self.__isoNr"""

    def getMass(self):
        return self.__mass

    def getRelAb(self):
        return self.__relAb

    """def getAll(self):
        return [self.__pNr, self.__isoNr, self.__mass, self.__relAb]"""




class Sequence(AbstractPattern):
    def __init__(self, name, sequenceString, molecule, id):
        """
        :param name: String
        :param sequenceList: String
        :param molecule: String (RNA, DNA, P)
        :param pse: String (which periodic table should be applied)
        """
        super(Sequence, self).__init__(name, id)
        self.__sequenceString = sequenceString
        self.__molecule = molecule


    def getSequenceString(self):
        return self.__sequenceString

    def getMolecule(self):
        return self.__molecule

    def getSequenceList(self):
        return findall('[A-Z][^A-Z]*', self.__sequenceString)
