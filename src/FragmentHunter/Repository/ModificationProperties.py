'''
Created on 29 Dec 2020

@author: michael
'''

import sqlite3
from src.FragmentHunter.Repository.FragmProperties import FragItem
from src.GeneralRepository.AbstractProperties import AbstractRepositoryWithItems
from src.GeneralRepository.Exceptions import AlreadyPresentException


class ModifiedItem(FragItem):
    def __init__(self,name,enabled, gain, loss, residue, radicals, zEffect):
        super(ModifiedItem, self).__init__(name, enabled, gain, loss, residue, radicals)
        self._zEffect = zEffect

    def getZEffect(self):
        return self._zEffect


class ModificationPattern(object):
    def __init__(self, name, modification, listOfMod, listOfOthers, id):
        self.name = name
        self.modification = modification
        self.listOfMod = listOfMod
        self.listOfOthers = listOfOthers
        self.id = id


class ModificationRepository(AbstractRepositoryWithItems):
    def __init__(self):
        super(ModificationRepository, self).__init__('TD_data.db', 'modPatterns',("name","modification"),
                            {'modItems':('name', 'enabled', 'gain', 'loss', 'residue', 'radicals', 'chargeEffect',
                               'included', 'patternId')})

    def makeTable(self):
        self._conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS modPatterns (
                        "id"	integer PRIMARY KEY UNIQUE ,
                        "name"	text NOT NULL UNIQUE,
                        "modification" text NOT NULL );""")
        self._conn.cursor().execute("""
                            CREATE TABLE IF NOT EXISTS modItems (
                                "id"	integer PRIMARY KEY,
                                "name"	text NOT NULL ,
                                "enabled" integer NOT NULL,
                                "gain" text NOT NULL ,
                                "loss" text NOT NULL ,
                                "residue" text NOT NULL ,
                                "radicals" integer NOT NULL ,
                                "chargeEffect" integer NOT NULL ,
                                 "included" integer NOT NULL ,
                                "patternId" integer NOT NULL );""")

    def createModPattern(self, modificationPattern):
        try:
            self.insertModificationItems(self.create(modificationPattern.name, modificationPattern.modification),
                                         modificationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(modificationPattern.name)


    def insertModificationItems(self, patternId, modificationPattern):
        for item in modificationPattern.listOfMod:
            self.createItem('modItems',item.getAll() + [1, patternId])
        for item in modificationPattern.listOfOthers:
            self.createItem('modItems',item.getAll() + [0, patternId])


    def getModPattern(self, name):
        pattern = self.get('name',name)
        return ModificationPattern(pattern[1], pattern[2], self.getModItems(pattern[0], 1),
                                   self.getModItems(pattern[0], 0), pattern[0])

    def getModItems(self, patternId, included):
        cur = self._conn.cursor()
        cur.execute("""SELECT * FROM modItems WHERE patternId=? AND included=?""", (patternId, included))
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(ModifiedItem(item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[0]))
        return listOfItems

    def getAllModPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(ModificationPattern(pattern[1], pattern[2], self.getModItems(pattern[0], 1),
                                   self.getModItems(pattern[0], 0), pattern[0]))
        return listOfPatterns


    def updateModPattern(self, modPattern):
        self.update(modPattern.name, modPattern.modification, modPattern.id)
        self.deleteList(modPattern.id, 'modItems')
        self.insertModificationItems(modPattern.id, modPattern)


    def deleteModPattern(self, id):
        self.deleteList(id, 'modItems')
        self.delete(id)
