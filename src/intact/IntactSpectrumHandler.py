import logging

import numpy as np

from src.entities.Ions import IntactIon
from src.top_down.SpectrumHandler import AbstractSpectrumHandler


class IntactSpectrumHandler(AbstractSpectrumHandler):
    def __init__(self, settings, peaks=None):
        '''
        Constructor, also processes spectrum
        :param (dict[str,Any]) settings: search settings
        :param (set[tuple[float]] | None) peaks: set of peak tuples (m/z, I)
        '''
        super(IntactSpectrumHandler, self).__init__(settings, settings['sprayMode'], IntactIon, peaks)


    def getChargeRange(self, mass):
        '''
        Calculates possible charge states (z) in the given m/z window
        :param (float) mass: mass of the unmodified species
        :param (float) minMz: minimal m/z
        :param (float) maxMz: maximum m/z
        :return: (generator) range between lowest possible z and highest possible z
        '''
        return range(int(mass/self._settings['maxMz'])+1, int(mass/self._settings['minMz'])+1)

    def findIons(self, neutralLibrary):
        '''
        Assigns peaks in spectrum to isotope peaks of corresponding ion
        1. Possible charges of species are calculated
        2. Search for n highest isotope peaks in spectrum: n either 1, 2 or 3 (see Fragment.getNumberOfHighestIsotopes)
        3. If found noise is calculated and the isotope peaks which could theoretically be above the noise are calculated:
            Programm searches for these peaks in spectrum
            If all isotope peaks are calculated to be below noise threshold, ion is added to deleted ion (comment = noise)
        :param (list) fragmentLibrary: list of Fragment-objects
        '''
        np.set_printoptions(suppress=True)
        self.getProtonIsotopePatterns()
        sortedMasses = sorted([neutral.getIsotopePattern()['m/z'][0] for neutral in neutralLibrary])
        zRange = self.getChargeRange(sortedMasses[0])
        for neutral in neutralLibrary:
            # neutralPatternFFT = formula.calculateIsotopePatternFFT(1, )
            logging.info(neutral.getName())
            self._searchedChargeStates[neutral.getName()] = []
            self.findIon(neutral, zRange)