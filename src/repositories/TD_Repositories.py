import sqlite3
from os.path import join

from src.entities.IonTemplates import FragmentationPattern, FragItem, ModificationPattern, ModifiedItem
from src.repositories.AbstractRepositories import AbstractRepositoryWith2Items

class FragmentationRepository(AbstractRepositoryWith2Items):
    def __init__(self):
        #self.__conn = sqlite3.connect(dbFile)
        super(FragmentationRepository, self).__init__(join('top_down.db'), 'fragPatterns',
                                                      ("name","gain", "loss"),
                    {'fragmentTypes':('name', 'gain', 'loss', 'residue', 'radicals', 'direct', 'enabled', 'patternId'),
                     'precFragments':('name', 'gain', 'loss', 'residue', 'radicals', 'enabled', 'patternId')},
                                                      ((4,5),(4,)), ((6,),(5,)))
        #self.__conn = sqlite3.connect(':memory:')

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS fragPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "gain" text NOT NULL ,
                "loss" text NOT NULL );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS fragmentTypes (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "direct" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "patternId" integer NOT NULL );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS precFragments (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "patternId" integer NOT NULL );""")


    def createPattern(self, pattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        # try:
        patternId = self.create(pattern.getName(), pattern.getInitGain(), pattern.getInitLoss())
        self.insertItem(patternId, pattern.getItems(), 0)
        self.insertItem(patternId, pattern.getItems2(), 1)

    def updatePattern(self, pattern):
        self.update(pattern.getName(), pattern.getInitGain(), pattern.getInitLoss(), pattern.getId())
        super(FragmentationRepository, self).updatePattern(pattern)


    def getItemColumns(self):
        columns1 = super(FragmentationRepository, self).getItemColumns()
        columns1.update(
            {'Residue':"If the species is dependent on the occurence of a specific residue within the sequenceList, enter the residue",
             'Radicals':"Enter the number of radicals",
             'Direction':"Enter +1 for forward (e.g. N-/5'- terminus) or -1 for backward (e.g. C-/3'- terminus)",
             'Enabled':"Activate/Deactivate Species"})
        columns1['Name'] = 'Name of the fragment, 1. letter specifies type of fragment, optionally followed by "+" or "-".\n' \
                           + columns1['Name']
        columns2 = super(FragmentationRepository, self).getItemColumns()
        columns2.update(
            {'Residue': "If the species is dependent on the occurence of a specific residue within the sequenceList, enter the residue",
             'Radicals': "Enter the number of radicals", 'Enabled': "Activate/Deactivate Species"})
        return (columns1,columns2)

    def getPattern(self, name):
        pattern = self.get('name', name)
        listOfLists = self.getAllItems(pattern[0])
        return FragmentationPattern(pattern[1], pattern[2], pattern[3], listOfLists[0], listOfLists[1], pattern[0])

    def getAllItems(self, patternId):
        keyList = [key for key in self._itemDict.keys()]
        listOfLists = []
        listOfItems = []
        for item in self.getItems(patternId, keyList[0]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6], item[7]))
        listOfLists.append(listOfItems)
        listOfItems = []
        for item in self.getItems(patternId, keyList[1]):
            listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6]))
        listOfLists.append(listOfItems)
        return listOfLists


    """def getPatternWithObjects(self, name):
        pattern = self.get('name', name)
        listOfItemLists = self.getItemsAsObjects(pattern[0])
        return FragmentationPattern(pattern[1], pattern[2], pattern[3], listOfItemLists[0], listOfItemLists[1], pattern[0])


    def getItemsAsObjects(self, patternId):
        listOfItemLists = []
        for table in self._itemDict.keys():
            listOfItems = []
            for item in super(FragmentationRepository, self).getItems(patternId,table):
                listOfItems.append(FragItem(item))
                #listOfItems.append(FragItem(item[1], item[2], item[3], item[4], item[5], item[6]))
            listOfItemLists.append(listOfItems)
        return listOfItemLists"""



class ModificationRepository(AbstractRepositoryWith2Items):
    def __init__(self):
        super(ModificationRepository, self).__init__('top_down.db', 'modPatterns',("name","modification"),
                            {'modItems':('name', 'gain', 'loss', 'residue', 'radicals', 'chargeEffect', 'calcOcc',
                                         'enabled', 'patternId'),
                             'excluded': ('name', 'patternId')}, ((4, 5),()), ((6,7),()) )

        #self._conn = sqlite3.connect(':memory:')
        #self._conn = sqlite3.connect('test.db')

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
                                "gain" text NOT NULL ,
                                "loss" text NOT NULL ,
                                "residue" text NOT NULL ,
                                "radicals" integer NOT NULL ,
                                "chargeEffect" integer NOT NULL ,
                                "calcOcc" integer NOT NULL ,
                                "enabled" integer NOT NULL,
                                "patternId" integer NOT NULL );""")
        self._conn.cursor().execute("""
                            CREATE TABLE IF NOT EXISTS excluded (
                                "id"	integer PRIMARY KEY,
                                "name"	text NOT NULL ,
                                "patternId" integer NOT NULL);""")

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


    def updateModPattern(self, pattern):
        self.update(pattern.name, pattern.modification, pattern.id)
        self.deleteList(pattern.id, 'modItems')
        self.insertModificationItems(pattern.id, pattern)


    def deleteModPattern(self, id):
        self.deleteList(id, 'modItems')
        self.delete(id)"""

    def createPattern(self, pattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        # try:
        patternId = self.create(pattern.getName(), pattern.getModification())
        self.insertItem(patternId, pattern.getItems(), 0)
        self.insertItem(patternId, pattern.getItems2(), 1)


    def updatePattern(self, pattern):
        self.update(pattern.getName(), pattern.getModification(), pattern.getId())
        super(ModificationRepository, self).updatePattern(pattern)


    def getItemColumns(self):
        columns = super(ModificationRepository, self).getItemColumns()
        columns.update(
            {'Residue':"If the species is dependent on the occurence of a specific residue within the sequenceList, enter "
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
            listOfItems.append((item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]))
        listOfLists.append(listOfItems)
        listOfLists.append([(item[1],) for item in self.getItems(patternId, keyList[1])])
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
            #listOfItems.append(ModifiedItem(item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]))
            listOfItems.append(ModifiedItem(item))
        listOfItemLists.append(listOfItems)
        listOfItemLists += [item for item in self.getItems(patternId, keyList[1])]
        return listOfItemLists