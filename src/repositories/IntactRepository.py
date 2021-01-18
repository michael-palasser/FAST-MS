'''
Created on 29 Dec 2020

@author: michael
'''
import sqlite3

from src.entities.IonEntities import IntactPattern, IntactModification
from src.repositories.AbstractRepositories import AbstractRepositoryWithItems
from os.path import join

class Intact_Repository(AbstractRepositoryWithItems):
    def __init__(self):
        super(Intact_Repository, self).__init__(join('intact.db'), 'intactPatterns', ("name",),
                                                {"intactModItems":('name', 'gain', 'loss', 'nrMod','enabled', 'patternId')}, (3,), (4,))
        #self._conn = sqlite3.connect(':memory:')

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS intactPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS intactModItems (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "nrMod" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "patternId" integer NOT NULL );""")

    """def getAll(self):
        try:
            return super(Intact_Repository, self).getAll()
        except sqlite3.OperationalError:
            self.makeTable()
            return []"""

    """def createPattern(self, pattern):
        try:
            super(Intact_Repository, self).createPattern(pattern)
        except sqlite3.IntegrityError:
            self.makeTable()
            super(Intact_Repository, self).createPattern(pattern)"""


    def getItemColumns(self):
        return {'Name':"Enter \"+\"modification or \"-\"loss", 'Gain':"molecular formula to be added",
                'Loss':"molecular formula to be subtracted", 'Nr.Mod.':"How often is species modified",
                'Enabled':"Activate/Deactivate Species"}


    def getPattern(self, name):
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], self.getItems(pattern[0], [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        listOfItems = list()
        for item in super(Intact_Repository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], self.getItemsAsObjects(pattern[0]),
                             pattern[0])

    def getItemsAsObjects(self,patternId):
        listOfItems = list()
        for item in super(Intact_Repository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(IntactModification(item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems

    """def createPattern(self, modificationPattern):
        
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        
        try:
            self.insertItem(self.create((modificationPattern.getName(),)), modificationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(modificationPattern.getName())

    def insertItem(self, patternId, modificationPattern):
        for item in modificationPattern.getItems():
            self.createItem('intactModItems', item.getAll() + [patternId])"""


    """def getModPattern(self, name):
        pattern = self.get('name', name)
        return PatternWithItems(pattern[1], self.getItems(pattern[0]), pattern[0])

    def getItems(self, patternId):
        listOfItems = list()
        for item in self.getAllItems('intactModItems', patternId):
            listOfItems.append(PatternWithItems(item[1], item[2], item[3], item[4], item[5], item[0]))
        return listOfItems

    def getAllPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(PatternWithItems(pattern[1], self.getItems(pattern[0]), pattern[0]))
        return listOfPatterns

    def updatePattern(self, pattern):
        self.update(pattern.getName(), pattern.getId())
        self.deleteList(pattern.getId(), 'intactModItems')
        self.insertItem(pattern.getId(), pattern)

    def deleteFragPattern(self, id):
        self.deleteList(id, 'intactModItems')
        self.delete(id)
    """