'''
Created on 31 Aug 2020

@author: michael
'''

import json
from os.path import isfile

class ConfigHandler(object):
    '''
    Class that reads and writes configuration-files (json-format) and stores it as dictionary
    '''
    def __init__(self, configFile):
        #with openAgain(configFile, "w") as f:
         #   json.dump(json.dumps(parameters), f)
        self.configFile = configFile
        if isfile(configFile):
            with open(configFile, "r") as f:
                self.__parameters = json.loads(json.load(f))
        else:
            print('not found')
            self.__parameters = dict()

    def get(self,key):
        if self.__parameters:
            return self.__parameters[key]
        raise Exception("Parameter",key, "does not exist")

    def write(self, parameters):
        with open(self.configFile, "w") as f:
            json.dump(json.dumps(parameters, indent=3), f)

    def getAll(self):
        if self.__parameters:
            return self.__parameters
        print("Configuration file does not exist")

"""
conf = {'sequName' : 'ribA',
    'charge' : 6,
    'modification' : 'CMCT',
    'spectralData' : '080819_ribA_PAR_6.txt',
    'noiseLimit' : 1550000.0,
    'sprayMode' : 'negative',
    'dissociation' : 'CAD'}

more = {'lowerBound' : 300,
'minUpperBound' : 1200,
'upperBoundTolerance' : 50,
'upperBoundWindowSize' : 20,

'k' : 0.0045,
'd' : 0.5,
'errorTolerance' : 2.5,

'shapeDel' : 0.6,
'shapeMarked' : 0.25,
'scoreMarked' : 2.5,

'noiseWindowSize' : 4,
'thresholdFactor' : 0.6,

'zTolerance' : 1.5,
'outlierLimit' : 0.65,

'manualDeletion' : 4,
'overlapThreshold' : 0.8,

'interestingIons' : ['c','y']}


conf =  {"CR_1_2":	('RNA',	'GAAGGGCAACCUUCG'),
        "CR_1_3":	('RNA',	'GAAGGUUCGCCUUCG'),
        "neoRibo":	('RNA',	'GGCUGCUUGUCCUUUAAUGGUCCAGUC'),
        "ribA":	('RNA',	'GGCGUCACACCUUCGGGUGAAGUCGCC'),
        "rre1":	('RNA',	'GGGUUCUUGGGAGCAGCAGGAUUCGUCCUGGCUGUGGAAAGAUACCC'),
        "rre2":	('RNA',	'GCACUAUGGGCGCAGCGUCAAUGACGCUGACGGUACAGGCCAGACAAUUAUUGUCUGGUAUAGUGC'),
        "rre2b":	('RNA',	'GGUCUGGGCGCAGCGUCAAUGACGCUGACGGUACAGGCC'),
        "encFtn":	('P',	'AQSSNSTHEPLEVLKEETVNRHRAIVSVMEELEAVDWYDQRVDASTDPELTAILAHNRDEEKEHAAMTLEWLRRNDAKWAEHLRTYLFTEGPITAANSSSVDKLAAALEHHHHHH')}

from src import path
absPath = path +"/src/Sequences.json"
handler = ConfigHandler(absPath)

with openAgain(absPath, "w") as f:
    json.dump(json.dumps(conf, indent=3), f)

with openAgain(absPath) as json_data_file:
    pattern = json.load(json_data_file)
print(pattern)
"""
