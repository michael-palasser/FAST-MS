import csv
import os
import sqlite3
import time
from os.path import join

import numpy as np

from src import path
from src.Exceptions import InvalidIsotopePatternException


class IsotopePatternReader(object):
    def __init__(self):
        self.__file = None


    def getFile(self):
        return self.__file

    def findFile(self, settings):
        if len(settings) == 1:
            file = settings[0]
            if not file[-4:] == '.csv':
                file += '.csv'
            self.__file = os.path.join(path, 'Fragment_lists',file)
        else:
            sequName, fragmentation, nrMod, modifications = settings[0], settings[1], settings[2], settings[3],
            if modifications == "-" or nrMod == "0":
                self.__file = os.path.join(path, 'Fragment_lists', '_'.join((sequName, fragmentation + '.csv')))
            else:
                self.__file = os.path.join(path, 'Fragment_lists', '_'.join((sequName, fragmentation, str(nrMod),
                                                                             modifications+'.csv')))
        return os.path.isfile(self.__file)


    def addIsotopePatternFromFile(self, fragmentLibrary):
        '''
        Reads and processes isotope patterns from existing file
        :param file: file with istope patterns (in folder Fragment_lists)
        :return: (list) fragmentLibrary
        '''
        isotopePatternDict = dict()
        #print(self.__file)
        with open(self.__file, mode='r') as f:
            reader = csv.reader(f)
            next(reader, None)
            isotopePattern = list()
            counter = 0
            i=0
            for i,row in enumerate(reader):
                #print(row)
                if len(row) < 3:
                    continue
                if counter == 0:
                    name = row[0]
                    counter = 1
                elif row[0] != '':
                    isotopePatternDict[name] = np.array(isotopePattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])
                    name = row[0]
                    isotopePattern = list()
                try:
                    isotopePattern.append((row[1], row[2]))
                except IndexError:
                    print(row)
                    raise InvalidIsotopePatternException(row, " incorrect")
            if i < 1:
                raise InvalidIsotopePatternException("", "no data in file")
            isotopePatternDict[name] = np.array(isotopePattern, dtype=[('m/z',np.float64),('calcInt', np.float64)])
        print('Checking correctness of fragment library')
        for fragment in fragmentLibrary:
            if fragment.getName() not in isotopePatternDict:
                raise InvalidIsotopePatternException(fragment.getName(), "not found in file")
            self.checkEquality(fragment, isotopePatternDict[fragment.getName()])
            fragment.setIsotopePattern(isotopePatternDict[fragment.getName()])
        print('done')
        return fragmentLibrary

    def checkEquality(self, fragment, savedPattern):
        '''
        Checks if stored isotope pattern is correct
        :type fragment: Fragment
        :param (Fragment) fragment: freshly created Fragment
        :param savedPattern: isotope pattern from file
        :raises InvalidIsotopePatternException if not equal
        '''
        newPattern = fragment.getFormula().calcIsotopePatternSlowly(2)
        for i in range(2):
            if newPattern[i]['m/z'] - savedPattern[i]['m/z'] > 10 ** (-6):
                raise InvalidIsotopePatternException(fragment.getName(), "mass incorrect " +
                                                     str(newPattern[i]['m/z']) + " != " + str(savedPattern[i]['m/z']))
            if newPattern[i]['calcInt'] - savedPattern[i]['calcInt'] > 10 ** (-6):
                print(newPattern)
                raise InvalidIsotopePatternException(fragment.getName(), '(' + str(i) + ") relative Abundance incorrect " +
                                                     str(newPattern[i]['calcInt']) + " != " + str(savedPattern[i]['calcInt']))


    def saveIsotopePattern(self, fragmentLibrary):
        '''
        Saves calculated isotope patterns to a file
        :param (list) fragmentLibrary: list of Fragment objects
        '''
        np.set_printoptions(suppress=True)
        #M_max = 0
        fieldnames = ['ion', 'mass', 'Intensities']
        with open(self.__file, mode="w") as f:
            f_writer = csv.DictWriter(f, fieldnames=fieldnames)
            f_writer.writeheader()
            for fragment in fragmentLibrary:
                counter = 0  # for new rows
                for isotope in fragment.getIsotopePattern():
                    if counter == 0:
                        #if M_max < isotope[0]:
                            #M_max = isotope[0]
                        #print(isotope[0])
                        f_writer.writerow({'ion': fragment.getName(), 'mass': np.around(isotope['m/z'], 6),
                                           'Intensities': np.around(isotope['calcInt'], 7)})
                        counter += 1
                    else:
                        f_writer.writerow({'ion': '', 'mass': np.around(isotope['m/z'], 6),
                                           'Intensities': np.around(isotope['calcInt'], 7)})


'''def __init__(self):
        self._conn = sqlite3.connect(join(path,"src","data","isoPatterns.db"))

    def makeTable(self):
        def makeTables(self):
            self._conn.cursor().execute("""
                        CREATE TABLE IF NOT EXISTS files (
                            "id"	integer PRIMARY KEY UNIQUE ,
                            "sequName"	text NOT NULL,   
                            "nrMod" integer NOT NULL ,
                            "fragName"	text NOT NULL,
                            "modName" text NOT NULL ,);""")
            self._conn.cursor().execute("""
                CREATE TABLE IF NOT EXISTS fragments (
                    "id"	integer PRIMARY KEY UNIQUE ,
                    "name"	text NOT NULL,
                    "fileId" text NOT NULL );""")
            self._conn.cursor().execute("""
                CREATE TABLE IF NOT EXISTS fragments (
                    "id"	integer PRIMARY KEY UNIQUE ,
                    "m/z"	 real NULL,
                    "calcInt"	 real NULL,
                    "fragmentId" text NOT NULL );""")

    def create(self, sequence, nrMod, fragName, modName, fragmenta):
        """

        :param args: Values of the newly created item
        :return:
        """
        cur = self._conn.cursor()
        #if len(self._columns)>1:
        sql = \''' INSERT INTO files(sequName, nrMod, fragName, modName) 
                              VALUES(?,?,?,?,?)\'''
       # else:
                                          #VALUES(\''' + (len(self._columns) * '?,')[:-1] + ')'
        #print(self._mainTable, args,sql, self._columns)
        print(sql,args)
        try:
            cur.execute(sql, args)
        except sqlite3.OperationalError:
            self.makeTables()
            cur.execute(sql, args)
        self._conn.commit()
        return cur.lastrowid


    def getFragment(self):'''