from re import findall

from src.entities.AbstractEntities import PatternWithItems, AbstractItem1, AbstractPattern, AbstractItem2


class Makromolecule(PatternWithItems):
    def __init__(self, name, moleculeLoss, monomeres, id):
        super(Makromolecule, self).__init__(name, monomeres, id)
        self.__moleculeLoss = moleculeLoss

    def getMoleculeLoss(self):
        return self.__moleculeLoss

    def getLossFormula(self):
        return AbstractItem2.stringToFormula(self.__moleculeLoss, dict(), -1)

    def getMonomerDict(self):
        itemDict = dict()
        for item in self._items:
            itemDict[item[0]] = Monomere(item[0], item[1], item[2])
        return itemDict

class Monomere(AbstractItem1):
    def __init__(self, name, formulaString, acidity):
        super(Monomere, self).__init__(name)
        self.__formulaString = formulaString
        self.__acidity = acidity

    def getFormulaString(self):
        return self.__formulaString

    def getFormula(self):
        return self.stringToFormula(self.__formulaString,dict(),1)

    def getAcidity(self):
        return self.__acidity


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
    def __init__(self, pNr, mass, relAb):
        """

        :param pNr: proton number
        :param isoNr: M+isoNr (monoisotopic = M)
        :param mass:
        :param relAb:
        """
        self.__pNr = pNr
        #self.__isoNr = isoNr
        self.__mass = mass
        self.__relAb = relAb

    def getPNr(self):
        return self.__pNr

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
