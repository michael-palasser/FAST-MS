'''
Created on 29 Dec 2020

@author: michael
'''
from abc import ABC, abstractmethod
import sqlite3
from src import path
from os.path import join



class AbstractRepository(ABC):
    def __init__(self, database, tableName, columns, integerVals, boolVals):
        self._conn = sqlite3.connect(join(path,"src","data",database))
        self._mainTable = tableName
        self._columns = columns
        self._integerVals = integerVals
        self._boolVals = boolVals

    def getIntegers(self):
        return self._integerVals

    def getBoolVals(self):
        return self._boolVals

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
        #print(self._mainTable, args,sql, self._columns)
        print(sql,args)
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
        try:
            cur.execute(sql, (value,))
            return cur.fetchall()[0]
        except IndexError:
            print(sql)
            raise IndexError("value " + value + " in " + self._mainTable + " not found")


    def getItemColumns(self):
        pass

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
        print(sql, args)
        cur.execute(sql, args)
        self._conn.commit()


    def delete(self, name):
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM ' + self._mainTable+ ' WHERE name=?', (name,))
        id = cur.fetchall()[0]
        cur.execute('DELETE FROM ' + self._mainTable + ' WHERE name=?', (name,))
        return id[0]


    def close(self):
        self._conn.close()


class AbstractRepositoryWithItems(AbstractRepository, ABC):
    def __init__(self,database, tableName, columns, itemDict, integerVals, boolVals):
        super(AbstractRepositoryWithItems, self).__init__(database, tableName, columns, integerVals, boolVals)
        self._itemDict = itemDict


    def createPattern(self, pattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        #try:
        self.insertItems(self.create(pattern.getName()), pattern.getItems(), 0)
        #except sqlite3.IntegrityError:
         #   raise AlreadyPresentException(pattern.getName())

    def insertItems(self, patternId, items, index):
        table = [key for key in self._itemDict.keys()][index]
        for item in items:
            #self.checkFormatOfItem(item)
            self.createItem(table, item + [patternId])


    def createItem(self,table, attributes):
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + '(' + ', '.join(self._itemDict[table]) + ''') 
                                      VALUES(''' + (len(self._itemDict[table]) * '?,')[:-1] + ')'
        print(sql, attributes)
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid

    def getPattern(self, name):
        pass


    def getPatternWithObjects(self, name):
        pass

    def getItems(self, patternId, table):
        #table = [key for key in self._itemDict.keys()][0]
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


    """def getAllPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(PatternWithItems(pattern[1], 
                                    self.getItems(pattern[0],[key for key in self._itemDict.keys()][0]), pattern[0]))
        return listOfPatterns"""

    def getAllPatternNames(self):
        listOfNames = list()
        for pattern in self.getAll():
            listOfNames.append(pattern[1])
        return listOfNames

    def updatePattern(self, pattern):
        self.update(pattern.getName(), pattern.getId())
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)


    def deleteAllItems(self, patternId):
        """

        :param patternId: id of parent pattern
        :return:
        """
        cur = self._conn.cursor()
        for table in self._itemDict.keys():
            cur.execute("DELETE FROM " + table + " WHERE patternId=?", (patternId,))
        self._conn.commit()

    def delete(self, name):
        #id = super(AbstractRepositoryWith2Items, self).delete(name)
        self.deleteAllItems(super(AbstractRepositoryWithItems, self).delete(name))


class AbstractRepositoryWith2Items(AbstractRepositoryWithItems, ABC):
    """def __init__(self,database, tableName, columns, itemDict):
        super(AbstractRepositoryWith2Items, self).__init__(database, tableName, columns, itemDict)
        self._itemDict = itemDict"""

    def getItemColumns(self):
        return {'Name':"Enter \"+\"modification or \"-\"loss", 'Gain':"molecular formula to be added",
                'Loss':"molecular formula to be subtracted"}

    """def createPattern(self, pattern):
        \"""
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        \"""
        #try:
        print("save",pattern.getItems2())
        patternId = self.create(pattern.getName())
        print(pattern.getItems(),pattern.getItems2())
        self.insertItems(patternId, pattern.getItems(), 0)
        self.insertItems(patternId, pattern.getItems2(), 1)"""
        #except sqlite3.IntegrityError:
         #   raise AlreadyPresentException(pattern.getName())


    def updatePattern(self, pattern):
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)
        self.insertItems(pattern.getId(), pattern.getItems2(), 1)
