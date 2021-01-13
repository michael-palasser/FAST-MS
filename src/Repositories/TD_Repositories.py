from src.Entities.IonEntities import FragmentationPattern, FragItem, ModificationPattern, ModifiedItem
from src.Repositories.AbstractRepositories import AbstractRepositoryWithItems2

class FragmentationRepository(AbstractRepositoryWithItems2):
    def __init__(self):
        #self.__conn = sqlite3.connect(dbFile)
        super(FragmentationRepository, self).__init__('TD_data.db', 'fragPatterns',("name",),
                    {'fragmentTypes':('name', 'gain', 'loss', 'residue', 'radicals', 'enabled', 'patternId'),
                     'precFragments':('name', 'gain', 'loss', 'residue', 'radicals', 'enabled', 'patternId')},
                                                      ((4,),(4,)), ((5,),(5,)))
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
        columns = super(FragmentationRepository, self).getItemColumns()
        columns.update(
            {'Residue':"If the species is dependent on the occurence of a specific residue within the sequence, enter the residue",
             'Radicals':"Enter the number of radicals", 'Enabled':"Activate/Deactivate Species"})
        return (columns,columns)


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




class ModificationRepository(AbstractRepositoryWithItems2):
    def __init__(self):
        super(ModificationRepository, self).__init__('TD_data.db', 'modPatterns',("name","modification"),
                            {'modItems':('name', 'gain', 'loss', 'residue', 'radicals', 'chargeEffect', 'calcOcc',
                                         'enabled', 'patternId'),
                             'excluded': ('name')}, ((4, 5),()), ((6,7),()) )

    def makeTables(self):
        self._conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS modPatterns (
                        "id"	integer PRIMARY KEY UNIQUE ,
                        "name"	text NOT NULL UNIQUE,
                        "modification" text NOT NULL );""")
        self._conn.cursor().execute("""
                            CREATE TABLE IF NOT EXISTS modItems (
                                "id"	integer PRIMARY KEY,
                                "name"	text NOT NULL ,
                                "enabled" integer NOT NULL,
                                "gain" text NOT NULL ,
                                "loss" text NOT NULL ,
                                "residue" text NOT NULL ,
                                "radicals" integer NOT NULL ,
                                "chargeEffect" integer NOT NULL ,
                                 "calcOcc" integer NOT NULL ,
                                "patternId" integer NOT NULL );""")
        self._conn.cursor().execute("""
                            CREATE TABLE IF NOT EXISTS exluded (
                                "id"	integer PRIMARY KEY,
                                "name"	text NOT NULL );""")

    """def createModPattern(self, modificationPattern):
        try:
            self.insertModificationItems(self.create(modificationPattern.name, modificationPattern.modification),
                                         modificationPattern)
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(modificationPattern.name)


    def insertModificationItems(self, patternId, modificationPattern):
        for item in modificationPattern.listOfMod:
            self.createItem('modItems',item.getAll() + [1, patternId])
        for item in modificationPattern.listOfContaminants:
            self.createItem('modItems',item.getAll() + [0, patternId])


    def getModPattern(self, name):
        pattern = self.get('name',name)
        return ModificationPattern(pattern[1], pattern[2], self.getModItems(pattern[0], 1),
                                   self.getModItems(pattern[0], 0), pattern[0])

    def getModItems(self, patternId, included):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM modItems WHERE patternId=? AND included=?", (patternId, included))
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(ModifiedItem(item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[0]))
        return listOfItems

    def getAllModPatterns(self):
        listOfPatterns = list()
        for pattern in self.getAll():
            listOfPatterns.append(ModificationPattern(pattern[1], pattern[2], self.getModItems(pattern[0], 1),
                                   self.getModItems(pattern[0], 0), pattern[0]))
        return listOfPatterns


    def updateModPattern(self, modPattern):
        self.update(modPattern.name, modPattern.modification, modPattern.id)
        self.deleteList(modPattern.id, 'modItems')
        self.insertModificationItems(modPattern.id, modPattern)


    def deleteModPattern(self, id):
        self.deleteList(id, 'modItems')
        self.delete(id)"""

    def getItemColumns(self):
        columns = super(ModificationRepository, self).getItemColumns()
        columns.update(
            {'Residue':"If the species is dependent on the occurence of a specific residue within the sequence, enter "
            "the residue", 'Radicals':"Enter the number of radicals",
            'z-Effect':"If the modification alters the charge of modified fragment enter an (empiric) number of the extent",
            'calcOcc':'Should the modification be used for occupancy calculation?',
            'Enabled':"Activate/Deactivate Modification"})
        return (columns,{'Name': 'Modification to be excluded'})



    def getPattern(self, name):
        pattern = self.get('name', name)
        listOfLists = self.getAllItems(pattern[0])
        return ModificationPattern(pattern[1], pattern[2], listOfLists[0], listOfLists[1], pattern[0])

    def getAllItems(self, patternId):
        keyList = [key for key in self._itemDict.keys()]
        listOfLists = []
        #for table in self._itemDict.keys():
        listOfItems = []
        for item in self.getItems(patternId, keyList[0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6], item[7]))
        listOfLists.append(listOfItems)
        listOfLists += [item for item in self.getItems(patternId, keyList[1])]
        return listOfLists


    def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        listOfItemLists = self.getItemsAsObjects(pattern[0])
        return ModificationPattern(pattern[1], pattern[2], listOfItemLists[0], listOfItemLists[1], pattern[0])


    def getItemsAsObjects(self, patternId):
        keyList = [key for key in self._itemDict.keys()]
        listOfItemLists = []
        #for table in self._itemDict.keys():
        listOfItems = []
        for item in super(ModificationRepository, self).getItems(patternId, keyList[0]):
            listOfItems.append(ModifiedItem(item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]))
        listOfItemLists.append(listOfItems)
        listOfItemLists += [item for item in self.getItems(patternId, keyList[1])]
        return listOfItemLists