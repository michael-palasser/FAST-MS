import re
from abc import ABC


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
        :param items: either list of Item objects for AbstractLibraryBuilder or 2D list for GUI
        :param id:
        :param integerVals:
        """
        super(PatternWithItems, self).__init__(name, id)
        self._items = items  # list of dict of values

    def getItems(self):
        return self._items

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
        '''
        Converts a String to a formula - dict and adds or subtracts it to or from an original formula
        :param formulaString: String which should be converted to a formula
        :param formulaDict: "old" formula (dictionary)
        :param sign: +1 or -1 for addition or subtraction of formula to or from formulaDict
        :return: new formula (dict)
        '''
        print("finally",formulaString)
        if formulaString == "":
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
        return formulaDict


class AbstractItem2(AbstractItem1, ABC):
    def __init__(self, name, enabled, gain, loss):
        super(AbstractItem2, self).__init__(name)
        self._enabled = enabled
        self._gain = gain
        self._loss = loss

    def enabled(self):
        return (self._enabled == 1)

    def getFormula(self):
        print(self._gain, self._loss)
        formulaDict = self.stringToFormula(self._gain, dict(), 1)
        return self.stringToFormula(self._loss, formulaDict, -1)




