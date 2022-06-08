'''
Created on 29 Dec 2020

@author: michael
'''
from os.path import join

from src.entities.GeneralEntities import Element
from src.repositories.sql.AbstractRepositories import AbstractRepositoryWithItems


class PeriodicTableRepository(AbstractRepositoryWithItems):
    '''
    Repository for periodic table of elements
    '''
    def __init__(self):
        super(PeriodicTableRepository, self).__init__(join('shared.db'), 'elements', ('name',),
                                                      {'isotopes':('nucNr', 'mass', 'relAb', 'patternId')}, (0,1,2),())

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS elements (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS isotopes (
                "id"	integer PRIMARY KEY UNIQUE,
                "nucNr" integer NOT NULL ,
                "mass" real NOT NULL ,
                "relAb" real NOT NULL ,
                "patternId" integer NOT NULL );""")

    def getItemColumns(self):
        '''
        Returns the column names and corresponding tooltips for the user
        :return: (dict[str,str]) dictionary of {column name: tooltip}
        '''
        #'isoNr': 'Number of isotope (e.g.: 13C --> isoNr = 1)
        return {'Nuc. no.':'Number of Nucleons',
                'Mass': 'Mass in Da',
                'Rel. ab.': 'Relative abundance'}


    def getPattern(self, name):
        '''
        Finds an element entry with its isotopes by name
        :param (str) name: name
        :return: (Element) element
        '''
        pattern = self.get('name', name)
        return Element(pattern[1], self.getItems(pattern[0], [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        '''
        Returns the isotope entries of an element entry
        :param (int) patternId: parent id
        :param (str) table: subtable which contains subsidiary entries
        :return: (list[list[float,float,float]])
        '''
        listOfItems = list()
        for item in super(PeriodicTableRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3]))#, item[4], item[5]) )
        return listOfItems


    """def getPatternWithObjects(self, name):
        '''
        
        :param name: 
        :return: 
        '''
        pattern = self.get('name', name)
        return Element(pattern[1], self.getItemsAsObjects(pattern[0]),
                             pattern[0])

    def getItemsAsObjects(self,patternId):
        listOfItems = list()
        for item in super(PeriodicTableRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(Isotope(item[1], item[2], item[3]) )
        return listOfItems"""

