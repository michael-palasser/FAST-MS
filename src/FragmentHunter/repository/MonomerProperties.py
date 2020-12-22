import sqlite3


class Monomere(object):
    def __init__(self, name, formula, molecule):
        self.__name = name
        self.__formula = formula
        self.__molecule = molecule

    def getName(self):
        return self.__name

    def getFormula(self):
        return self.__formula

    def getMolecule(self):
        return self.__molecule


class MonomereRepository(object):
    def __init__(self, dbFile):
        self.__conn = sqlite3.connect(dbFile)

    def makeTables(self):
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS monomeres (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "formula" text NOT NULL ,
                "molecule" text NOT NULL );""")

    def createMonomere(self, monomere):
        if (not monomere.getName()[0].isupper()) or monomere.getName()[1:].isupper():
            raise Exception("First case of monomere name must be upper case, all other letters must be lowercase")
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO monomeres(name, formula, molecule)
                              VALUES(?, ?, ?) '''
        try:
            cur.execute(sql, (monomere.getName(),monomere.getFormula(), monomere.getMolecule()))
            self.__conn.commit()
        except sqlite3.IntegrityError:
            raise Exception(monomere.getName(),"already present")

    def getMonomeres(self, molecule):
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM monomeres WHERE molecule=?", (molecule,))
        listOfMonomeres = list()
        for item in cur.fetchall()[0]:
            listOfMonomeres.append(Monomere(item[1], item[2], item[3]))
        return listOfMonomeres

    def updateMonomere(self, monomere):
        cur = self.__conn.cursor()
        sql = ''' UPDATE monomeres SET formula=? WHERE name=?'''
        cur.execute(sql, (monomere.getFormula(), monomere.getName()))
        self.__conn.commit()

    def deleteMonomere(self, monomere):
        cur = self.__conn.cursor()
        cur.execute(''' DELETE FROM monomeres WHERE name=?''', (monomere.getName(),))