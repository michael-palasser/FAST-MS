import sqlite3

class Item(object):
    def __init__(self, name, enabled, gain, loss, residue, radicals):
        self.name = name
        self.enabled = enabled
        self.gain = gain
        self.loss = loss
        self.residue = residue
        self.radicals = radicals

    def getAll(self):
        return [self.name, self.enabled, self.gain, self.loss, self.residue, self.radicals]

class ModifiedItem(Item):
    def __init__(self,name,enabled, gain, loss, residue, radicals, zEffect):
        super(ModifiedItem, self).__init__(name, enabled, gain, loss, residue, radicals)
        self.zEffect = zEffect

    def getAll(self):
        return super(ModifiedItem, self).getAll() + [self.zEffect]

class PrecursorFragmentationPattern(object):
    def __init__(self, fragmentTypes):
        self.fragmentTypes = fragmentTypes

class FragmentationPattern(PrecursorFragmentationPattern):
    def __init__(self, name, fragmentTypes):
        super(FragmentationPattern, self).__init__(fragmentTypes)
        self.name = name

class ModificationPattern(PrecursorFragmentationPattern):
    def __init__(self, name, modification, listOfMod, listOfOthers):
        self.name = name
        self.modification = modification
        self.listOfMod = listOfMod
        self.listOfOthers = listOfOthers


class FragmentationRepository(object):
    def __init__(self, dbFile):
        self.__conn = sqlite3.connect(dbFile)
        #self.__conn = sqlite3.connect(':memory:')

    def makeTables(self):
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS fragPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE);""")
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS fragmentTypes (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "enabled" integer NOT NULL,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "patternId" integer NOT NULL );""")
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS modPatterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "modification" text NOT NULL );""")
        self.__conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS modItems (
                        "id"	integer PRIMARY KEY,
                        "name"	text NOT NULL ,
                        "enabled" integer NOT NULL,
                        "gain" text NOT NULL ,
                        "loss" text NOT NULL ,
                        "residue" text NOT NULL ,
                        "radicals" integer NOT NULL ,
                        "chargeEffect" integer NOT NULL ,
                         "included" integer NOT NULL ,
                        "patternId" integer NOT NULL );""")

        self.__conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS precFragments (
                        "id"	integer PRIMARY KEY UNIQUE,
                        "name"	text NOT NULL ,
                        "enabled" integer NOT NULL,
                        "gain" text NOT NULL ,
                        "loss" text NOT NULL ,
                        "residue" text NOT NULL ,
                        "radicals" integer NOT NULL );""")

    def createFragPattern(self, fragmentationPattern):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO fragPatterns(name)
                      VALUES(?) '''
        try:
            cur.execute(sql, (fragmentationPattern.name,))
            self.__conn.commit()
            self.insertFragmentTypes(cur.lastrowid, fragmentationPattern)
        except sqlite3.IntegrityError:
            raise Exception(fragmentationPattern.name,"already present")

    def insertFragmentTypes(self, patternId, fragmentationPattern):
        for item in fragmentationPattern.fragmentTypes:
            self.createFragItem(item, patternId)


    def createFragItem(self, item, patternId):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO fragmentTypes(name, enabled, gain, loss, residue, radicals, patternId)
                      VALUES(?, ?, ?, ?, ?, ?,?) '''
        values = item.getAll() + [patternId]
        cur.execute(sql, values)
        self.__conn.commit()
        return cur.lastrowid


    def createModPattern(self, modificationPattern):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO modPatterns(name, modification)
                      VALUES(?,?) '''
        try:
            cur.execute(sql, (modificationPattern.name, modificationPattern.modification))
            self.__conn.commit()
            self.insertModificationItems(cur.lastrowid, modificationPattern)
        except sqlite3.IntegrityError:
            raise Exception(modificationPattern.name, "already present")


    def insertModificationItems(self, patternId, modificationPattern):
        for item in modificationPattern.listOfMod:
            self.createModItem(item, 1, patternId)
        for item in modificationPattern.listOfOthers:
            self.createModItem(item, 0, patternId)


    def createModItem(self, item, included, patternId):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO modItems(name, enabled, gain, loss, residue, radicals, chargeEffect, included, patternId)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?) '''
        values = item.getAll() + [included, patternId]
        cur.execute(sql, values)
        self.__conn.commit()
        return cur.lastrowid

    def insertPrecItems(self, precFragPattern):
        for item in precFragPattern.fragmentTypes:
            self.createPrecItem(item)


    def createPrecItem(self, item):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO precFragments(name, enabled, gain, loss, residue, radicals, patternId)
                      VALUES(?, ?, ?, ?, ?, ?,?) '''
        cur.execute(sql, item.getAll())
        self.__conn.commit()
        return cur.lastrowid


    def getFragPattern(self, name):
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM fragPatterns WHERE name=?",(name,))
        pattern = cur.fetchall()[0]
        return FragmentationPattern(pattern[1], self.getItems(pattern[0]))

    def getItems(self, patternId):
        cur = self.__conn.cursor()
        if patternId != None:
            cur.execute("SELECT * FROM fragmentTypes WHERE patternId=?",(patternId,))
        else:
            cur.execute("SELECT * FROM fragmentTypes")
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(Item(item[1],item[2],item[3],item[4],item[5],item[6]))
        return listOfItems


    def getModPattern(self, name):
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM modPatterns WHERE name=?", (name,))
        pattern = cur.fetchall()[0]
        return ModificationPattern(pattern[1], pattern[2], self.getModItems(pattern[0], 1), self.getModItems(pattern[0], 0))

    def getModItems(self, patternId, included):
        cur = self.__conn.cursor()
        cur.execute("""SELECT * FROM modItems WHERE patternId=? AND included=?""",(patternId,included))
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(ModifiedItem(item[1],item[2],item[3],item[4],item[5],item[6],item[7]))
        return listOfItems

    def getPrecFragments(self):
        return PrecursorFragmentationPattern(self.getItems(None))


    def updateFragPattern(self, fragPattern):
        cur = self.__conn.cursor()
        cur.execute("""SELECT id FROM fragPatterns WHERE name=?""",(fragPattern.name,))
        patternId = cur.fetchone()[0]
        self.deleteLists(patternId, (fragPattern.fragmentTypes,))
        self.insertFragmentTypes(patternId, fragPattern)


    def updateModPattern(self, modPattern):
        cur = self.__conn.cursor()
        cur.execute("""SELECT id FROM modPatterns WHERE name=?""",(modPattern.name,))
        patternId = cur.fetchone()[0]
        self.deleteLists(patternId, (modPattern.listOfMod, modPattern.listOfOthers))
        self.insertModificationItems(patternId, modPattern)

    def updatePrecFragments(self, precFragPattern):
        cur = self.__conn.cursor()
        cur.execute("DELETE * FROM precFragments")
        self.__conn.commit()
        self.insertPrecItems(precFragPattern)

    def deleteLists(self, patternId, tableNames):
        cur = self.__conn.cursor()
        for tableName in tableNames:
            sql = "DELETE FROM " + tableName + " WHERE patternId=?"
            cur.execute(sql,(patternId,))
            self.__conn.commit()

    def deleteFragPattern(self, fragPattern):
        cur = self.__conn.cursor()
        cur.execute("""SELECT id FROM fragPatterns WHERE name=?""", (fragPattern.name,))
        patternId = cur.fetchone()[0]
        self.deleteLists(patternId, (fragPattern.fragmentTypes,))
        cur.execute("DELETE FROM fragPatterns WHERE id=?",(patternId,))
        #self.__conn.commit()

    def deleteModPattern(self, modPattern):
        cur = self.__conn.cursor()
        cur.execute("""SELECT id FROM fragPatterns WHERE name=?""", (modPattern.name,))
        patternId = cur.fetchone()[0]
        self.deleteLists(patternId, (modPattern.listOfMod, modPattern.listOfOthers))
        cur.execute("DELETE FROM fragPatterns WHERE id=?",(patternId,))
        #self.__conn.commit()


    def close(self):
        self.__conn.close()


"""if __name__ == '__main__':
    pattern = FragmentationPattern("CAD_CMCT","CMCT",
                                   [Item("a","","H1O3P1","",0), Item("c","","","",0)],
                                   [ModifiedItem("CMCT", "C14H25N3O","","",0,0.5)],[])
    repository = FragmentationRepository("Fragmentation_test3.db")
    try:
        repository.makeTables()
        repository.createFragPattern(pattern)
        pattern2 = repository.getFragPattern("CAD_CMCT")
    finally:
        repository.close()"""