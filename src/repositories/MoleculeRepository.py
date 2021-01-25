from os.path import join

from src.entities.GeneralEntities import Makromolecule, BuildingBlock
from src.repositories.AbstractRepositories import AbstractRepositoryWithItems


class MoleculeRepository(AbstractRepositoryWithItems):
    def __init__(self):
        super(MoleculeRepository, self).__init__(join('shared.db'), 'molecules',
                                                 ("name", "gain", "loss"),
                                                 {"monomeres": ('name', 'formula', 'acidity','patternId')},(2,),())

    def makeTables(self):
        self._conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS molecules (
                        "id"	integer PRIMARY KEY UNIQUE ,
                        "name"	text NOT NULL UNIQUE ,
                        "gain"	text NOT NULL,
                        "loss"	text NOT NULL);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS monomeres (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL,
                "formula" text NOT NULL ,
                "acidity" real NOT NULL ,
                "patternId" text NOT NULL );""")

    def createPattern(self, pattern):
        self.insertItems(self.create(pattern.getName(), pattern.getGain(), pattern.getLoss()), pattern.getItems(), 0)

    def updatePattern(self, pattern):
        self.update(pattern.getName(), pattern.getGain(), pattern.getLoss(), pattern.getId())
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)

    def getItemColumns(self):
        return {'Name':'First Letter must be uppercase, all other letters must be lowercase',
                'Formula':'molecular formula of monomer',
                'Acidity':'Enter a positive value for acidic monomers or a negative for basic ones'} #ToDo: which value

    def getPattern(self, name):
        pattern = self.get('name', name)
        return Makromolecule(pattern[1], pattern[2], pattern[3], self.getItems(pattern[0],
                                               [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        listOfItems = list()
        for item in super(MoleculeRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3])) #, item[3], item[4], item[5]) )
        return listOfItems
