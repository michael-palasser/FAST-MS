'''
Created on 29 Dec 2020

@author: michael
'''
import sqlite3
from src.GeneralRepository.AbstractProperties import AbstractRepositoryWithItems, PatternWithItems, AbstractItem
from src.GeneralRepository.Exceptions import AlreadyPresentException
from os.path import join



class IntactPattern(PatternWithItems):
    def __init__(self,  name, items, id):
        super(IntactPattern, self).__init__(name, items, id, (3, 4))


"""def getItemsAsList(self):
        _itemDict = dict()
        #_itemDict = {"Name":[], "Gain":[], "Loss":[], "NrOfMod":[], "enabled":[]}
        for item in self.__modifications:
            for key, val in item.items()
                if item not in
        return {"Name":[], "Gain", "Loss", "NrOfMod", "enabled"}"""

class IntactModification(AbstractItem):
    def __init__(self, name, gain, loss, nrMod, enabled):
        super(IntactModification, self).__init__(name, enabled, gain, loss)
        self._nrMod = nrMod

    def getNrMod(self):
        return self._nrMod



class ESI_Repository(AbstractRepositoryWithItems):
    def __init__(self):
        super(ESI_Repository, self).__init__(join('Intact_Ion_Search','Repository','ESI_data.db'), 'intactPatterns',("name",),
                            {"intactModItems":('name', 'gain', 'loss', 'nrMod','enabled', 'patternId')})

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
            return super(ESI_Repository, self).getAll()
        except sqlite3.OperationalError:
            self.makeTable()
            return []"""

    """def createPattern(self, pattern):
        try:
            super(ESI_Repository, self).createPattern(pattern)
        except sqlite3.IntegrityError:
            self.makeTable()
            super(ESI_Repository, self).createPattern(pattern)"""


    def getItemColumns(self):
        return super(ESI_Repository, self).getItemColumns()+['Nr.Mod.','Enabled']


    def getPattern(self, name):
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], self.getItems(pattern[0], [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        listOfItems = list()
        for item in super(ESI_Repository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], self.getItemsAsObjects(pattern[0]),
                             pattern[0])

    def getItemsAsObjects(self,patternId):
        listOfItems = list()
        for item in super(ESI_Repository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(IntactModification(item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems

    """def createPattern(self, modificationPattern):
        
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        
        try:
            self.insertModifications(self.create((modificationPattern.getName(),)), modificationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(modificationPattern.getName())

    def insertModifications(self, patternId, modificationPattern):
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

    def updatePattern(self, modPattern):
        self.update(modPattern.getName(), modPattern.getId())
        self.deleteList(modPattern.getId(), 'intactModItems')
        self.insertModifications(modPattern.getId(), modPattern)

    def deleteFragPattern(self, id):
        self.deleteList(id, 'intactModItems')
        self.delete(id)
    """