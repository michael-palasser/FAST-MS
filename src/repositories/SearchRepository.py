import sqlite3
import numpy as np

from src.entities.Ions import FragmentIon, Fragment
from src.entities.Search import Search
from src.repositories.AbstractRepositories import AbstractRepositoryWithItems, AbstractRepository


class SearchRepository(AbstractRepository):
    def __init__(self, ):
        super(SearchRepository, self).__init__('search.db', 'searches',
                                               ('name', "date","sequName", "charge", "fragmentation", "modifications",
                                                "nrMod", "spectralData", "noiseLimit", "fragLib", 'logFile'), (), ())
        #self.__conn = sqlite3.connect(':memory:')
        self._depTables = {'ions': ("type", "number", "modif", "formula", "sequ", "radicals", "monoiso", "charge",
                                    "noise", "int", "error", "qual", "comment", 'status', "parentId"),
                           'peaks': ("mz", "relAb", "calInt", "error", "used", "parentId"),
                           'chargeStates': ("name", "zList", "parentId"),
                           'logs': ("log", "parentId")}

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS searches (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE ,
                "date"	text NOT NULL ,
                "sequName"	text NOT NULL ,
                "charge"	integer NOT NULL ,
                "fragmentation"	text NOT NULL,
                "modifications"	text NOT NULL,
                "nrMod"	integer NOT NULL ,
                "spectralData"	text NOT NULL,
                "noiseLimit"	real NOT NULL,
                "fragLib"	text NOT NULL);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS ions (
                "id"	integer PRIMARY KEY UNIQUE,
                "type"	text NOT NULL ,
                "number" integer NOT NULL ,
                "modif" text NOT NULL ,
                "formula" text NOT NULL ,
                "sequ" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "monoiso" real NOT NULL,
                "charge" integer NOT NULL,
                "noise" integer NOT NULL,
                "int" integer NOT NULL,
                "error" real NOT NULL,
                "qual" real NOT NULL,
                "comment" text NOT NULL,
                "status" integer NOT NULL,
                "parentId" integer NOT NULL );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS peaks (
                "id"	integer PRIMARY KEY UNIQUE,
                "mz"	real NOT NULL ,
                "relAb" integer NOT NULL ,
                "calInt" integer NOT NULL ,
                "error" real NOT NULL ,
                "used" integer NOT NULL,
                "parentId" integer NOT NULL );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS logs (
                "id"	integer PRIMARY KEY UNIQUE,
                "log"	text NOT NULL ,
                "parentId" integer NOT NULL );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS chargeStates (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "zList" text NOT NULL ,
                "parentId" integer NOT NULL );""")

    def getAllNames(self):
        return [searchVals[1] for searchVals in self.getAll()]

    def getSearch(self, name):
        searchVals = self.get('name', name)
        ions, delIons, remIons = [], [], []
        for ionVals in self.getItems(searchVals[0], 'ions'):
            peaks = [(peak[1], peak[2], peak[3], peak[4], peak[5]) for peak in self.getItems(ionVals[0],'peaks')]
            peaks = np.array(peaks, dtype=[('m/z', np.float64), ('relAb', np.float64),('calcInt', np.float64),
                                           ('error', np.float32), ('used', np.bool_)])
            ion = FragmentIon(Fragment(ionVals[1], ionVals[2], ionVals[3], ionVals[4], ionVals[5],
                                       ionVals[6]),
                              ionVals[7], ionVals[8], peaks,ionVals[9])
            ion.setRemaining(ionVals[10], ionVals[11], ionVals[12], ionVals[13])
            if ionVals[14] == 0:
                ions.append(ion)
            elif ionVals[14] == 1:
                delIons.append(ion)
            else:
                remIons.append(ion)
        searchedZStates = {ionVals[1]:ionVals[2] for ionVals in self.getItems(searchVals[0], 'chargeStates')}
        log = self.getItems(searchVals[0], 'logs')[1]
        return Search(searchVals, ions, delIons, remIons, searchedZStates, log)


    def getItems(self, parentId, table):
        #table = [key for key in self._itemDict.keys()][0]
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM " + table + " WHERE parentId=?", (parentId,))
        return cur.fetchall()


    def createSearch(self, search):
        """
        Function create() creates new pattern which is filled by insertIsotopes
        :param modificationPattern:
        :return:
        """
        #try:
        searchId = self.create(search.getVals())
        self.insertItems(searchId, search.getIons(), 0)
        self.insertItems(searchId, search.getDeletedIons(), 1)
        self.insertItems(searchId, search.getIons(), 2)
        [self.createItem('chargeStates', [frag,zList, searchId]) for frag,zList in search.getSearchedZStates().items()]

    def create(self, vals):
        """

        :param args: Values of the newly created item
        :return:
        """
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + self._mainTable + '(' + ', '.join(self._columns) + ''') 
                              VALUES(''' + (len(self._columns) * '?,')[:-1] + ')'
        print(sql, vals)
        try:
            cur.execute(sql, vals)
        except sqlite3.OperationalError:
            self.makeTables()
            cur.execute(sql, vals)
        self._conn.commit()
        return cur.lastrowid

    def insertItems(self, searchId, ions, status):
        for ion in ions:
            ionId = self.createItem('ions', ion.toStorage() + [status, searchId])
            for peak in ion.peaksToStorage():
                self.createItem('peaks', peak+[ionId])

    def createItem(self,table, attributes):
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + '(' + ', '.join(self._depTables[table]) + ''') 
                                      VALUES(''' + (len(self._depTables[table]) * '?,')[:-1] + ')'
        print(sql, attributes)
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid


    def updateSearch(self, search):
        searchId = self.getSearch(search.getName())
        self.update(search.getVals()[0], searchId)
        self.deleteIons(searchId)
        self.insertItems(searchId, search.getIons(), 0)
        self.insertItems(searchId, search.getDeletedIons(), 1)
        self.insertItems(searchId, search.getIons(), 2)

    def deleteIons(self, searchId):
        cur = self._conn.cursor()
        for ion in self.getItems(searchId, 'ions'):
            cur.execute("DELETE FROM peaks WHERE patternId=?", (ion[0],))
        cur.execute("DELETE FROM ions WHERE patternId=?", (searchId,))
        self._conn.commit()

    def delete(self, searchName):
        #id = super(AbstractRepositoryWith2Items, self).delete(name)
        self.deleteIons(super(SearchRepository, self).delete(searchName))