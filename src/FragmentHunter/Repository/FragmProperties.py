import sqlite3

from src.GeneralRepository.AbstractProperties import *
from src.GeneralRepository.Exceptions import AlreadyPresentException


class FragItem(AbstractItem):
    def __init__(self, name, enabled, gain, loss, residue, radicals, id):
        super(FragItem, self).__init__(name, enabled, gain, loss, id)
        self._residue = residue
        self._radicals = radicals

    def getAll(self):
        return super(FragItem, self).getAll() + [self._residue, self._radicals]

    def getResidue(self):
        return self._residue

    def getRadicals(self):
        return self._radicals


"""class PrecursorFragmentationPattern(object):
    def __init__(self, fragmentTypes):
        self.fragmentTypes = fragmentTypes"""


class FragmentationPattern(object):
    def __init__(self, name, fragmentTypes, precursorFragments, id):
        self.name = name
        self.fragmentTypes = fragmentTypes
        self.precursorFragments = precursorFragments
        self.id = id



class FragmentationRepository(AbstractRepositoryWithItems):
    def __init__(self, dbFile):
        #self.__conn = sqlite3.connect(dbFile)
        super(FragmentationRepository, self).__init__('TD_data.db', 'fragPatterns',("name",),
                    {'fragmentTypes':('name', 'enabled', 'gain', 'loss', 'residue', 'radicals', 'patternId'),
                     'precFragments':('name', 'enabled', 'gain', 'loss', 'residue', 'radicals', 'patternId')})
        #self.__conn = sqlite3.connect(':memory:')

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS fragPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS fragmentTypes (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "enabled" integer NOT NULL,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "patternId" integer NOT NULL );""")
        self._conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS precFragments (
                        "id"	integer PRIMARY KEY UNIQUE,
                        "name"	text NOT NULL UNIQUE ,
                        "enabled" integer NOT NULL,
                        "gain" text NOT NULL ,
                        "loss" text NOT NULL ,
                        "residue" text NOT NULL ,
                        "radicals" integer NOT NULL ,
                        "patternId" integer NOT NULL );""")


    def createFragPattern(self, fragmentationPattern):
        try:
            self.insertFragments(self.create((fragmentationPattern.name,)), fragmentationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(fragmentationPattern.name)


    def insertFragments(self, patternId, fragmentationPattern):
        for item in fragmentationPattern.fragmentTypes:
            self.createItem('fragmentTypes', item.getAll() + [patternId])
        for item in fragmentationPattern.precursorFragments:
            self.createItem('precFragments', item.getAll() + [patternId])


        """def insertPrecItems(self, precFragment):
        try:
            self.createItem('precFragments', precFragment.getAll())
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(precFragment.getName())"""


    def getFragPattern(self, name):
        pattern = self.get('name',name)
        return FragmentationPattern(pattern[1], self.getFragments('fragmentTypes', pattern[0]),
                                    self.getFragments('precFragments', pattern[0]), pattern[0])

    def getFragments(self, patternId, table):
        listOfItems = list()
        for item in self.getAllItems(table, patternId):
            listOfItems.append(FragItem(item[1], item[2], item[3], item[4], item[5], item[6], item[0]))
        return listOfItems

    def getAllPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(FragmentationPattern(pattern[1], self.getFragments('fragmentTypes', pattern[0]),
                                                       self.getFragments('precFragments', pattern[0]), pattern[0]))
        return listOfPatterns

    """def getPrecFragments(self):
        return PrecursorFragmentationPattern(self.getFragments(None))"""


    def updateFragPattern(self, fragPattern):
        self.update(fragPattern.name, fragPattern.id)
        self.deleteList(fragPattern.id, 'fragmentTypes')
        self.deleteList(fragPattern.id, 'precFragments')
        self.insertFragments(fragPattern.id, fragPattern)


        """def updatePrecFragment(self, precFragPattern):
        cur = self._conn.cursor()
        sql = 'UPDATE precFragments SET ' + '=?, '.join(self._itemDict['precFragments']) + '=? WHERE id=?'
        cur.execute(sql, precFragPattern.fragmentTypes.getAll(), precFragPattern.id)
        self._conn.commit()"""


    def deleteFragPattern(self, id):
        self.deleteList(id, 'fragmentTypes')
        self.deleteList(id, 'precFragments')
        self.delete(id)

    def deletePrecFragment(self, id):
        cur = self._conn.cursor()
        cur.execute('DELETE FROM precFragments WHERE id=?', (id,))




"""if __name__ == '__main__':
    pattern = FragmentationPattern("CAD_CMCT","CMCT",
                                   [FragItem("a","","H1O3P1","",0), FragItem("c","","","",0)],
                                   [ModifiedItem("CMCT", "C14H25N3O","","",0,0.5)],[])
    Repository = FragmentationRepository("Fragmentation_test3.db")
    try:
        Repository.makeTable()
        Repository.createElement(pattern)
        pattern2 = Repository.getModPattern("CAD_CMCT")
    finally:
        Repository.close()"""