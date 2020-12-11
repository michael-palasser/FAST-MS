'''
Created on 31 Aug 2020

@author: michael
'''

import json
from src import path
from os.path import isfile


        #with open(configFile, "w") as f:
         #   json.dump(json.dumps(parameters), f)
configFile = path + '/src'+'/FragmentHunter' +"/settings.json"

def read():
    with open(configFile, "r") as f:
            return json.loads(json.load(f))

    def get(self,parameter):
        if self.__parameters:
            return self.__parameters[parameter]
        raise Exception("Parameter",parameter, "does not exist")

def write(parameters):
    with open(configFile, "w") as f:
        json.dump(json.dumps(parameters, indent=3), f)

print(read())


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
"""





