import sqlite3

from src.GeneralRepository.AbstractProperties import *
from src.GeneralRepository.Exceptions import AlreadyPresentException


class FragItem(AbstractItem):
    def __init__(self, name, gain, loss, residue, radicals, enabled):
        super(FragItem, self).__init__(name, gain, loss, enabled)
        self._residue = residue
        self._radicals = radicals


    def getResidue(self):
        return self._residue

    def getRadicals(self):
        return self._radicals


"""class PrecursorFragmentationPattern(object):
    def __init__(self, fragmentTypes):
        self.fragmentTypes = fragmentTypes"""


class FragmentationPattern(PatternWithItems):
    def __init__(self, name, fragmentTypes, precursorFragments, id):
        super(FragmentationPattern, self).__init__(name, fragmentTypes,id, [4])
        self.__precursorFragments = precursorFragments

    def getPrcFragments(self):
        return self.__precursorFragments


class FragmentationRepository(AbstractRepositoryWithItems):
    def __init__(self):
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
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "enabled" integer NOT NULL,
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


    """def createFragPattern(self, fragmentationPattern):
        try:
            self.insertFragments(self.create((fragmentationPattern.name,)), fragmentationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(fragmentationPattern.name)


    def insertFragments(self, patternId, fragmentationPattern):
        for item in fragmentationPattern.fragmentTypes:
            self.createItem('fragmentTypes', item.getAll() + [patternId])
        for item in fragmentationPattern.precursorFragments:
            self.createItem('precFragments', item.getAll() + [patternId])


        def insertPrecItems(self, precFragment):
        try:
            self.createItem('precFragments', precFragment.getAll())
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(precFragment.getName())


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

    def getPrecFragments(self):
        return PrecursorFragmentationPattern(self.getFragments(None))


    def updatePattern(self, fragPattern):
        self.update(fragPattern.name, fragPattern.id)
        self.deleteAllItems(fragPattern.id, 'precFragments')
        self.insertFragments(fragPattern.id, fragPattern)


    def updatePrecFragment(self, precFragPattern):
        cur = self._conn.cursor()
        sql = 'UPDATE precFragments SET ' + '=?, '.join(self._itemDict['precFragments']) + '=? WHERE id=?'
        cur.execute(sql, precFragPattern.fragmentTypes.getAll(), precFragPattern.id)
        self._conn.commit()


    def deleteFragPattern(self, id):
        self.deleteAllItems(id)
        self.delete(id)

    def deletePrecFragment(self, id):
        cur = self._conn.cursor()
        cur.execute('DELETE FROM precFragments WHERE id=?', (id,))"""


    def getItemColumns(self):
        return super(FragmentationRepository, self).getItemColumns()+['Residue', 'Radicals', 'Enabled']


    def getPattern(self, name):
        pattern = self.get('name', name)
        listOfLists = self.getAllItems(pattern[0])
        return FragmentationPattern(pattern[1], listOfLists[0], listOfLists[1], pattern[0])

    def getAllItems(self, patternId):
        listOfLists = []
        for table in self._itemDict.keys():
            listOfItems = []
            for item in self.getItems(patternId, table):
                listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6]))
            listOfLists.append(listOfItems)
        return listOfLists


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        listOfItemLists = self.getItemsAsObjects(pattern[0])
        return FragmentationPattern(pattern[1], listOfItemLists[0], listOfItemLists[1], pattern[0])


    def getItemsAsObjects(self, patternId):
        listOfItemLists = []
        for table in self._itemDict.keys():
            listOfItems = []
            for item in super(FragmentationRepository, self).getItems(patternId,table):
                listOfItems.append(FragItem(item[1], item[2], item[3], item[4], item[5], item[6]))
            listOfItemLists.append(listOfItems)
        return listOfItemLists