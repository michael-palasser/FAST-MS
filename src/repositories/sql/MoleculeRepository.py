from os.path import join

from src.entities.GeneralEntities import Macromolecule
from src.repositories.sql.AbstractRepositories import AbstractRepositoryWithItems


class MoleculeRepository(AbstractRepositoryWithItems):
    '''
    Repository for molecule types
    '''
    def __init__(self):
        super(MoleculeRepository, self).__init__(join('shared.db'), 'molecules',
                                                 ("name", "gain", "loss"),
                                                 {"buildingBlocks": ('name', 'translation', 'formula', 'gbP', 'gbN','patternId')},(3,4),())

    def makeTables(self, table='molecules'):
        self._conn.cursor().execute("""
                    CREATE TABLE IF NOT EXISTS """ + table + """ (
                        "id"	integer PRIMARY KEY UNIQUE ,
                        "name"	text NOT NULL UNIQUE ,
                        "gain"	text NOT NULL,
                        "loss"	text NOT NULL);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS buildingBlocks (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL,
                "translation" text NOT NULL DEFAULT "",
                "formula" text NOT NULL ,
                "gbP" real NOT NULL ,
                "gbN" real NOT NULL ,
                "patternId" text NOT NULL );""")

    def getItemColumns(self):
        '''
        Returns the column names and corresponding tooltips for the user
        :return: (dict[str,str]) dictionary of {column name: tooltip}
        '''
        return {'name':'Enter the short name of the building block. The first letter must be uppercase, all other letters must be lowercase',
                'translation': 'Enter the long name (e.g. in HELM or 3-letter code)',
                'formula':'Molecular formula of the building block'}
                #'p(+)':'Empirically derived factor that indicates the propabilty that a building block is positively charged in positive ion mode',
                #'p(-)':'Empirically derived factor that indicates the propabilty that a building block is negatively charged in negatively ion mode'}
                #'gb+':'Enter the gas phase basicity (kJ/mol) of the building block in positive mode',
                #'gb-':'Enter the gas phase basicity (kJ/mol) of the (deprotonated) building block in negative mode\n'
                #      '(not relevant for nucleic acids)'

    def getPattern(self, name):
        '''
        Finds a molecule entry with its building blocks by name
        :param (str) name: name
        :return: (Macromolecule) molecule
        '''
        pattern = self.get('name', name)
        return Macromolecule(pattern[1], pattern[2], pattern[3], self.getItems(pattern[0],
                                                                               [key for key in self._itemDict.keys()][0]), pattern[0])

    def getItems(self,patternId, table):
        '''
        Returns the subsidiary building block entries of a molecule entry
        :param (int) patternId: parent id
        :param (str) table: subtable which contains subsidiary entries
        :return: (list[list[str,str,float,float]])
        '''
        listOfItems = list()
        for item in super(MoleculeRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append((item[1], item[2], item[3], item[4],item[5])) #, item[3], item[4], item[5]) )
        return listOfItems

    def createPattern(self, pattern):
        """
        Creates a new molecule entry in the main table and subsidiary building block entries in the subtable
        :param (Macromolecule) pattern: the object which should be stored within the database
        """
        self.insertItems(self.create((pattern.getName(), pattern.getGain(), pattern.getLoss())), pattern.getItems(), 0)

    def updatePattern(self, pattern):
        '''
        Updates a molecule entry and all subsidiary building block entries
        :param (Molecule) pattern: updated Molecule object
        '''
        self.update((pattern.getName(), pattern.getGain(), pattern.getLoss(), pattern.getId()))
        self.deleteAllItems(pattern.getId())
        self.insertItems(pattern.getId(), pattern.getItems(), 0)


    def addNewColumn(self, name):
        cur = self._conn.cursor()
        cur.execute('ALTER TABLE buildingBlocks RENAME TO  temp_class;')
        self.makeTables()
        sql = 'INSERT INTO buildingBlocks (' + ', '.join(('name', 'formula', 'gbP', 'gbN','patternId')) + ''')
              SELECT '''+ ', '.join(('name', 'formula', 'gbP', 'gbN','patternId')) + '''
              FROM temp_class;'''
        cur.execute(sql)
        self._conn.commit()
        #print("sql",sql)
        cur.execute('DROP TABLE temp_class;')
        return self.getPattern(name)