'''
Created on 15 Aug 2020

@author: michael
'''
import sqlite3
from re import findall

class Sequence(object):
    def __init__(self, name, sequenceString, molecule, pse):
        """
        :param name: String
        :param sequence: String
        :param molecule: String (RNA, DNA, P)
        :param pse: String (which periodic table should be applied)
        """
        self.__name = name
        self.__sequenceString = sequenceString
        self.__molecule = molecule
        self.__pse = pse

    def getName(self):
        return self.__name

    def getSequence(self):
        return findall('[A-Z][^A-Z]*', self.__sequenceString)

    def getMolecule(self):
        return self.__molecule

    def getPSE(self):
        return self.__pse



class SequenceRepository(object):
    def __init__(self, dbFile):
        self.__conn = sqlite3.connect(dbFile)

    def makeTables(self):
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "sequence" text NOT NULL ,
                "molecule" text NOT NULL ,
                "pse" text NOT NULL);""")

    def addSequence(self, sequence):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO sequences(name, sequence, molecule, pse)
                         VALUES(?,?,?,?) '''
        try:
            cur.execute(sql, (sequence.getName(), sequence.getSequence(), sequence.getMolecule(), sequence.getPSE()))
            self.__conn.commit()
        except sqlite3.IntegrityError:
            raise Exception(sequence.getName(), "already present")

    def getSequence(self, name):
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM sequences WHERE name=?", (name,))
        sequence = cur.fetchall()[0]
        return Sequence(sequence[1], sequence[2], sequence[3], sequence[4])

    def updateSequence(self):
        pass

    def deleteSequenc(self):
        pass
