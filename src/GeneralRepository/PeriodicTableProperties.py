'''
Created on 29 Dec 2020

@author: michael
'''
from src.GeneralRepository.AbstractProperties import AbstractRepository


class Element(object):
    def __init__(self, name, isotopes, id):
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
    def __init__(self, name, nr, mass, relAb):
        """

        :param name:
        :param nr: M+nr (monoisotopic = M)
        :param mass:
        :param relAb:
        """
        self.__name = name
        self.__nr = nr
        self.__mass = mass
        self.__relAb = relAb

    def getName(self):
        return self.__name

    def getNr(self):
        return self.__nr

    def getMass(self):
        return self.__mass

    def getRelAb(self):
        return self.__relAb


class PeriodicTableRepository(AbstractRepository):
    def __init__(self):
        super(PeriodicTableRepository, self).__init__('elements', ('name'))

    #ToDo