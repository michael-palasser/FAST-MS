'''
Created on 29 Dec 2020

@author: michael
'''

from src.entities.IonTemplates import IntactPattern
from src.repositories.sql.AbstractRepositories import AbstractRepositoryWithItems
from os.path import join

class IntactRepository(AbstractRepositoryWithItems):
    '''
    Repository for intact modification patterns
    '''
    def __init__(self):
        super(IntactRepository, self).__init__(join('intact.db'), 'intactPatterns', ("name",),
                                               {"intactModItems":('name', 'gain', 'loss', 'nrMod', 'radicals','enabled',
                                                                  'patternId')}, (3,4), (5,))
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
                "radicals" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "patternId" integer NOT NULL );""")



    def getItemColumns(self):
        '''
        Returns the column names and corresponding tooltips for the user
        :return: (dict[str,str]) dictionary of {column name: tooltip}
        '''
        return {'name':"Enter \"+\"modification or \"-\"loss", 'gain':"Molecular formula to be added",
                'loss':"Molecular formula to be subtracted", 'no.mod.':"Number how often the species is modified",
                'radicals': "Enter the number of radicals",
                'enabled':"Activate/Deactivate Species"}


    def getPattern(self, name):
        '''
        Finds an intact pattern entry with its intact modifications by name
        :param (str) name: name
        :return: (IntactPattern) intact pattern
        '''
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], self.getItems(pattern[0],[key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        '''
        Returns the subsidiary intact modification entries of a intact pattern entry
        :param (int) patternId: parent id
        :param (str) table: subtable which contains subsidiary entries
        :return: (list[list[str,str,str,int,int,int]])
        '''
        listOfItems = list()
        for item in super(IntactRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6]))
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
        Creates a new intact pattern entry in the main table and subsidiary entries in the subtable
        :param (Any) pattern: the object which should be stored within the database
        """
        # try:
        patternId = self.create((pattern.getName(),))
        self.insertItems(patternId, pattern.getItems(), 0)

    def updatePattern(self, pattern):
        '''
        Updates an intact pattern entry and all subsidiary intact modification entries
        :param (IntactPattern) pattern: updated IntactPattern object
        '''
        self.update((pattern.getName(), pattern.getId()))
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)