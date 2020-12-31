'''
Created on 29 Dec 2020

@author: michael
'''
import sqlite3
from src.GeneralRepository.AbstractProperties import AbstractRepositoryWithItems, AbstractItem
from src.GeneralRepository.Exceptions import AlreadyPresentException


class IntactModifications(object):
    def __init__(self, name, modifications, id):
        self.__name = name
        self.__modifications = modifications
        self.__id = id

    def getName(self):
        return self.__name

    def getModification(self):
        return self.__modifications

    def getId(self):
        return self.__id

class IntactModification(AbstractItem):
    def __init__(self, name, enabled, gain, loss, nrMod, id):
        super(IntactModification, self).__init__(name, enabled, gain, loss, id)
        self._nrMod = nrMod

    def getNrMod(self):
        return self._nrMod

    def getAll(self):
        super(IntactModification, self).getAll() + [self._nrMod]


class ESI_Repository(AbstractRepositoryWithItems):
    def __init__(self):
        super(ESI_Repository, self).__init__('ESI_data.db', 'modPatterns',("name"),
                            {"intactModItems":('name', 'enabled', 'gain', 'loss', 'residue', 'radicals', 'patternId')})

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


    def createPattern(self, modificationPattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        try:
            self.insertModifications(self.create((modificationPattern.name,)), modificationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(modificationPattern.name)

    def insertModifications(self, patternId, modificationPattern):
        for item in modificationPattern.fragmentTypes:
            self.createItem('intactModItems', item.getAll() + [patternId])


    def getModPattern(self, name):
        pattern = self.get('name', name)
        return IntactModifications(pattern[1], self.getItems(pattern[0]), pattern[0])

    def getItems(self, patternId):
        listOfItems = list()
        for item in self.getAllItems('intactModItems', patternId):
            listOfItems.append(IntactModification(item[1], item[2], item[3], item[4], item[5], item[0]))
        return listOfItems

    def getAllPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(IntactModifications(pattern[1], self.getItems(pattern[0]), pattern[0]))
        return listOfPatterns


    def updateFragPattern(self, modPattern):
        self.update(modPattern.getName(), modPattern.getId())
        self.deleteList(modPattern.getId(), 'intactModItems')
        self.insertModifications(modPattern.getId(), modPattern)


    def deleteFragPattern(self, id):
        self.deleteList(id, 'intactModItems')
        self.delete(id)