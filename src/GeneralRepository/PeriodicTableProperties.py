'''
Created on 29 Dec 2020

@author: michael
'''
import sqlite3

from src.GeneralRepository.AbstractProperties import AbstractRepositoryWithItems
from src.GeneralRepository.Exceptions import AlreadyPresentException


class Element(object):
    def __init__(self, name, isotopes, id):
        """

        :param name:
        :param isotopes: vorerst 2D list, dann (ToDo) 2D numpy array
        :param id:
        """
        self.__name = name
        self.__isotopes = isotopes
        self.__id = id

    def getName(self):
        return self.__name

    def getIsotopes(self):
        return self.__isotopes

    def getId(self):
        return self.__id

class Isotope(object):
    """
    wahrsch zu umstaendlich
    """
    def __init__(self, pNr, isoNr, mass, relAb, id):
        """

        :param pNr: proton number
        :param isoNr: M+isoNr (monoisotopic = M)
        :param mass:
        :param relAb:
        """
        self.__pNr = pNr
        self.__isoNr = isoNr
        self.__mass = mass
        self.__relAb = relAb
        self.__id = id

    def getPNr(self):
        return self.__pNr

    def getNr(self):
        return self.__isoNr

    def getMass(self):
        return self.__mass

    def getRelAb(self):
        return self.__relAb

    def getId(self):
        return self.__id

    def getAll(self):
        return [self.__pNr, self.__isoNr, self.__mass, self.__relAb]


class PeriodicTableRepository(AbstractRepositoryWithItems):
    def __init__(self):
        super(PeriodicTableRepository, self).__init__('Shared_data.db', 'elements', ('name'),
                                                      {'isotopes':('pNr', 'isoNr', 'mass', 'relAb')})

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS elements (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS isotopes (
                "id"	integer PRIMARY KEY UNIQUE,
                "pNr"	integer NOT NULL ,
                "isoNr" integer NOT NULL ,
                "mass" real NOT NULL ,
                "relAb" real NOT NULL ,
                "patternId" integer NOT NULL );""")


    def createElement(self, element):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
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
        self.delete(id)