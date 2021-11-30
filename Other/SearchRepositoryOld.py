#import sqlite3

import numpy as np
from tqdm import tqdm

from src.entities.Ions import FragmentIon, Fragment
from src.entities.Search import Search
from src.repositories.AbstractRepositories import AbstractRepository


class SearchRepository(AbstractRepository):
    '''
    Repository for storing values of a top-down analysis
    '''
    def __init__(self):
        super(SearchRepository, self).__init__('search.db', 'searches',
                                               ('name', "date","sequName", "charge", "fragmentation", "modifications",
                                                "nrMod", "spectralData", "noiseLimit", "fragLib"), (), ())
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
        #ToDo weg mit radicals, monoiso, error,
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS peaks (
                "id"	integer PRIMARY KEY UNIQUE,
                "mz"	real NOT NULL ,
                "relAb" integer NOT NULL ,
                "calInt" integer NOT NULL ,
                "error" real NOT NULL ,
                "used" integer NOT NULL,
                "parentId" integer NOT NULL );""")
        #ToDo weg mit error
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
        '''
        Returns the names of all stored sequences
        :return: (list[str]) names
        '''
        return [searchVals[1] for searchVals in self.getAll()]

    def getSearch(self, name):
        '''
        Finds a search by name
        :param (str) name: name of the search
        :return: (Search) search
        '''
        searchVals = self.get('name', name)
        ions, delIons, remIons = [], [], []
        ionVals = self.getItems(searchVals[0], 'ions')
        bar = tqdm(total=len(ionVals)+4)
        for ionVals in ionVals:
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
            bar.update(1)
        searchedZStates = {ionVals[1]:ionVals[2] for ionVals in self.getItems(searchVals[0], 'chargeStates')}
        bar.update(2)
        log = self.getItems(searchVals[0], 'logs')[0][1]
        bar.update(2)
        return Search(searchVals, ions, delIons, remIons, searchedZStates, log)


    def getItems(self, parentId, table):
        '''
        Returns the subsidiary entries of a search
        :param (int) parentId: id of the search
        :param (str) table: corresponding subtable
        :return: (list[Any]) subsidiary entries
        '''
        #table = [key for key in self._itemDict.keys()][0]
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM " + table + " WHERE parentId=?", (parentId,))
        return cur.fetchall()


    def createSearch(self, search):
        """
        Creates a new search entry and subsidiary entries in the subtables
        :param (Search) search: new entry
        """
        #try:
        searchId = self.create(search.getVals())
        self.insertItems(searchId, search.getIons(), 0)
        self.insertItems(searchId, search.getDeletedIons(), 1)
        self.insertItems(searchId, search.getRemIons(), 2)
        self.createItem('logs', (search.getInfo().toString(), searchId))
        [self.createItem('chargeStates', [frag,zList, searchId]) for frag,zList in search.getSearchedZStates().items()]

    """def create(self, vals):
        '''

        :param args: Values of the newly created item
        :return:
        '''
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
        return cur.lastrowid"""

    def insertItems(self, searchId, ions, status):
        '''
        Creates new ion and peak entries
        :param (int) searchId: parent id of the search
        :param (list[FragmentIon]) ions: list of ions
        :param (int) status: 1 if ions were deleted, 0 otherwise
        '''
        for ion in ions:
            ionId = self.createItem('ions', ion.toStorage() + [status, searchId])
            for peak in ion.peaksToStorage():
                self.createItem('peaks', peak+[ionId])

    def createItem(self,table, attributes):
        '''
        Creates a subsidiary entry in a subtable
        :param (str) table: target subtable
        :param (list[Any] | tuple[Any]) attributes: attributes of the new entry
        :return: (int) id of the created entry
        '''
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + '(' + ', '.join(self._depTables[table]) + ''') 
                                      VALUES(''' + (len(self._depTables[table]) * '?,')[:-1] + ')'
        print(sql, attributes)
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid


    def updateSearch(self, search):
        '''
        Updates a search entry and its subsidiary entries
        :param (Search) search: updated search
        '''
        searchId = self.get('name', search.getName())[0]
        self.update(search.getVals() + [searchId])
        self.deleteDependentTables(searchId)
        self.insertItems(searchId, search.getIons(), 0)
        self.insertItems(searchId, search.getDeletedIons(), 1)
        self.insertItems(searchId, search.getIons(), 2)
        self.createItem('logs', (search.getInfo().toString(), searchId))

    '''def update(self, vals): #ToDo
        """

        :param args: new attributes, last attribute must be id
        :return:
        """
        cur = self._conn.cursor()
        sql = 'UPDATE ' + self._mainTable + ' SET ' + '=?, '.join(self._columns) + '=? WHERE id=?'
        print(sql, vals)
        cur.execute(sql, vals)
        self._conn.commit()'''


    def deleteDependentTables(self, searchId):
        '''
        Deletes all subsidiary entries of a search
        :param (int) searchId: parent id of the search
        '''
        cur = self._conn.cursor()
        for ion in self.getItems(searchId, 'ions'):
            cur.execute("DELETE FROM peaks WHERE parentId=?", (ion[0],))
        cur.execute("DELETE FROM ions WHERE parentId=?", (searchId,))
        cur.execute("DELETE FROM logs WHERE parentId=?", (searchId,))
        self._conn.commit()

    def delete(self, searchName):
        '''
        Deletes a search by name
        :param (str) searchName: name
        '''
        #id = super(AbstractRepositoryWith2Items, self).delete(name)
        self.deleteDependentTables(super(SearchRepository, self).delete(searchName))


'''if __name__ == '__main__':
    string = ""
    with open('log39.txt') as f:
        for line in f:
            string+=line
        print(string)
        rep = SearchRepository()
        rep.createItem('logs', (string, 39))'''