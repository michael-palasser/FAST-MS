from copy import deepcopy

from src.services.assign_services.AbstractSpectrumHandler import calculateError
from src.services.assign_services.Finders import IntactFinder, TD_Finder
from numpy import array


class Calibrator(object):
    '''
    Responsible for calibrating ions in a spectrum
    '''
    def __init__(self, theoValues, settings, getChargeRange=None):
        '''
        :param (list[IntactNeutral]) theoValues: library of neutrals
        :param (dict[str,Any]) settings: settings
        '''
        if getChargeRange is None:
            self._finder = IntactFinder(theoValues, settings)
        else:
            self._finder = TD_Finder(theoValues, settings, getChargeRange)
        self._ionData = self._finder.readFile(settings['calIons'])[0]
        self._settings = settings
        errorLimit = settings['errorLimitCalib']
        self._assignedIons = self._finder.findIonsInSpectrum(0, errorLimit, self._ionData)
        self._calibrationValues, self._errors, self._quality, self._usedIons = \
            self._finder.findCalibrationFunction(self._assignedIons, errorLimit, settings['maxStd'])

    def getIonData(self):
        return self._ionData
    def getCalibrationValues(self):
        return self._calibrationValues, self._errors
    def getFinder(self):
        return self._finder

    def getQuality(self):
        return self._quality

    def getUsedIons(self):
        return self._usedIons

    def getIonArray(self):
        l = []
        usedIons = [(ion.getName(),ion.getCharge()) for ion in self._usedIons]
        calData = deepcopy(self._ionData)
        calData['m/z']=self._finder.calibrate(calData['m/z'], self._calibrationValues)
        for ion in self._finder.findIonsInSpectrum(0, self._settings['errorLimitCalib'], self._ionData, False):
            used = False
            if (ion.getName(),ion.getCharge()) in usedIons:
                used=True
            #calMz = self._finder.calibrate(ion.getMonoisotopic(), self._calibrationValues)
            x = ion.getMonoisotopic()
            l.append((x,ion.getCharge(),int(ion.getIntensity()),ion.getName(),
                      round(calculateError(self._calibrationValues[0]*x**2+self._calibrationValues[1]*x+self._calibrationValues[2],ion.getTheoMz()),2),
                                           ion.getTheoMz(),used))
                      #round(calculateError(x,ion.getTheoMz()),2),ion.getTheoMz(),used))

        return array(l, dtype=[('m/z',float),('z',int),('int',int),('name','U32'),('error',float),('m/z_theo',float),('used',bool)])

    def calibratePeaks(self, peaks):
        '''
        Calibrates a peak array
        :param (ndarray[float,float]) peaks: m/z, int
        :return:
        '''
        peaks[:,0] = self._finder.calibrate(peaks[:,0], self._calibrationValues)
        return peaks

    def writePeaks(self, peaks, fileName):
        with open(fileName) as f:
            f.write('m/z\tI\n')
            for peak in peaks:
                f.write(str(peak[0]+'\t'+str(peak[1])+'\n'))

    def recalibrate(self, usedIons):
        updatedIons = [ion for ion in self._assignedIons if (ion.getName(),ion.getCharge()) in usedIons]
        self._calibrationValues, self._errors, self._quality, self._usedIons = \
            self._finder.findCalibrationFunction(updatedIons, self._settings['errorLimitCalib'], self._settings['maxStd'])
