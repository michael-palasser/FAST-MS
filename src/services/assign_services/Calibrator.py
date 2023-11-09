from copy import deepcopy
from numpy import dtype, uint8, int64
from src.repositories.SpectralDataReader import SpectralDataReader

from src.services.assign_services.AbstractSpectrumHandler import calculateError
from src.services.assign_services.Finders import IntactFinder, TD_Finder
from numpy import array


class Calibrator(object):
    '''
    Responsible for calibrating a peak list using a ion list
    '''
    def __init__(self, theoValues, settings, getChargeRange=None):
        '''
        :param (list[IntactNeutral]) theoValues: library of neutrals
        :param (dict[str,Any]) settings: settings
        :param (Callable) getChargeRange: optional, method to calculate the charge range of a fragment
        '''
        if getChargeRange is None:
            self._finder = IntactFinder(theoValues, settings)
        else:
            self._finder = TD_Finder(theoValues, settings, getChargeRange)
        #self._ionData = self._finder.readFile(settings['calIons'])[0]
        self._settings = settings
        self._ionData = SpectralDataReader().openFile(self._settings['calIons'],
                                                      dtype([('m/z', float), ('z', uint8), ('I', float)]))
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
        '''
        Searches for ions in ion list and returns their values as an array
        :return: (ndarray[dtype = [('m/z',float),('z',int),('int',int),('name','U32'),('error',float),('m/z_theo',float),('used',bool)]])
        '''
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

        return array(l, dtype=[('m/z',float),('z',int),('int',int64),('name','U32'),('error',float),('m/z_theo',float),('used',bool)])

    def calibratePeaks(self, peaks):
        '''
        Calibrates a peak array
        :param (ndarray[float,float]) peaks: array with columns m/z, int
        :return: (ndarray[float,float]) calibrated peaks
        '''
        peaks['m/z'] = self._finder.calibrate(peaks['m/z'], self._calibrationValues)
        return peaks

    @staticmethod
    def writePeaks(peaks, fileName):
        '''
        Writes a calibrated peak list to a file
        :param (ndarray[float,float]) peaks: array with columns m/z, int
        :param (str) fileName: name of the file
        '''
        with open(fileName, 'w') as f:
            f.write('m/z\tI\n')
            for peak in peaks:
                f.write(str(peak['m/z'])+'\t'+str(peak['I'])+'\n')

    def recalibrate(self, usedIons):
        '''
        Calculates the calibration function by a given ion list
        :param (tuple[str,int]) usedIons: hashes of ions (name, charge) that should be used for calibration
        '''
        updatedIons = [ion for ion in self._assignedIons if (ion.getName(),ion.getCharge()) in usedIons]
        self._calibrationValues, self._errors, self._quality, self._usedIons = \
            self._finder.findCalibrationFunction(updatedIons, self._settings['errorLimitCalib'], self._settings['maxStd'])

