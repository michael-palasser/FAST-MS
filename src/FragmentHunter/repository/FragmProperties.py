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



class FragmentationPattern(object):
    def __init__(self, name, modification, listOfUnmod, listOfMod, listOfOthers):
        self.name = name
        self.modification = modification
        self.listOfUnmod = listOfUnmod
        self.listOfMod = listOfMod
        self.listOfOthers = listOfOthers



class FragmentationRepository(object):
    def __init__(self, dbFile):
        self.__conn = sqlite3.connect(dbFile)
        #self.__conn = sqlite3.connect(':memory:')

    def makeTables(self):
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "modification" text NOT NULL );""")
        self.__conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS items (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "enabled" integer NOT NULL,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "patternId" integer NOT NULL );""")
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

    def createPattern(self, fragmentationPattern):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO patterns(name, modification)
                      VALUES(?,?) '''
        try:
            cur.execute(sql, (fragmentationPattern.name, fragmentationPattern.modification))
            self.__conn.commit()
            self.insertData(cur.lastrowid, fragmentationPattern)
        except sqlite3.IntegrityError:
            raise Exception(fragmentationPattern.name,"already present")

    def insertData(self, patternId, fragmentationPattern):
        for item in fragmentationPattern.listOfUnmod:
            self.createItem(item, patternId)
        for item in fragmentationPattern.listOfMod:
            self.createModItem(item, 1, patternId)
        for item in fragmentationPattern.listOfOthers:
            self.createModItem(item, 0, patternId)


    def createItem(self, item, patternId):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO items(name, enabled, gain, loss, residue, radicals, patternId)
                      VALUES(?, ?, ?, ?, ?, ?,?) '''
        values = item.getAll() + [patternId]
        cur.execute(sql, values)
        self.__conn.commit()
        return cur.lastrowid

    def createModItem(self, item, included, patternId):
        cur = self.__conn.cursor()
        sql = ''' INSERT INTO modItems(name, enabled, gain, loss, residue, radicals, chargeEffect, included, patternId)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?) '''
        values = item.getAll() + [included, patternId]
        cur.execute(sql, values)
        self.__conn.commit()
        return cur.lastrowid


    def getPattern(self, name):
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM patterns WHERE name=?",(name,))
        pattern2 = cur.fetchall()
        pattern = pattern2[0]
        #pattern = cur.fetchall()[0]
        return FragmentationPattern(pattern[1], pattern[2], self.getItems(pattern[0]),
                                           self.getModItems(pattern[0],1), self.getModItems(pattern[0],0))

    def getItems(self, patternId):
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM items WHERE patternId=?",(patternId,))
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(Item(item[1],item[2],item[3],item[4],item[5],item[6]))
        return listOfItems

    def getModItems(self, patternId, included):
        cur = self.__conn.cursor()
        cur.execute("""SELECT * FROM modItems WHERE patternId=? AND included=?""",(patternId,included))
        listOfItems = list()
        for item in cur.fetchall():
            listOfItems.append(ModifiedItem(item[1],item[2],item[3],item[4],item[5],item[6],item[7]))
        return listOfItems


    def updatePattern(self, fragmentationPattern):
        cur = self.__conn.cursor()
        cur.execute("""SELECT id FROM patterns WHERE name=?""",(fragmentationPattern.name,))
        patternId = cur.fetchone()[0]
        self.deleteLists(patternId)
        self.insertData(patternId, fragmentationPattern)

    def deleteLists(self, patternId):
        cur = self.__conn.cursor()
        cur.execute("DELETE FROM items WHERE patternId=?",(patternId,))
        self.__conn.commit()
        cur.execute("DELETE FROM modItems WHERE patternId=?",(patternId,))
        self.__conn.commit()

    def deletePattern(self, fragmentationPattern):
        cur = self.__conn.cursor()
        cur.execute("""SELECT id FROM patterns WHERE name=?""", (fragmentationPattern.name,))
        patternId = cur.fetchone()[0]
        self.deleteLists(patternId)
        cur.execute("DELETE FROM patterns WHERE id=?",(patternId,))
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
        repository.createPattern(pattern)
        pattern2 = repository.getPattern("CAD_CMCT")
    finally:
        repository.close()"""