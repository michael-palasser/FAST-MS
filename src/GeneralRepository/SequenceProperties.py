'''
Created on 15 Aug 2020

@author: michael
'''
import sqlite3
from re import findall

from src.GeneralRepository.AbstractProperties import AbstractRepository


class Sequence(object):
    def __init__(self, name, sequenceString, molecule, id):
        """
        :param name: String
        :param sequence: String
        :param molecule: String (RNA, DNA, P)
        :param pse: String (which periodic table should be applied)
        """
        self.__name = name
        self.__sequenceString = sequenceString
        self.__molecule = molecule
        self.__id = id

    def getName(self):
        return self.__name

    def getSequence(self):
        return findall('[A-Z][^A-Z]*', self.__sequenceString)

    def getMolecule(self):
        return self.__molecule

    def getId(self):
        return self.__id


class SequenceRepository(AbstractRepository):
    def __init__(self):
        super(SequenceRepository, self).__init__('sequences', ('name', 'sequence', 'molecule'))

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "sequence" text NOT NULL ,
                "molecule" text NOT NULL );""")

    def addSequence(self, sequence):
        try:
            self.create(sequence.getName(), sequence.getSequence(), sequence.getMolecule())
        except sqlite3.IntegrityError:
            raise Exception(sequence.getName(), "already present")

    def getSequence(self, name):
        sequenceTuple = self.get('name', name)
        return Sequence(sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[4])

    def updateSequence(self, sequence):
        self.update(sequence.getName(), sequence.getSequence(), sequence.getMolecule(), sequence.getId())

    """def deleteSequence(self):
        pass"""
