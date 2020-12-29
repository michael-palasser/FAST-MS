'''
Created on 29 Dec 2020

@author: michael
'''
import sqlite3
from src.GeneralRepository.AbstractProperties import AbstractRepository, AbstractItem


class IntactModifications(object):
    def __init__(self, name, modifications):
        self.__name = name
        self.__modifications = modifications

    def getName(self):
        return self.__name

    def getModification(self):
        return self.__modifications

class IntactModification(AbstractItem):
    def __init__(self, name, enabled, gain, loss, nrMod, id):
        super(IntactModification, self).__init__(name, enabled, gain, loss, id)
        self._nrMod = nrMod

    def getNrMod(self):
        return self._nrMod

    def getAll(self):
        super(IntactModification, self).getAll() + [self._nrMod]


class ESI_Repository(AbstractRepository):
    def __init__(self):
        super(ESI_Repository, self).__init__('modPatterns',("name"))
        self.modColumns = ('name', 'enabled', 'gain', 'loss', 'residue', 'radicals', 'patternId')

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS intactPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS intactModItems (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "enabled" integer NOT NULL,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "nrMod" integer NOT NULL ,
                "patternId" integer NOT NULL );""")

    #ToDo
    """def createFragPattern(self, fragmentationPattern):
        try:
            self.insertFragmentTypes(self.create((fragmentationPattern.name,)), fragmentationPattern)
        except sqlite3.IntegrityError:
            raise Exception(fragmentationPattern.name, "already present")

    def insertFragmentTypes(self, patternId, fragmentationPattern):
        for item in fragmentationPattern.fragmentTypes:
            self.createFragItem(item, patternId)

    def createFragItem(self, item, patternId):
        cur = self._conn.cursor()
        sql = 'INSERT INTO intactModItems(' + ', '.join(self.modColumns) + ''')
                      VALUES(?, ?, ?, ?, ?, ?,?) '''
        values = item.getAll() + [patternId]
        self.create()
        cur.execute(sql, values)
        self._conn.commit()
        return cur.lastrowid

    def getFragPattern(self, name):
        pattern = self.get('name', name)
        return FragmentationPattern(pattern[1], self.getItems(pattern[0]), pattern[0])

    def getItems(self, patternId):
        cur = self._conn.cursor()
        if patternId != None:
            cur.execute("SELECT * FROM intactModItems WHERE patternId=?", (patternId,))
        else:
            cur.execute("SELECT * FROM intactModItems")
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(Item(item[1], item[2], item[3], item[4], item[5], item[6], item[0]))
        return listOfItems

    def getAllPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(FragmentationPattern(pattern[1], self.getItems(pattern[0]), pattern[0]))
        return listOfPatterns


    def updateFragPattern(self, fragPattern):
        self.update(fragPattern.name, fragPattern.id)
        self.deleteList(fragPattern.id, 'fragmentTypes')
        self.insertFragmentTypes(fragPattern.id, fragPattern)


    def deleteFragPattern(self, id):
        self.deleteList(id, 'fragmentTypes')
        self.delete(id)
"""