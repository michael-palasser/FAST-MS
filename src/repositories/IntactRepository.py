'''
Created on 29 Dec 2020

@author: michael
'''
import sqlite3

from src.entities.IonTemplates import IntactPattern, IntactModification
from src.repositories.AbstractRepositories import AbstractRepositoryWithItems
from os.path import join

class IntactRepository(AbstractRepositoryWithItems):
    def __init__(self):
        super(IntactRepository, self).__init__(join('intact.db'), 'intactPatterns', ("name",),
                                               {"intactModItems":('name', 'gain', 'loss', 'nrMod','enabled', 'patternId')}, (3,), (4,))
        #self._conn = sqlite3.connect(':memory:')

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS intactPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS intactModItems (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "nrMod" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "patternId" integer NOT NULL );""")



    def getItemColumns(self):
        return {'Name':"Enter \"+\"modification or \"-\"loss", 'Gain':"molecular formula to be added",
                'Loss':"molecular formula to be subtracted", 'Nr.Mod.':"How often is species modified",
                'Enabled':"Activate/Deactivate Species"}


    def getPattern(self, name):
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], self.getItems(pattern[0],[key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        listOfItems = list()
        for item in super(IntactRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems


    """def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], pattern[2], pattern[3], self.getItemsAsObjects(pattern[0]), pattern[0])

    def getItemsAsObjects(self,patternId):
        listOfItems = list()
        for item in super(IntactRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(IntactModification(item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems"""

    def createPattern(self, pattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        # try:
        patternId = self.create((pattern.getName(),))
        self.insertItems(patternId, pattern.getItems(), 0)

    def updatePattern(self, pattern):
        self.update((pattern.getName(), pattern.getId()))
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)