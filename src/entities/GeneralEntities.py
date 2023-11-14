from re import findall

from src.entities.AbstractEntities import PatternWithItems, AbstractItem1, AbstractPattern, AbstractItem2


rnaDict = {'G': 'R(G)P', 'U': 'R(U)P', 'C': 'R(C)P', 'A': 'R(A)P','Gms': '[mR](G)[sP]', 'Gm': '[mR](G)P', 'Um': '[mR](U)P', 'Cm': '[mR](C)P', 'Am': '[mR](A)P', 'Cf': '[fR](C)P', 'Uf': '[fR](U)P', 'Agalnac': '[Adem-GalNAc](A)P', 'Umps': '[MeMOP](U)[sP]', 'Gfs': '[fR](G)[sP]', 'Afs': '[fR](A)[sP]', 'Af': '[fR](A)P', 'Cms': '[mR](C)[sP]'}
aadict = {'A': 'Ala', 'Aib': 'Aib', 'C': 'Cys', 'D': 'Asp', 'E': 'Glu', 'F': 'Phe', 'G': 'Gly', 'H': 'His', 'I': 'Ile', 'K': 'Lys', 'Kbrac': 'Lys(bromoacetyl)', 'L': 'Leu', 'Q': 'Gln', 'R': 'Arg', 'S': 'Ser', 'T': 'Thr', 'V': 'Val', 'W': 'Trp', 'Y': 'Tyr', 'M': 'Met', 'N': 'Asn', 'O': 'Pyl', 'P': 'Pro', 'U': 'Sec'}


class Macromolecule(PatternWithItems):
    '''
    Class which stores molecule properties. E.g. protein, RNA, DNA
    '''
    def __init__(self, name, moleculeGain, moleculeLoss, buildingBlocks, id):
        '''
        :param (str) name: name of macromolecule
        :param (str) moleculeGain: template of formula (gain)
        :param (str) moleculeLoss: template of formula (loss)
        :param (list[tuple[str, str, float, float] | list[str, str, float, float] | BuildingBlock]) buildingBlocks:
            list of building blocks
        :param (int | None) id: id of macromolecule
        '''
        bbs = [list(bb) for bb in buildingBlocks]
        #if len(buildingBlocks[0])<5:
        bbs = [[bb[0],bb[1],bb[2]] for bb in buildingBlocks]
        super(Macromolecule, self).__init__(name, bbs, id)
        self.__gain = moleculeGain
        self.__loss = moleculeLoss


            

    def setItems(self, items):
        self._items = items

    def getGain(self):
        return self.__gain

    def getLoss(self):
        return self.__loss

    def getFormula(self):
        '''
        Returns template of molecular formula of macromolecule
        :return: (str) molecular formula
        '''
        formula = AbstractItem2.stringToFormula(self.__gain, dict(), 1)
        return AbstractItem2.stringToFormula(self.__loss, formula, -1)
    

    def getBBDict(self):
        '''
        Returns dict of building blocks
        :return (dict[str,BuildingBlock]) dict of {name of building block:BuildingBlock}
        '''
        itemDict = dict()
        for item in self._items:
            if isinstance(item, BuildingBlock):
                itemDict[item.getName()] = item
            else:
                itemDict[item[0]] = BuildingBlock(item)
        return itemDict

class BuildingBlock(AbstractItem1):
    '''
    e.g. guanidine for RNA, lysine for proteins
    '''
    #def __init__(self, name, formulaString, acidity):
    def __init__(self, item):
        '''
        :param (list[str, str, str, float, float] | tuple[str, str, str, float, float]) item:
            list of properties (name, formulaString, translation, gas-phase basicity (gb) in positive mode, gb in negative mode)
        '''
        super(BuildingBlock, self).__init__(item[0])
        #if len(item)==5:
            #raise NotImplementedError("Building Block Table not updated")
            #self.__translation = ""
            #self.__p_pos = item[2]
            #self.__p_neg = item[3]
        #else:
        self.__translation = item[1]
        self.__formulaString = item[2]
        """self.__p_pos = item[3]
        self.__p_neg = item[4]"""

    def getFormulaString(self):
        return self.__formulaString

    def getFormula(self):
        return self.stringToFormula(self.__formulaString,dict(),1)

    def getTranslation(self):
        return self.__translation
    def setTranslation(self, translation):
        self.__translation = translation

    """def getP_pos(self):
        return self.__p_pos
    def getP_neg(self):
        return self.__p_neg

    def setP_pos(self, p_pos):
        self.__p_pos = p_pos
    def setP_neg(self, p_neg):
        self.__p_neg = p_neg

    def getP_charged(self, mode):
        if mode> 0:
            return self.__p_pos
        return self.__p_neg"""


class Element(PatternWithItems):
    def __init__(self, name, isotopes, id):
        """
        :param (str) name: name of element
        :param (list[list[int, float, float] | list[tuple[int, float, float] | Isotope]) isotopes:
            list of isotopes (tuples of nucNr, mass, relAb)
        :param (int | None) id: id of element
        """
        super(Element, self).__init__(name, isotopes, id)


'''class Isotope(object):
    """
    wahrsch zu umstaendlich
    """
    def __init__(self, nucNr, mass, relAb):
        """

        :param (int) nucNr: number of nucleons
        :param (float) mass: mass of isotope
        :param (float) relAb: relative abundance of isotope
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
        return [self.__pNr, self.__isoNr, self.__mass, self.__relAb]"""'''




class Sequence(AbstractPattern):
    def __init__(self, name, sequenceString, molecule, id):
        """
        :param (str) name
        :param (str) sequenceString: sequence-string
        :param (str) molecule: RNA, DNA, P or other self defined macromolecule
        :param (int | None) id
        """
        super(Sequence, self).__init__(name, id)
        self.__sequenceString = sequenceString
        self.__molecule = molecule


    def getSequenceString(self):
        return self.__sequenceString

    def getMolecule(self):
        return self.__molecule

    def getSequenceList(self):
        '''
        Converts sequence string to list of building blocks (strings)
        :return list of str
        '''
        return findall('[A-Z][^A-Z]*', self.__sequenceString)
