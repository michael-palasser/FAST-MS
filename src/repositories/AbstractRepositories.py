'''
Created on 29 Dec 2020

@author: michael
'''
from abc import ABC, abstractmethod
import sqlite3
from src import path
from os.path import join


class AbstractRepository(ABC):
    '''
    Abstract parent class for SearchRepository, SequenceRepository and AbstractRepositoryWithItems
    Dealing with just one table
    '''
    def __init__(self, database, tableName, columns, integerVals, boolVals, isolationLevel=None):
        '''
        :param (str) database: path + filename of the database
        :param (str) tableName: name of the table
        :param (tuple[str]) columns: column names of the table
        :param (tuple[int]]) integerVals: indices of the columns which contain numerical values
        :param (tuple[int]]) boolVals: indices of the columns which contain boolean values
        '''
        if isolationLevel is not None:
            self._conn = sqlite3.connect(join(path,"src","data",database),isolation_level=isolationLevel)
        else:
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

    def create(self, vals):
        """
        Creates a new entry in the table
        :param (list[Any] | tuple[Any]) vals: Values of the newly created item
        :return: (int) id of the newly created entry
        """
        cur = self._conn.cursor()
        #if len(self._columns)>1:
        sql = 'INSERT INTO ' + self._mainTable + '(' + ', '.join(self._columns) + ''') 
                              VALUES(''' + (len(self._columns) * '?,')[:-1] + ')'
       # else:
            #sql = 'INSERT INTO ' + self._mainTable + '(' + self._columns[0] + ''')
                                          #VALUES(''' + (len(self._columns) * '?,')[:-1] + ')'
        #print(self._mainTable, args,sql, self._columns)
        print(sql, vals)
        try:
            cur.execute(sql, vals)
        except sqlite3.OperationalError:
            self.makeTables()
            cur.execute(sql, vals)
        self._conn.commit()
        return cur.lastrowid


    def get(self, property, value):
        """
        Returns the entry with the desired value of the corresponding property
        :param (str) property: Searched attribute
        :param (Any) value: expected value of property
        :return: (list[Any]) entry
        :raises IndexError: if no matching entry is found
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
        '''
        Returns all stored entries within the database
        :return: (list[list[Any]]) all entries
        '''
        cur = self._conn.cursor()
        try:
            cur.execute('SELECT * FROM ' + self._mainTable)
            return cur.fetchall()
        except sqlite3.OperationalError:
            self.makeTables()
            return []


    def update(self, vals): #ToDo
        """
        Updates an entry
        :param (list[Any] | tuple[Any]) vals: new attributes, last attribute must be id
        """
        #print(vals)
        #print(vals[0])
        cur = self._conn.cursor()
        sql = 'UPDATE ' + self._mainTable + ' SET ' + '=?, '.join(self._columns) + '=? WHERE id=?'
        print(sql, vals)
        cur.execute(sql, vals)
        self._conn.commit()


    def delete(self, name):
        '''
        Deletes the entry
        :param (str) name: name of the entry which should be deleted
        :return: (int) id of the deleted entry
        '''
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM ' + self._mainTable+ ' WHERE name=?', (name,))
        id = cur.fetchall()[0]
        cur.execute('DELETE FROM ' + self._mainTable + ' WHERE name=?', (name,))
        return id[0]


    def close(self):
        self._conn.close()



class AbstractRepositoryWithItems(AbstractRepository, ABC):
    '''
    Abstract parent class for IntactRepository, MoleculeRepository, PeriodicTableRepository and AbstractRepositoryWith2Items
    Dealing with one main table and 1 subtable
    '''
    def __init__(self,database, tableName, columns, itemDict, integerVals, boolVals):
        '''
        :param (str) database: path + filename of the database
        :param (str) tableName: name of the main table
        :param (tuple[str]) columns: column names of the main table
        :param (dict[str,tuple[str]]) itemDict: dictionary {table name: column names} that defines the subtable
        :param (tuple[int] | tuple[tuple[int]]) integerVals: indices of the columns of the subtable which contain
            numerical values
        :param (tuple[int] | tuple[tuple[int]]) boolVals: indices of the columns of the subtable which contain boolean
            values
        '''
        super(AbstractRepositoryWithItems, self).__init__(database, tableName, columns, integerVals, boolVals)
        self._itemDict = itemDict


    def createPattern(self, pattern):
        """
        Creates a new entry in the main table and subsidiary entries in the subtable
        :param (Any) pattern: the object which should be stored within the database
        """
        #try:
        self.insertItems(self.create((pattern.getName(),)), pattern.getItems(), 0)
        #except sqlite3.IntegrityError:
         #   raise AlreadyPresentException(pattern.getName())

    def insertItems(self, patternId, items, index):
        '''
        Creates subsidiary entries in a subtable
        :param (int) patternId: id of the parent entry
        :param (list[list[Any]] | list[tuple[Any]]) items: list of subsidiary items which should be stored in the
            database
        :param (int) index: index of the corresponding subtable in _itemDict
        '''
        table = [key for key in self._itemDict.keys()][index]
        for item in items:
            #self.checkFormatOfItem(item)
            print(item)
            self.createItem(table, list(item) + [patternId])


    def createItem(self,table, attributes):
        '''
        Creates a subsidiary entry in a subtable
        :param (str) table: target subtable
        :param (list[Any] | tuple[Any]) attributes: attributes of the new entry
        :return: (int) id of the created entry
        '''
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + ' (' + ', '.join(self._itemDict[table]) + ''') 
                                      VALUES(''' + (len(self._itemDict[table]) * '?,')[:-1] + ')'
        print(sql, attributes)
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid

    def getPattern(self, name):
        pass

    def getItems(self, patternId, table):
        '''
        Returns the subsidiary entries of a parent entry
        :param (int) patternId: parent id
        :param (str) table: subtable which contains subsidiary entries
        :return: (list[list[Any]])
        '''
        #table = [key for key in self._itemDict.keys()][0]
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM " + table + " WHERE patternId=?", (patternId,))
        return cur.fetchall()


    def getAllPatternNames(self):
        '''
        Returns all names of the main entries
        :return: (list[str]) names
        '''
        return [pattern[1] for pattern in self.getAll()]

    def updatePattern(self, pattern):
        '''
        Updates a parent entry and all subsidiary entries
        :param (Any) pattern: object whose values should be updated in the database
        '''
        self.update((pattern.getName(), pattern.getId()))
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)


    def deleteAllItems(self, patternId):
        """
        Deletes all subsidiary entries of a parent entry
        :param patternId: id of parent entry
        """
        cur = self._conn.cursor()
        for table in self._itemDict.keys():
            cur.execute("DELETE FROM " + table + " WHERE patternId=?", (patternId,))
        self._conn.commit()

    def delete(self, name):
        '''
        Deletes a parent entry and all subsidiary entries
        :param name: name of the parent entry which should be deleted
        '''
        #id = super(AbstractRepositoryWith2Items, self).delete(name)
        self.deleteAllItems(super(AbstractRepositoryWithItems, self).delete(name))

    def deleteTables(self):
        '''
        Deletes all tables in a database
        '''
        cur = self._conn.cursor()
        for table in ([self._mainTable]+list(self._itemDict.keys())):
            cur.execute('DROP TABLE '+table)
        self._conn.commit()


class AbstractRepositoryWith2Items(AbstractRepositoryWithItems, ABC):
    '''
    Abstract parent class for FragmentationRepository and ModificationRepository
    Dealing with one main table and 2 subtables
    '''

    def __init__(self,database, tableName, columns, itemDict, integerVals, boolVals):
        '''
        :param (str) database: path + filename of the database
        :param (str) tableName: name of the main table
        :param (tuple[str]) columns: column names of the main table
        :param (dict[str,tuple[str]]) itemDict: dictionary {table name: column names} that defines the subtables
        :param (tuple[tuple[int]]) integerVals: indices of the columns which contain numerical values for each subtable
        :param (tuple[tuple[int]]) boolVals: indices of the columns which contain boolean values for each subtable
        '''
        super(AbstractRepositoryWith2Items, self).__init__(database, tableName, columns, itemDict, integerVals, boolVals)

    def getItemColumns(self):
        '''
        Returns the column names and corresponding tooltips for the user
        :return: (dict[str,str]) dictionary of {column name: tooltip}
        '''
        return {'Name':"Enter \"+\"modification or \"-\"loss", 'Gain':"molecular formula to be added",
                'Loss':"molecular formula to be subtracted"}


    def updatePattern(self, pattern):
        '''
        Updates a parent entry and all subsidiary entries
        :param (Any) pattern: object whose values should be updated in the database
        '''
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)
        self.insertItems(pattern.getId(), pattern.getItems2(), 1)
