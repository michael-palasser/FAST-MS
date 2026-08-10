'''
Created on 31 Aug 2020

@author: michael
'''
import json
import traceback
from os.path import isfile, join
from src.resources import getRelativePath, base_path, user, processLongPaths

top_down_search = {'sequName': '', 'charge': -1, 'fragmentation': '', 'modifications': '', 'nrMod': 0,
                   'spectralData': '', 'noiseLimit': 0.0, 'fragLib': '', 'calibration': False, 'calIons': ''}
intact_search = {'sequName': '', 'modifications': '', 'spectralData': '', 'sprayMode': 'negative', 'noiseLimit': 0.0,
                 'minMz': 300, 'maxMz': 1600, 'calibration': True, 'calIons': ''}
intact_assign = {'sequName': '', 'modifications': '', 'spectralData': [''], 'sprayMode': 'negative',
                 'inputMode': 'abundances (int./z)', 'minMz': 300, 'maxMz': 1600, 'calibration': True, 'output': ''}
configurations = {'lowerBound': 300, 'minUpperBound': 1200, 'upperBoundTolerance': 100, 'upperBoundWindowSize': 20.0,
                  'errorLimitCalib': 50, 'maxStd': 1.5, 'overwrite': False, 'zTolerance': 0.8, 'k': 4.5, 'd': 0.5,
                  'errorTolerance': 2.5, 'noiseWindowSize': 4.0, 'thresholdFactor': 0.45, 'maxIso': 0.996,
                  'approxIso': 20, 'outlierLimit': 1.6, 'manualDeletion': 3, 'overlapThreshold': 0.8, 'shapeDel': 0.6,
                  'shapeMarked': 0.25, 'scoreMarked': 2.5, 'SNR': 2.0, 'useAb': True, 'interestingIons': ['c', 'y'],
                  '# ions displayed':10}
top_down_export = {'columns': ['m/z', 'z', 'intensity', 'fragment', 'error /ppm', 'S/N', 'quality', 'formula', 'score', 'comment'],
                   'analysis': ['occupancies', 'reduced charges'], 'dir': join(base_path, 'Spectral_data', 'top-down')}
intact_export = {'columns': ['m/z', 'z', 'intensity', 'fragment', 'error /ppm', 'S/N', 'quality', 'formula', 'score', 'comment'],
                 'analysis': [], 'dir': join(base_path, 'Spectral_data', 'intact')}
                 
md = {'sequName': '', 'charge': 1, 'fragmentation': '', 'modifications': '', 'nrMod': 0,
                   'spectralData': '', 'snapData': "", 'profile': "","output":""}


scoreDict = {'pen_S/N':-10,'pen_error':-3,'pen_prec':-5,
             'I':1,'S/N':1, 'quality':2,                          #FAST MS
             'I_SNAP':0.5,'S/N_SNAP':1, 'quality_SNAP':1,       #SNAP
             'I_mono':0.5,'S/N_mono':5}  


class ConfigHandler(object):
    '''
    Class that reads and writes configuration-_files (json-format) and stores it as dictionary
    '''
    def __init__(self, configFile, default):
        '''
        :param (str) configFile: path of json file where configuration values are stored
        '''
        self._configFile = configFile
        if not isfile(configFile):
            if isfile(processLongPaths(configFile)):
                self._configFile = processLongPaths(configFile)
            else:
                print('not found')
                print(configFile)
                self._configFile = None
                self.__parameters = default
        if self._configFile is not None:
            with open(self._configFile, "r") as f:
                try:
                    self.__parameters = json.loads(json.load(f))
                except:
                    traceback.print_exc()
                    self.__parameters = default
        else:
            self._configFile = configFile


    def get(self,key):
        '''
        Returns the corresponding value of the key
        :param (str) key:
        :return: (Any) value
        '''
        if self.__parameters:
            try:
                return self.__parameters[key]
            except:
                if key in ('calIons', 'spectralData', 'snapData', 'profile'):
                    return ''
                return 0
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
        if not self.__parameters:
            print("Configuration file does not exist")
        return self.__parameters

    def update(self, parameter, value):
        if parameter not in self.__parameters.keys():
            raise Exception('Parameter ',parameter, ' not in configurations.')
        self.__parameters[parameter] = value

    def update2(self, parameter, value):
        self.__parameters[parameter] = value


class ConfigurationHandlerFactory(object):
    '''
    Factory class which creates the appropriate ConfigHandler
    '''
    @staticmethod
    def getTD_SettingHandler(filePath = None):
        if filePath is None:
            return ConfigHandler(getRelativePath("settings_top_down_"+user+".json"), top_down_search)
        else:
            return ConfigHandler(filePath, top_down_search)

    """@staticmethod
    def getPersonalTD_SettingHandler():
        return ConfigHandler("C:/temp/settings_top_down.json",
                             ConfigurationHandlerFactory.getTD_SettingHandler().getAll())"""
    @staticmethod
    def getTable_SettingHandler():
        return ConfigHandler(getRelativePath("settings_td_table_"+user+".json"), top_down_search)

    """@staticmethod
    def getPersonalTable_SettingHandler():
        return ConfigHandler("C:/temp/settings_td_table.json",
                             ConfigurationHandlerFactory.getPersonalTD_SettingHandler().getAll())"""

    @staticmethod
    def getConfigHandler(filePath=None):
        if filePath is None:
            return ConfigHandler(getRelativePath("configurations.json"), configurations)
        else:
            return ConfigHandler(filePath, configurations)

    @staticmethod
    def getExportHandler():
        return ConfigHandler(getRelativePath("export_options_"+user+".json"), top_down_export)

    @staticmethod
    def getIntactExportHandler():
        return ConfigHandler(getRelativePath("export_options_intact_"+user+".json"), intact_export)

    @staticmethod
    def getIntactAssignHandler():
        return ConfigHandler(getRelativePath("settings_intact_"+user+".json"), intact_assign)

    @staticmethod
    def getFullIntactHandler():
        return ConfigHandler(getRelativePath("settings_intactFull_"+user+".json"), intact_search)

    @staticmethod
    def getMDHandler():
        return ConfigHandler(getRelativePath("settings_MD_"+user+".json"), md)

    @staticmethod
    def getMDScoresHandler():
        return ConfigHandler(getRelativePath("settings_MD_scores.json"), scoreDict)

