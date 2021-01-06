'''
Created on 29 Dec 2020

@author: michael
'''

from abc import ABC, abstractmethod
import sqlite3
from src import path
from os.path import join

from src.GeneralRepository.Exceptions import AlreadyPresentException


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
    def __init__(self, name, items, id, integerVals):
        super(PatternWithItems, self).__init__(name, id)
        self._items = items #list of dict of values
        self._integerVals = integerVals

    def getItems(self):
        return self._items

    def setItems(self, items):
        formatedItems = list()
        for i,row in enumerate(items):
            formatedRow = list()
            for j, val in enumerate(items):
                try:
                    if j in self._integerVals:
                        formatedRow.append(int(val))
                    elif (j == 1) or (j==2):
                        #ToDo: Ueberpruefen ob Formel passt und ob enabled<2
                        formatedRow.append(val)
                except ValueError:
                    raise Exception("Invalid Input in row "+str(i)+", column "+str(j)+". Input must be an integer!")
                else:
                    formatedRow.append(val)
            formatedItems.append(formatedRow)
        self._items = formatedItems

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

"""class AbstractItem(ABC):
    def __init__(self, name, enabled, gain, loss, id):
        self._name = name
        self._enabled = enabled
        self._gain = gain
        self._loss = loss
        self._id = id

    def getName(self):
        return self._name

    def enabled(self):
        return (self._enabled == 1)

    def getGain(self):
        return self._gain

    def getLoss(self):
        return self._loss

    def getId(self):
        return self._id

    def getAll(self):
        return [self._name, self._enabled, self._gain, self._loss]

    def getItemsAsList(self):
        pass
"""

class AbstractRepository(ABC):
    def __init__(self, database, tableName, columns):
        self._conn = sqlite3.connect(join(path,"src",database))
        self._mainTable = tableName
        self._columns = columns

    @abstractmethod
    def makeTables(self):
        pass


    def create(self, *args):
        """

        :param args: Values of the newly created item
        :return:
        """
        cur = self._conn.cursor()
        #if len(self._columns)>1:
        sql = 'INSERT INTO ' + self._mainTable + '(' + ', '.join(self._columns) + ''') 
                              VALUES(''' + (len(self._columns) * '?,')[:-1] + ')'
       # else:
            #sql = 'INSERT INTO ' + self._mainTable + '(' + self._columns[0] + ''')
                                          #VALUES(''' + (len(self._columns) * '?,')[:-1] + ')'
        try:
            cur.execute(sql, args)
        except sqlite3.OperationalError:
            self.makeTables()
            cur.execute(sql, args)
        self._conn.commit()
        return cur.lastrowid


    def get(self, property, value):
        """

        :param property: Searched attribute (String)
        :param value: expected value of property
        :return:
        """
        cur = self._conn.cursor()
        sql = 'SELECT * FROM ' + self._mainTable + ' WHERE ' + property + '=?'
        cur.execute(sql, (value,))
        return cur.fetchall()[0]

    def getAll(self):
        cur = self._conn.cursor()
        try:
            cur.execute('SELECT * FROM ' + self._mainTable)
            return cur.fetchall()
        except sqlite3.OperationalError:
            self.makeTables()
            return []


    def update(self, *args):
        """

        :param args: new attributes, last attribute must be id
        :return:
        """
        cur = self._conn.cursor()
        sql = 'UPDATE ' + self._mainTable + ' SET ' + '=?, '.join(self._columns) + '=? WHERE id=?'
        cur.execute(sql, args)
        self._conn.commit()


    def delete(self, id):
        cur = self._conn.cursor()
        cur.execute('DELETE FROM ' + self._mainTable + ' WHERE id=?', (id,))


    def close(self):
        self._conn.close()


class AbstractRepositoryWithItems(AbstractRepository, ABC):
    def __init__(self,database, tableName, columns, itemDict):
        super(AbstractRepositoryWithItems, self).__init__(database, tableName, columns)
        self._itemDict = itemDict

    def getItemColumns(self, *args):
        pass

    def createPattern(self, pattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        #try:
        self.insertModifications(self.create(pattern.getName()), pattern)
        #except sqlite3.IntegrityError:
         #   raise AlreadyPresentException(pattern.getName())

    def insertModifications(self, patternId, pattern):
        table = [key for key in self._itemDict.keys()][0]
        for item in pattern.getItems():
            self.createItem(table, item + [patternId])

    def createItem(self,table, attributes):
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + '(' + ', '.join(self._itemDict[table]) + ''') 
                                      VALUES(''' + (len(self._itemDict[table]) * '?,')[:-1] + ')'
        print(attributes)
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid

    def getPattern(self, name):
        pass

    def getItems(self, patternId):
        table = [key for key in self._itemDict.keys()][0]
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM " + table + " WHERE patternId=?", (patternId,))
        return cur.fetchall()
        """listOfItems = list()
        for item in cur.fetchall():
            row = []
            for val in item:
                row
            #propertyDict = {}
            #for i, val in enumerate(self._itemDict.values()):
            #    propertyDict[val]= item[i]
            listOfItems.append(propertyDict)

        return listOfItems"""


    def getAllPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(PatternWithItems(pattern[1], self.getItems(pattern[0]), pattern[0]))
        return listOfPatterns

    def getAllPatternNames(self):
        listOfNames = list()
        for pattern in self.getAll():
            listOfNames.append(pattern[1])
        return listOfNames

    def updateFragPattern(self, modPattern):
        self.update(modPattern.getName(), modPattern.getId())
        self.deleteAllItems(modPattern.getId())
        self.insertModifications(modPattern.getId(), modPattern)


    def deleteAllItems(self, patternId):
        """

        :param patternId: id of parent pattern
        :return:
        """
        cur = self._conn.cursor()
        for table in self._itemDict.keys():
            cur.execute("DELETE FROM " + table + " WHERE patternId=?", (patternId,))
        self._conn.commit()

    def deleteFragPattern(self, id):
        self.deleteAllItems(id)
        self.delete(id)