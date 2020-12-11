import sqlite3

class Item(object):
    def __init__(self):
        self.name = ""
        self.gain = ""
        self.loss = ""
        self.loss = ""
        self.residue = ""
        self.radicals = 0

class ModifiedItem(Item):
    def __init__(self):
        super(ModifiedItem, self).__init__()
        self.zEffect = 0

"""class FragmentationPattern(object):
    def __init__(self):
        self.name = ""
        self.modification = ""
        self.listOfUnmod = list()
        self.listOfMod = list()
        self.listOfOthers = list()"""

class FragmentationRepository(object):
    def readData(self):
        with