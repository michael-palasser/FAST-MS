import numpy as np

from src.services.assign_services.AbstractSpectrumHandler import calculateError, getErrorLimit


class PeakMatcher(object):
    def __init__(self, k, d, peakDtype):
        self._k = k
        self._d = d
        self._peakDtype = peakDtype


    def matchPeaks(self, ions, peaks):
        usedPeaks = []
        for ion in ions:
            peak=self.findPeak(ion.getMonoisotopic(), peaks)
            ion.setMonoPeak(peak)
            if peak['m/z']>0:
                usedPeaks.append(peak['m/z'])
        overlaps = self.checkPeaks(usedPeaks)
        return ions, overlaps


    def matchPeaks2(self, foundIons, data):
        ionDict = {}
        for ion in foundIons:
            ionDict[ion.getHash()] = self.findPeak(ion.getMonoisotopic(), data)
        return ionDict

    def matchIons(self, foundIons, snapIons):
        ionDict = {}
        for foundIon in foundIons:
            for snapIon in snapIons:
                if (foundIon.getName()==snapIon.getName()) and (foundIon.getCharge()==snapIon.getCharge()):
                    ionDict[foundIon.getHash()] = snapIon
        return ionDict
        
    def findPeak(self, theoPeak, peaks):
        searchMask = np.where(abs(calculateError(peaks['m/z'], theoPeak)) < getErrorLimit(peaks['m/z'], self._k, self._d))
        return self.getCorrectPeak(peaks[searchMask], theoPeak)

    def getCorrectPeak(self, foundpeaks, theoPeak):
        '''
        Selects the correct peak in spectrum for a theoretical isotope peak
        Correct is the peak with the lowest ppm error
        :param (ndArray (dtype=float)) foundpeaks:
        :param (ndArray (dtype=[float,float]) theoPeak: calculated peak (structured array [m/z,calcInt])
        :return: (Tuple[float, int, float, float, bool]) m/z, z, int, error, used
        '''
        if len(foundpeaks) == 0:
            return np.array([(0,0,0)], dtype=self._peakDtype)  # passt mir noch nicht
        elif len(foundpeaks) == 1:
            return foundpeaks[0]
        else:
            lowestError = 100
            for peak in foundpeaks: #ToDo
                error = calculateError(peak['m/z'], theoPeak)
                if abs(error) < abs(lowestError):
                    lowestError = error
                    lowestErrorPeak = peak
            return lowestErrorPeak

    @staticmethod
    def checkPeaks(usedPeaks):
        peakSet = set()
        overlaps = []
        for peak in usedPeaks:
            if peak in peakSet:
                overlaps.append(peak)
            else:
                peakSet.add(peak)
        return overlaps