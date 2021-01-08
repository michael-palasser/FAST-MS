'''
Created on 29 Dec 2020

@author: michael
'''

import sqlite3
from src.FragmentHunter.Repository.FragmProperties import FragItem
from src.GeneralRepository.AbstractProperties import AbstractRepositoryWithItems, PatternWithItems
from src.GeneralRepository.Exceptions import AlreadyPresentException


class ModifiedItem(FragItem):
    def __init__(self,name, gain, loss, residue, radicals, zEffect,enabled):
        super(ModifiedItem, self).__init__(name, gain, loss, residue, radicals, enabled)
        self.__zEffect = zEffect

    def getZEffect(self):
        return self.__zEffect


class ModificationPattern(PatternWithItems):
    def __init__(self, name, modification, listOfMod, listOfContaminants, id):
        super(ModificationPattern, self).__init__(name, listOfMod,id, [4,5])
        self.__modification = modification
        self.__listOfContaminants = listOfContaminants

    def getModification(self):
        return self.__modification

    def getListOfContaminants(self):
        return self.__listOfContaminants


class ModificationRepository(AbstractRepositoryWithItems):
    def __init__(self):
        super(ModificationRepository, self).__init__('TD_data.db', 'modPatterns',("name","modification"),
                            {'modItems':('name', 'gain', 'loss', 'residue', 'radicals', 'chargeEffect',
                                         'enabled', 'patternId'),
                             'contaminants': ('name', 'gain', 'loss', 'residue', 'radicals', 'chargeEffect',
                                          'enabled', 'patternId')})

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
        self._conn.cursor().execute("""
                            CREATE TABLE IF NOT EXISTS contaminants (
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

    """def createModPattern(self, modificationPattern):
        try:
            self.insertModificationItems(self.create(modificationPattern.name, modificationPattern.modification),
                                         modificationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(modificationPattern.name)


    def insertModificationItems(self, patternId, modificationPattern):
        for item in modificationPattern.listOfMod:
            self.createItem('modItems',item.getAll() + [1, patternId])
        for item in modificationPattern.listOfContaminants:
            self.createItem('modItems',item.getAll() + [0, patternId])


    def getModPattern(self, name):
        pattern = self.get('name',name)
        return ModificationPattern(pattern[1], pattern[2], self.getModItems(pattern[0], 1),
                                   self.getModItems(pattern[0], 0), pattern[0])

    def getModItems(self, patternId, included):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM modItems WHERE patternId=? AND included=?", (patternId, included))
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
        self.delete(id)"""

    def getItemColumns(self):
        return super(ModificationRepository, self).getItemColumns()+['Residue', 'Radicals', 'z-Effect' 'Enabled']


    def getPattern(self, name):
        pattern = self.get('name', name)
        listOfLists = self.getAllItems(pattern[0])
        return ModificationPattern(pattern[1], pattern[2], listOfLists[0], listOfLists[1], pattern[0])

    def getAllItems(self, patternId):
        listOfLists = []
        for table in self._itemDict.keys():
            listOfItems = []
            for item in self.getItems(patternId, table):
                listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6], item[7]))
            listOfLists.append(listOfItems)
        return listOfLists


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        listOfItemLists = self.getItemsAsObjects(pattern[0])
        return ModificationPattern(pattern[1], pattern[2], listOfItemLists[0], listOfItemLists[1], pattern[0])


    def getItemsAsObjects(self, patternId):
        listOfItemLists = []
        for table in self._itemDict.keys():
            listOfItems = []
            for item in super(ModificationRepository, self).getItems(patternId,table):
                listOfItems.append(ModifiedItem(item[1], item[2], item[3], item[4], item[5], item[6], item[7]))
            listOfItemLists.append(listOfItems)
        return listOfItemLists