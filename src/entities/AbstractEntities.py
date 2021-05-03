import re
from abc import ABC

from src.FormulaFunctions import stringToFormula as MF_stringToFormula


#from src.Exceptions import InvalidInputException



class AbstractPattern(ABC):
    '''
    Parent class of Sequence, PatternWithItems
    '''
    def __init__(self, name, id):
        '''

        :param (str) name:
        :param (int) id:
        '''
        self._name = name
        self._id = id

    def getName(self):
        return self._name

    def getId(self):
        return self._id

    def setName(self, name):
        self._name = name

    def setId(self, id):
        self._id = id

class PatternWithItems(AbstractPattern):
    '''
    Parent class of Element, Macromolecule, FragmentationPattern, IntactPattern, ModificationPattern
    '''
    def __init__(self, name, items, id):
        """
        :param (str) name:
        :param (list[tuple[Any]]) items: either list of Item objects for AbstractLibraryBuilder or 2D list for views
        :param (int) id:
        """
        super(PatternWithItems, self).__init__(name, id)
        self._items = items  # list of dict of values

    def getItems(self):
        return self._items

    def setItems(self, items):
        self._items = items

    def getFormula(self):
        return dict()

class AbstractItem1(ABC):
    '''
    Parent class of BuildingBlock, AbstractItem2
    '''
    def __init__(self, name):
        '''
        :param (str) name:
        '''
        self._name = name

    def getName(self):
        return self._name

    @staticmethod
    def stringToFormula(formulaString, formulaDict, sign):
        '''
        Converts the a formula from string (can contain parenthesis) to dict
        :param (str) formulaString: string to be converted
        :param (dict[str:int]) formulaDict: initial formula dictionary
        :param (int) sign: +1 to add new formula to initial or -1 to subtract
        :return (dict[str:int]): new formula dictionary
        '''
        #everything in parenthesis
        '''beginIndizes = [m.start() for m in re.finditer('\(', formulaString)]
        endIndizes = [m.start() for m in re.finditer('\)', formulaString)]
        if len(beginIndizes) != len(endIndizes):
            raise InvalidInputException(formulaString, 'Incorrect use of parenthesis')
        #subString = formulaString[:beginIndizes[0]]
        #formulaDict = AbstractItem1.stringToFormula2(formulaString[:beginIndizes[0]], formulaDict, sign)
        #print(beginIndizes,endIndizes)
        lastEnd = 0
        for bI,eI in zip(beginIndizes,endIndizes):
            #print(formulaString[lastEnd:bI],formulaString[bI+1:eI])
            formulaDict = AbstractItem1.stringToFormula2(formulaString[lastEnd:bI], formulaDict, sign)
            temp = AbstractItem1.stringToFormula2(formulaString[bI+1:eI], {}, sign)
            if (len(formulaString)>eI+1) and (formulaString[eI+1].isnumeric()):
                nr = int(re.findall('\)\d+', formulaString[bI+1:])[0][1:])
                #print('nr',nr)
                temp = {key:val*nr for key,val in temp.items()}
            AbstractItem1.addToDict(formulaDict,temp)
            lastEnd = eI
        formulaDict = AbstractItem1.stringToFormula2(formulaString[lastEnd:],formulaDict,sign)'''
        return MF_stringToFormula(formulaString, formulaDict, sign)

    """@staticmethod
    def stringToFormula2(formulaString, formulaDict, sign):
        '''
        Converts a String to a formula - dict and adds or subtracts it to or from an original formula
        :param (str) formulaString: String which should be converted to a formula
        :param (dict[str:int]) formulaDict: "old" formula
        :param (int) sign: +1 or -1 for addition or subtraction of formula to or from formulaDict
        :return (dict[str:int]): new formula
        '''
        if formulaString == "" or formulaString == "-":
            return formulaDict
        for item in re.findall('[A-Z][^A-Z]*', formulaString):
            element = item
            number = 1
            match = re.match(r"([a-z]+)([0-9]+)", item, re.I)  # re.I: ignore case: ?
            if match:
                element = match.group(1)
                number = int(match.group(2))
            if element in formulaDict:
                formulaDict[element] += number * sign
            else:
                formulaDict[element] = number * sign
        if len(formulaDict)<1:
            raise InvalidInputException(formulaString, "Unvalid format of formula")
        return formulaDict

    @staticmethod
    def addToDict(dict1,dict2):
        '''
        Adds the values of one dict to another dict
        :param (dict[str:int]) dict1:
        :param (dict[str:int]) dict2:
        :return (dict[str:int]): "sum" dict
        '''
        for element, number in dict2.items():
            if element in dict1.keys():
                dict1[element] += number
            else:
                dict1[element] = number
        return dict1"""


class AbstractItem2(AbstractItem1, ABC):
    '''
    Parent class of IntactModification, AbstractItem3
    '''
    def __init__(self, name, gain, loss, enabled):
        '''
        :param (str) name:
        :param (str) gain:
        :param (str) loss:
        :param (int) enabled:
        '''
        super(AbstractItem2, self).__init__(name)
        self._gain = gain
        self._loss = loss
        self._enabled = enabled

    def processItem(self, item):
        '''
        Inserts a "-" into a value if it is empty
        :param (tuple[Any]) item:
        :return: (tuple[Any])
        '''
        processedItem = []
        for val in item:
            if val =='':
                processedItem.append('-')
            else:
                processedItem.append(val)
        return processedItem

    def enabled(self):
        return (self._enabled == 1)

    def getFormula(self):
        formulaDict = self.stringToFormula(self._gain, dict(), 1)
        return self.stringToFormula(self._loss, formulaDict, -1)


class AbstractItem3(AbstractItem2):
    '''
    Parent class of FragItem, PrecursorItem, ModificationItem
    '''
    def __init__(self, name, gain, loss, residue, radicals, enabled):
        '''
        :param (str) name:
        :param (str) gain:
        :param (str) loss:
        :param (str) residue:
        :param (int | str) radicals:
        :param (int) enabled:
        '''
        super(AbstractItem3, self).__init__(name, gain, loss, enabled)
        self._residue = residue
        self._radicals = radicals

    def getResidue(self):
        return self._residue

    def getRadicals(self):
        if self._radicals =='-' or self._radicals == '':
            return 0
        return self._radicals

    def toString(self):
        return [self._name, self._gain, self._loss, self._residue, str(self._radicals), str(self._enabled)]
