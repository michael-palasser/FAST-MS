'''
Created on 29 Dec 2020

@author: michael
'''
from os.path import join

from src.Entities.GeneralEntities import Element, Isotope
from src.Repositories.AbstractRepositories import AbstractRepositoryWithItems1


class PeriodicTableRepository(AbstractRepositoryWithItems1):
    def __init__(self):
        super(PeriodicTableRepository, self).__init__(join('Repositories', 'Shared_data.db'), 'elements', ('name',),
                                                      {'isotopes':('pNr', 'mass', 'relAb', 'patternId')}, (0,1,2),())

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS elements (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS isotopes (
                "id"	integer PRIMARY KEY UNIQUE,
                "pNr" integer NOT NULL ,
                "mass" real NOT NULL ,
                "relAb" real NOT NULL ,
                "patternId" integer NOT NULL );""")

    def getItemColumns(self):
        #'isoNr': 'Number of isotope (e.g.: 13C --> isoNr = 1)
        return {'pNr':'Number of Protons',
                'mass': 'Mass of the isotope in Da',
                'relAb': 'Relative abundance of isotope'}


    def getPattern(self, name):
        pattern = self.get('name', name)
        return Element(pattern[1], self.getItems(pattern[0], [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        listOfItems = list()
        for item in super(PeriodicTableRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5]) )
        return listOfItems


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        return Element(pattern[1], self.getItemsAsObjects(pattern[0]),
                             pattern[0])

    def getItemsAsObjects(self,patternId):
        listOfItems = list()
        for item in super(PeriodicTableRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(Isotope(item[1], item[2], item[3]) )
        return listOfItems



    """def createElement(self, element):
        \"""
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        \"""
        try:
            self.insertIsotopes(self.create((element.getName(),)), element)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(element.getName())

    def insertIsotopes(self, elementId, element):
        for item in element.getIsotopes():
            self.createItem('isotopes', item.getAll() + [elementId])


    def getElement(self, name):
        element = self.get('name', name)
        return Element(element[1], self.getIsotopes(element[0]), element[0])

    def getIsotopes(self, patternId):
        isotopes = list()
        for isotope in self.getAllItems('isotopes', patternId):
            isotopes.append(Isotope(isotope[1], isotope[2], isotope[3], isotope[4], isotope[0]))
        return isotopes

    def getAllElements(self):
        elements = list()
        for element in self.getAll():
            elements.append(Element(element[1], self.getIsotopes(element[0]), element[0]))
        return elements


    def updatePattern(self, element):
        self.update(element.getName(), element.getId())
        self.deleteList(element.getId(), 'isotopes')
        self.insertIsotopes(element.getId(), element)


    def deleteElement(self, id):
        self.deleteList(id, 'intactModItems')
        self.delete(id)"""