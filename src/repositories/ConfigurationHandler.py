'''
Created on 31 Aug 2020

@author: michael
'''

import json
from os.path import isfile, join
from src import path


class ConfigHandler(object):
    '''
    Class that reads and writes configuration-_files (json-format) and stores it as dictionary
    '''
    def __init__(self, configFile):
        '''
        :param (str) configFile: path of json file where configuration values are stored
        '''
        #with openAgain(_configFile, "w") as f:
         #   json.dump(json.dumps(parameters), f)
        self._configFile = configFile
        print('new')
        if isfile(configFile):
            with open(configFile, "r") as f:
                try:
                    self.__parameters = json.loads(json.load(f))
                except:
                    self.__parameters = dict()
        else:
            print('not found')
            print(configFile)
            self.__parameters = dict()

    def get(self,key):
        '''
        Returns the corresponding value of the key
        :param (str) key:
        :return: (Any) value
        '''
        if self.__parameters:
            return self.__parameters[key]
        raise Exception("Parameter",key, "does not exist")

    def write(self, parameters):
        '''
        Updates the configuration file
        :param (dict[str,Any]) parameters: new configurations
        '''
        with open(self._configFile, "w") as f:
            json.dump(json.dumps(parameters, indent=3), f)

    def getAll(self):
        '''
        Returns all parameters as a dictionary
        :return: (dict[str,Any]) parameters
        '''
        if self.__parameters:
            return self.__parameters
        print("Configuration file does not exist")

    def update(self, parameter, value):
        if parameter not in self.__parameters.keys():
            raise Exception('Parameter ',parameter, ' not in configurations.')
        self.__parameters[parameter] = value

dataPath = join(path, "src", "data")

class ConfigurationHandlerFactory(object):
    '''
    Factory class which creates the appropriate ConfigHandler
    '''
    @staticmethod
    def getTD_SettingHandler():
        return ConfigHandler(join(dataPath,"settings_top_down.json"))

    @staticmethod
    def getTD_ConfigHandler():
        return ConfigHandler(join(dataPath,"configurations_top_down.json"))


    @staticmethod
    def getExportHandler():
        return ConfigHandler(join(dataPath, "export_options.json"))

    @staticmethod
    def getIntactHandler():
        print('eig new configH')
        return ConfigHandler(join(dataPath, "configurations_intact.json"))

    @staticmethod
    def getFullIntactHandler():
        return ConfigHandler(join(dataPath, "configurations_intactFull.json"))


conf = {'sequName' : 'ribA',
    'charge' : -6,
    'fragmentation': 'RNA_CAD',
    'modifications' : 'CMCT',
    'nrMod': 1,
    'spectralData' : '080819_ribA_PAR_6.txt',
    'noiseLimit' : 1550000.0,
    'fragLib' : '',
    'output' : ''}
"""
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
"""
from src import path
if __name__ == '__main__':
    absPath = path +"/src/data/settings_top_down.json"
    handler = ConfigHandler(absPath)

    with open(absPath, "w") as f:
        json.dump(json.dumps(conf, indent=3), f)
"""
with open(absPath) as json_data_file:
    pattern = json.load(json_data_file)
print(pattern)
"""
