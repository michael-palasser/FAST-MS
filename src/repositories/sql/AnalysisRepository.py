import sqlite3
import numpy as np
from tqdm import tqdm

from src.entities.Ions import FragmentIon, Fragment
from src.entities.Search import Search
from src.resources import processTemplateName
from src.services.assign_services.AbstractSpectrumHandler import peaksArrType



class AnalysisRepository(object):
    '''
    Repository for storing values of a top-down analysis
    '''
    def __init__(self, databasePath):
        self._conn = sqlite3.connect(databasePath,isolation_level='DEFERRED')
        #self.__conn = sqlite3.connect(':memory:')
        self._tables = {'ions': ("name", "number", "formula", "monoiso", "charge",
                                    "noise", "qual", "comment", 'status'),
                           'peaks': ("mz", "relAb", "calInt", "error", "used", "parentId"),
                           'chargeStates': ("name", "zList"),
                           'logs': ("log",)}

    def makeTables(self):
        '''self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS searches (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE ,
                "date"	text NOT NULL,
                "noiseLevel"	text NOT NULL);""")'''
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS ions (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "number" integer NOT NULL ,
                "formula" text NOT NULL ,
                "monoiso" real NOT NULL,
                "charge" integer NOT NULL,
                "noise" integer NOT NULL,
                "qual" real NOT NULL,
                "comment" text NOT NULL,
                "status" integer NOT NULL);""")
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
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS logs (
                "id"	integer PRIMARY KEY UNIQUE,
                "log"	text NOT NULL);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS chargeStates (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "zList" text NOT NULL);""")

    """def getAllNames(self):
        '''
        Returns the names of all stored sequences
        :return: (list[str]) names
        '''
        return [searchVals[1] for searchVals in self.getAll()]"""

    def getSearch(self):
        '''
        Finds a search by name
        :param (str) name: name of the search
        :return: (Search) search
        '''
        ions, delIons = [], []
        ionVals = self.getAll('ions')
        bar = tqdm(total=len(ionVals)+4)
        for ionVals in ionVals:
            peaks = [(peak[1], peak[2], peak[3], peak[4], peak[5]) for peak in self.getItems(ionVals[0],'peaks')]
            
            peaks = np.array(peaks, dtype=peaksArrType)
            type, modification = processTemplateName(ionVals[1])

            ion = FragmentIon(Fragment(type, ionVals[2], modification, ionVals[3], [],0),
                              ionVals[4], ionVals[5], peaks,ionVals[6], ionVals[7], True, ionVals[8])
            #ion.setRemaining(ionVals[10], ionVals[11], ionVals[12], ionVals[13])
            if ionVals[9] == 0:
                ions.append(ion)
            elif ionVals[9] == 1:
                delIons.append(ion)
            bar.update(1)
        searchedZStates = {ionVals[1]:ionVals[2] for ionVals in self.getAll('chargeStates')}
        bar.update(2)
        log = self.getAll('logs')[0][1]
        bar.update(2)
        self._conn.close()
        return ions, delIons, searchedZStates, log

    def getAll(self, table:str):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM " + table)
        return cur.fetchall()

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


    def createSearch(self, ions, deletedIons, searchedZStates, info):
        """
        Creates a new search entry and subsidiary entries in the subtables
        :param (Search) search: new entry
        """
        #try:
        self.makeTables()
        self._bar = tqdm(total=len(ions+deletedIons)+2)
        self.createItem('logs', (info,))
        self._bar.update(1)
        self.insertIons(ions, 0)
        self.insertIons(deletedIons, 1)
        [self.createItem('chargeStates', [frag,zList]) for frag,zList in searchedZStates.items()]
        self._bar.update(1)
        self._conn.close()


    def insertIons(self, ions, status):
        '''
        Creates new ion and peak entries
        :param (int) searchId: parent id of the search
        :param (list[FragmentIon]) ions: list of ions
        :param (int) status: 1 if ions were deleted, 0 otherwise
        '''
        for ion in ions:
            ionId = self.createItem('ions', ion.toStorage() + [status])
            for peak in ion.peaksToStorage():
                self.createItem('peaks', peak+[ionId])
            self._bar.update(1)

    def createItem(self,table, attributes):
        '''
        Creates a subsidiary entry in a subtable
        :param (str) table: target subtable
        :param (list[Any] | tuple[Any]) attributes: attributes of the new entry
        :return: (int) id of the created entry
        '''
        cur = self._conn.cursor()
        sql = 'INSERT INTO ' + table + '(' + ', '.join(self._tables[table]) + ''') 
                                      VALUES(''' + (len(self._tables[table]) * '?,')[:-1] + ')'
        cur.execute(sql, attributes)
        self._conn.commit()
        return cur.lastrowid



    """def updateSearch(self, search):
        '''
        Updates a search entry and its subsidiary entries
        :param (Search) search: updated search
        '''
        searchId = self.get('name', search.getName())[0]
        self.deleteDependentTables(searchId)
        self.createItem('logs', (search.getInfo()))
        self.insertIons(search.getIons(), 0)
        self.insertIons(search.getDeletedIons(), 1)"""

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


    """def deleteDependentTables(self):
        '''
        Deletes all subsidiary entries of a search
        :param (int) searchId: parent id of the search
        '''
        cur = self._conn.cursor()
        for ion in self.getItems('ions'):
            cur.execute("DELETE FROM peaks WHERE parentId=?", (ion[0],))
        cur.execute("DELETE FROM ions")
        cur.execute("DELETE FROM logs WHERE parentId=?", (searchId,))
        self._conn.commit()

    def delete(self, searchName):
        '''
        Deletes a search by name
        :param (str) searchName: name
        '''
        #id = super(AbstractRepositoryWith2Items, self).delete(name)
        self.deleteDependentTables(super(AnalysisRepository, self).delete(searchName))"""


'''if __name__ == '__main__':
    string = ""
    with open('log39.txt') as f:
        for line in f:
            string+=line
        print(string)
        rep = AnalysisRepository()
        rep.createItem('logs', (string, 39))'''