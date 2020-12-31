import sqlite3

from src.GeneralRepository.AbstractProperties import AbstractRepository
from src.GeneralRepository.Exceptions import AlreadyPresentException


class Monomere(object):
    def __init__(self, name, formula, molecule):
        self.__name = name
        self.__formula = formula
        self.__molecule = molecule
        self.__id = id

    def getName(self):
        return self.__name

    def getFormula(self):
        return self.__formula

    def getMolecule(self):
        return self.__molecule

    def getId(self):
        self.__id = id

class MonomereRepository(AbstractRepository):
    def __init__(self):
        #self.__conn = sqlite3.connect(dbFile)
        super(MonomereRepository, self).__init__('Shared_data.db', 'monomeres', ("name", "formula", "molecule"))

    def makeTable(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS monomeres (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "formula" text NOT NULL ,
                "molecule" text NOT NULL );""")

    def createMonomere(self, monomere):
        #ToDo: gehoert eig nicht hierher sondern in hoehere Schicht
        if (not monomere.getName()[0].isupper()) or monomere.getName()[1:].isupper():
            raise Exception("First case of monomere name must be upper case, all other letters must be lowercase")
        try:
            self.create(monomere.getName(),monomere.getFormula(), monomere.getMolecule())
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(monomere.getName())


    def getMonomeres(self, molecule):
        listOfMonomeres = list()
        for item in self.get('molecule', molecule):
            listOfMonomeres.append(Monomere(item[1], item[2], item[3]))
        return listOfMonomeres


    def updateMonomere(self, monomere):
        self.update(monomere.getName(),monomere.getFormula(), monomere.getId)

    """def deleteMonomere(self, monomere):
        cur = self.__conn.cursor()
        cur.execute(''' DELETE FROM monomeres WHERE name=?''', (monomere.getName(),))"""