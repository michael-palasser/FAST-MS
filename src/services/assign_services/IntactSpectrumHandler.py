import logging

import numpy as np

from src.services.MolecularFormula import MolecularFormula
from src.entities.Ions import IntactIon
from src.services.assign_services.AbstractSpectrumHandler import AbstractSpectrumHandler


class IntactSpectrumHandler(AbstractSpectrumHandler):
    def __init__(self, settings, configs, peaks=None):
        '''
        Constructor, also processes spectrum
        :param (dict[str,Any]) settings: search settings
        :param (set[tuple[float]] | None) peaks: set of peak tuples (m/z, I) (optional)
        '''
        mode = 1
        if settings['sprayMode'] == 'negative':
            mode *= -1
        super(IntactSpectrumHandler, self).__init__(settings, configs, mode, IntactIon, peaks)


    def getChargeRange(self, mass):
        '''
        Calculates possible charge states (z) in the given m/z window
        :param (float) mass: mass of the unmodified species
        :return: (generator) range between lowest possible z and highest possible z
        '''
        minMz = self._settings['minMz']
        if np.min(self._spectrum['m/z'])>minMz:
            minMz = np.min(self._spectrum['m/z'])
        maxMz = self._settings['maxMz']
        if self._upperBound<maxMz:
            maxMz = self._upperBound
        return range(int(mass/maxMz+1), int(mass/minMz)+1)

    def findIons(self, neutralLibrary):
        '''
        Assigns peaks in spectrum to isotope peaks of corresponding ion
        1. Possible charges of species are calculated
        2. Search for n highest isotope peaks in spectrum: n either 1, 2 or 3 (see Fragment.getNumberOfHighestIsotopes)
        3. If found noise is calculated and the isotope peaks which could theoretically be above the noise are calculated:
            Programm searches for these peaks in spectrum
            If all isotope peaks are calculated to be below noise threshold, ion is added to deleted ion (comment = noise)
        :param (list[Neutral]) neutralLibrary: list of possible neutral species
        '''
        np.set_printoptions(suppress=True)
        sortedMasses = sorted([neutral.getIsotopePattern()['m/z'][0] for neutral in neutralLibrary])
        zRange = self.getChargeRange(sortedMasses[0])
        self._maxZ = zRange[-1]
        self.getProtonIsotopePatterns()
        for neutral in neutralLibrary:
            # neutralPatternFFT = formula.calculateIsotopePatternFFT(1, )
            logging.info(neutral.getName())
            self._searchedChargeStates[neutral.getName()] = []
            self.findIon(neutral, zRange)


    def getProtonIsotopePatterns(self):
        '''
        Calculates the isotope patterns (rel.abundances) of various numbers of protons
        :return: (ndArray[float,float]) array with 2 columns: rows represent proton nr + 1, column 1: monoisotopic,
            column 2: M+1 peak
        '''
        protonIsotopePatterns = np.zeros((self._maxZ,2))
        for i in range(self._maxZ):
            protonIsotopePatterns[i] = MolecularFormula({'H':i+1}).calcIsotopePatternPart(2)['calcInt']
            logging.debug(str(protonIsotopePatterns[i][0])+'\t'+str(protonIsotopePatterns[i][1]))
        self._protonIsoPatterns = protonIsotopePatterns