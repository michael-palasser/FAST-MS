'''
Created on 29 Dec 2020

@author: michael
'''

from abc import ABC
import sqlite3
from src import path
from os.path import join


class AbstractItem(ABC):
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


class AbstractRepository(ABC):
    def __init__(self, database, tableName, columns):
        self._conn = sqlite3.connect(database)
        self.mainTable = tableName
        self.columns = columns

    """@abstractmethod
    def makeTable(self):
        pass"""


    def create(self, *args):
        """

        :param args: Values of the newly created item
        :return:
        """
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + self.mainTable + '(' + ', '.join(self.columns) + ''') 
                              VALUES(''' + (len(self.columns)*'?,')[:-1] + ')'
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
        sql = 'SELECT * FROM ' + self.mainTable + ' WHERE ' + property + '=?'
        cur.execute(sql, (value,))
        return cur.fetchall()[0]

    def getAll(self):
        cur = self._conn.cursor()
        cur.execute('SELECT * FROM ' + self.mainTable)
        return cur.fetchall()


    def update(self, *args):
        """

        :param args: new attributes, last attribute must be id
        :return:
        """
        cur = self._conn.cursor()
        sql = 'UPDATE ' + self.mainTable + ' SET ' + '=?, '.join(self.columns) + '=? WHERE id=?'
        cur.execute(sql, args)
        self._conn.commit()


    def delete(self, id):
        cur = self._conn.cursor()
        cur.execute('DELETE FROM ' + self.mainTable + ' WHERE id=?', (id,))


    def close(self):
        self._conn.close()


class AbstractRepositoryWithItems(AbstractRepository):
    def __init__(self,database, tableName, columns, itemDict):
        super(AbstractRepositoryWithItems, self).__init__(database, tableName, columns)
        self.itemDict = itemDict

    def createItem(self,table, attributes):
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + '(' + ', '.join(self.itemDict[table]) + ''') 
                                      VALUES(''' + (len(self.itemDict[table]) * '?,')[:-1] + ')'
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid

    def getAllItems(self, table, patternId):
        cur = self._conn.cursor()
        if patternId != None:
            cur.execute("SELECT * FROM " + table +" WHERE patternId=?", (patternId,))
        else:
            cur.execute("SELECT * FROM " + table)
        return cur.fetchall()

    def deleteList(self, patternId, table):
        """

        :param patternId: id of parent pattern
        :return:
        """
        cur = self._conn.cursor()
        cur.execute("DELETE FROM " + table + " WHERE patternId=?", (patternId,))
        self._conn.commit()
