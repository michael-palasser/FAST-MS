from src.services.assign_services.Finders import Finder


class Calibrator(object):
    '''
    Responsible for calibrating ions in a spectrum
    '''
    def __init__(self, theoValues, settings):
        '''
        :param (list[IntactNeutral]) theoValues: library of neutrals
        :param (dict[str,Any]) settings: settings
        '''
        self._finder = Finder(theoValues, settings)
        self._ionData = self._finder.readFile(settings['calIons'])[0]
        errorLimit = settings['errorLimitCalib']
        assignedIons = self._finder.findIonsInSpectrum(0, errorLimit, self._ionData)
        self._calibrationValues, self._errors, self._quality, self._usedIons = \
            self._finder.findCalibrationFunction(assignedIons, errorLimit, settings['maxStd'])

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