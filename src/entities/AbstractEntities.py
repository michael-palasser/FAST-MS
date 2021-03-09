import re
from abc import ABC

from src.Exceptions import UnvalidInputException


class AbstractPattern(ABC):
    def __init__(self, name, id):
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
    def __init__(self, name, items, id):
        """

        :param name:
        :param items: either list of Item objects for AbstractLibraryBuilder or 2D list for views
        :param id:
        :param integerVals:
        """
        super(PatternWithItems, self).__init__(name, id)
        self._items = items  # list of dict of values

    def getItems(self):
        return self._items

    def setItems(self, items):
        self._items = items

    """def setItems(self, items):
        formatedItems = list()
        for i, row in enumerate(items):
            formatedRow = []
            for j, val in enumerate(items):
                try:
                    if j in self._integerVals:
                        formatedRow.append(int(val))
                    elif (j == 1) or (j == 2):
                        # ToDo: Ueberpruefen ob Formel passt: alle keys in PeriodicTable
                        # AbstractItem2.stringToFormula(val, dict(),1)
                        formatedRow.append(val)
                except ValueError:
                    raise Exception(
                        "Invalid Input in row " + str(i) + ", column " + str(j) + ". Input must be an integer!")
                else:
                    formatedRow.append(val)
            formatedItems.append(formatedRow)
        self._items = formatedItems"""

    """def getItemsAsList(self):


        :return: dict of lists (lists = columns)

        itemDict = dict()
        # _itemDict = {"Name":[], "Gain":[], "Loss":[], "NrOfMod":[], "enabled":[]}
        for item in self._items:
            for key, val in item.items():
                if key not in itemDict.keys():
                    itemDict[key] = [val]
                else:
                    itemDict[key].append(val)
        return itemDict"""

    """def getItemsAsList(self):

        :return: dict
        of
        lists(lists=columns)

        itemDict = dict()
        # _itemDict = {"Name":[], "Gain":[], "Loss":[], "NrOfMod":[], "enabled":[]}
        for item in self._items:
            for key, val in item.items():
                if key not in itemDict.keys():
                    itemDict[key] = [val]
                else:
                    itemDict[key].append(val)
        return itemDict"""


class AbstractItem1(ABC):
    def __init__(self, name):
        self._name = name

    def getName(self):
        return self._name

    @staticmethod
    def stringToFormula(formulaString, formulaDict, sign):
        #everything in parenthesis
        beginIndizes = [m.start() for m in re.finditer('\(', formulaString)]
        endIndizes = [m.start() for m in re.finditer('\)', formulaString)]
        if len(beginIndizes) != len(endIndizes):
            raise UnvalidInputException(formulaString, 'Incorrect use of parenthesis')
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
        formulaDict = AbstractItem1.stringToFormula2(formulaString[lastEnd:],formulaDict,sign)
        return formulaDict


        '''if ')' in formulaString:
            print('yes')
        if ('(' in formulaString) and (')' in formulaString):
            print(re.findall('\)[^A-Z]',formulaString))
            for form,nrStr in zip(re.findall('\(.*?\)',formulaString), re.findall('\)[^A-Z]',formulaString)):
                nr=1
                if len(nrStr)>1:
                    nr = int(nrStr[1:])
                temp = {key:val*nr for key,val in AbstractItem1.stringToFormula2(form[1:-1], {}, sign).items()}
                for element, number in temp.items():
                    if element in formulaDict.keys():
                        formulaDict[element] += number
                    else:
                        formulaDict[element] = number
            #everything outside parenthesis
            print(formulaDict)
            for subString in formulaString.split('('):
                if subString !='':
                    if not ')' in subString:
                        formulaDict = AbstractItem1.stringToFormula2(subString,formulaDict,sign)
                    else:
                        subI2 = subString.split(')')
                        match = re.match(r"([0-9]+)([a-z]+)", subI2[1], re.I)  # re.I: ignore case: ?
                        if match:
                            formulaDict = AbstractItem1.stringToFormula2(match.group(2),formulaDict,sign)
                        elif not subI2[1].isnumeric():
                            formulaDict = AbstractItem1.stringToFormula2(subI2[1],formulaDict,sign)
        else:
            formulaDict = AbstractItem1.stringToFormula2(formulaString, formulaDict, sign)
        return formulaDict'''

    @staticmethod
    def stringToFormula2(formulaString, formulaDict, sign):
        '''
        Converts a String to a formula - dict and adds or subtracts it to or from an original formula
        :param formulaString: String which should be converted to a formula
        :param formulaDict: "old" formula (dictionary)
        :param sign: +1 or -1 for addition or subtraction of formula to or from formulaDict
        :return: new formula (dict)
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
            raise UnvalidInputException(formulaString, "Unvalid format of formula")
        return formulaDict

    @staticmethod
    def addToDict(dict1,dict2):
        print('adding', dict1,dict2)
        for element, number in dict2.items():
            if element in dict1.keys():
                dict1[element] += number
            else:
                dict1[element] = number
        return dict1


class AbstractItem2(AbstractItem1, ABC):
    def __init__(self, name, gain, loss, enabled):
        super(AbstractItem2, self).__init__(name)
        self._gain = gain
        self._loss = loss
        self._enabled = enabled

    def processItem(self, item):
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
    def __init__(self, name, gain, loss, residue, radicals, enabled):
        super(AbstractItem3, self).__init__(name, gain, loss, enabled)
        self._residue = residue
        self._radicals = radicals

    def getResidue(self):
        return self._residue

    def getRadicals(self):
        return self._radicals

    def toString(self):
        return [self._name, self._gain, self._loss, self._residue, str(self._radicals), str(self._enabled)]
