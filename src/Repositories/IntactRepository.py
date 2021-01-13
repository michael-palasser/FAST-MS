'''
Created on 29 Dec 2020

@author: michael
'''
from src.Entities.IonEntities import IntactPattern, IntactModification
from src.Repositories.AbstractRepositories import AbstractRepositoryWithItems2
from os.path import join

class ESI_Repository(AbstractRepositoryWithItems2):
    def __init__(self):
        super(ESI_Repository, self).__init__(join('Intact_Ion_Search','data','ESI_data.db'), 'intactPatterns',("name",),
                            {"intactModItems":('name', 'gain', 'loss', 'nrMod','enabled', 'patternId')}, (3,),(4,))

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
        columns = super(ESI_Repository, self).getItemColumns()
        columns.update({'Nr.Mod.':"How often is species modified",'Enabled':"Activate/Deactivate Species"})
        return columns


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

    def updatePattern(self, modPattern):
        self.update(modPattern.getName(), modPattern.getId())
        self.deleteList(modPattern.getId(), 'intactModItems')
        self.insertItem(modPattern.getId(), modPattern)

    def deleteFragPattern(self, id):
        self.deleteList(id, 'intactModItems')
        self.delete(id)
    """