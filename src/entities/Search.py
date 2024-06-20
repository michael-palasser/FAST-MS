
class Search(object):
    '''
    Class to store all important settings and results of a top-down MS analysis
    '''
    #def __init__(self, name, date, sequName, _charge, fragmentation, nrMod, spectralData, noise, lib, ions, id):
    def __init__(self, vals, ions, deletedIons, remIons, searchedZStates, info):
        '''
        :param (tuple[int, str, str, int, str, str, int, str, float, str] |
            list[int, str, str, int, str, str, int, str, float, str]) vals: settings
        :param (list[FragmentIon]) ions: list of observed ions
        :param (list[FragmentIon]) deletedIons: list of deleted ions
        :param (list[FragmentIon]) remIons: list of remodelled ions
        :param (dict[str:list[int]]) searchedZStates: dictionary {fragment-name: possible charge states} of calculated
            charge state for each fragment
        :param (str) info: information about user inputs
        '''
        self._name = vals[1]
        self._date = vals[2]
        self._noiseLevel = vals[3]
        if vals[3] == 0:
            self._noiseLevel = vals[10]
        self._sequName = vals[4]
        self._charge = vals[5]
        self._fragmentation = vals[6]
        self._modifications = vals[7]
        self._nrMod = vals[8]
        self._spectralData = vals[9]
        self._noiseLimit = vals[10]
        if len(vals)>11:
            self._fragLib = vals[11]
        self._ions = ions
        self._deletedIons = deletedIons
        self._remIons = remIons
        self._searchedZStates = searchedZStates
        self._info = info

    def getName(self):
        return self._name

    def getDate(self):
        return self._date

    def getVals(self):
        return [self._name, self._date, self._noiseLevel, self._sequName, self._charge, self._fragmentation, self._modifications,
                self._nrMod, self._spectralData, self._noiseLimit, self._fragLib]

    def getIons(self):
        return self._ions

    def getDeletedIons(self):
        return self._deletedIons

    def getRemIons(self):
        return self._remIons

    def getSearchedZStates(self):
        return self._searchedZStates

    def getInfo(self):
        return self._info

    def getSettings(self):
        return {'sequName': self._sequName, 'charge': self._charge, 'fragmentation': self._fragmentation,
                'modifications': self._modifications, 'nrMod': self._nrMod, 'spectralData': self._spectralData,
                'noiseLimit': self._noiseLimit, 'fragLib': self._fragLib}

    def setNoiseLevel(self, noiseLevel):
        self._noiseLevel = noiseLevel
    def getNoiseLevel(self):
        return self._noiseLevel