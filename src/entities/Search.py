
class Search(object):
    #def __init__(self, name, date, sequName, charge, fragmentation, nrMod, spectralData, noise, lib, ions, id):
    def __init__(self, vals, ions, deletedIons, remIons, searchedZStates):
        self._name = vals[1]
        self._date = vals[2]
        self._sequName = vals[3]
        self._charge = vals[4]
        self._fragmentation = vals[5]
        self._nrMod = vals[6]
        self._spectralData = vals[7]
        self._noiseLimit = vals[8]
        self._fragLib = vals[9]
        self._ions = ions
        self._deletedIons = deletedIons
        self._remIons = remIons
        self._searchedZStates = searchedZStates

    def getName(self):
        return self._name

    def getDate(self):
        return self._date

    def getVals(self):
        return [self._name, self._sequName, self._charge, self._fragmentation, self._nrMod, self._spectralData,
                self._noiseLimit, self._fragLib]

    def getIons(self):
        return self._ions

    def getDeletedIons(self):
        return self._deletedIons

    def getRemIons(self):
        return self._remIons

    def getSearchedZStates(self):
        return self._searchedZStates

    def getSettings(self):
        return {'sequName': self._sequName, 'charge': self._charge, 'fragmentation': self._fragmentation,
                'nrMod': self._nrMod, 'spectralData': self._spectralData, 'noiseLimit': self._noiseLimit,
                'fragLib': self._fragLib}