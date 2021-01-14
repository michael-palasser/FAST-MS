from re import findall

from src.Entities.AbstractEntities import PatternWithItems, AbstractItem1, AbstractPattern


class Makromolecule(PatternWithItems):
    def __init__(self, name, monomeres, id):
        super(Makromolecule, self).__init__(name, monomeres, id)


class Monomere(AbstractItem1):
    def __init__(self, name, formulaString):
        super(Monomere, self).__init__(name)
        self.__formulaString = formulaString

    def getFormulaString(self):
        return self.__formulaString

    def getFormula(self):
        return self.stringToFormula(self.__formulaString,dict(),1)



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
        :param sequence: String
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

    def getSequence(self):
        return findall('[A-Z][^A-Z]*', self.__sequenceString)
