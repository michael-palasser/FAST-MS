import sqlite3
from os.path import join

from src.entities.IonTemplates import FragmentationPattern, FragItem, ModificationPattern, ModifiedItem
from src.repositories.AbstractRepositories import AbstractRepositoryWith2Items

class FragmentationRepository(AbstractRepositoryWith2Items):
    def __init__(self):
        #self.__conn = sqlite3.connect(dbFile)
        super(FragmentationRepository, self).__init__(join('top_down.db'), 'fragPatterns',
                                                      ("name",),
                    {'fragmentTypes':('name', 'gain', 'loss', 'residue', 'radicals', 'direct', 'enabled', 'patternId'),
                     'precFragments':('name', 'gain', 'loss', 'residue', 'radicals', 'enabled', 'patternId')},
                                                      ((4,5),(4,)), ((6,),(5,)))
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
        patternId = self.create(pattern.getName())
        self.insertItems(patternId, pattern.getItems(), 0)
        self.insertItems(patternId, pattern.getItems2(), 1)

    def updatePattern(self, pattern):
        self.update(pattern.getName(), pattern.getId())
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
        return FragmentationPattern(pattern[1], listOfLists[0], listOfLists[1], pattern[0])

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


    def createPattern(self, pattern):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        # try:
        patternId = self.create(pattern.getName(), pattern.getModification())
        self.insertItems(patternId, pattern.getItems(), 0)
        self.insertItems(patternId, pattern.getItems2(), 1)


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