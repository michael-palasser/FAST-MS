from os.path import join

from src.entities.GeneralEntities import Makromolecule, Monomere
from src.repositories.AbstractRepositories import AbstractRepositoryWithItems


class MoleculeRepository(AbstractRepositoryWithItems):
    def __init__(self):
        #self.__conn = sqlite3.connect(dbFile)
        super(MoleculeRepository, self).__init__(join('shared.db'), 'molecules',
                                                 ("name",),
                                                 {"monomeres": ('name', 'formula','patternId')},(),())

    def makeTables(self):
        self._conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS molecules (
                        "id"	integer PRIMARY KEY UNIQUE ,
                        "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS monomeres (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL,
                "formula" text NOT NULL ,
                "patternId" text NOT NULL );""")

    def getItemColumns(self):
        return {'Name':'First Letter must be uppercase, all other letters must be lowercase',
                'Formula':'molecular formula of monomer'}

    def getPattern(self, name):
        pattern = self.get('name', name)
        return Makromolecule(pattern[1], self.getItems(pattern[0], [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        listOfItems = list()
        for item in super(MoleculeRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2])) #, item[3], item[4], item[5]) )
        return listOfItems


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        return Makromolecule(pattern[1], self.getItemsAsObjects(pattern[0]), pattern[0])

    def getItemsAsObjects(self,patternId):
        listOfItems = list()
        for item in super(MoleculeRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(Monomere(item[1], item[2]) )
        return listOfItems




    """def createMonomere(self, monomere):
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
        self.update(monomere.getName(),monomere.getFormula(), monomere.getId)"""

    """def deleteMonomere(self, monomere):
        cur = self.__conn.cursor()
        cur.execute(''' DELETE FROM monomeres WHERE name=?''', (monomere.getName(),))"""