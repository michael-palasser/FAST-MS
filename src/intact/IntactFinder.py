'''
Created on 1 Oct 2020

@author: michael
'''

import numpy as np
from scipy.optimize import curve_fit
from src.entities.Ions import IntactIon as Ion
from src.top_down.SpectrumHandler import calculateError

protonMass = 1.00727647


class Finder(object):
    '''
    Responsible for assigning ions
    '''
    def __init__(self, theoValues, configHandler):
        '''
        :param (dict[str, MolecularFormula]) theoValues: library of formulas {name:formula}
        :param configHandler: (ConfigHandler) configurationHandler for intact ions
        '''
        self._theoValues = theoValues
        self._mode = 1
        if configHandler.get('sprayMode') == 'negative':
            self._mode *= -1
        self._configHandler = configHandler
        self._data = list()
        self._foundIons = list()

    def getData(self):
        return self._data

    def readData(self,file):
        '''
        Reads txt files containing ion data (format: m/z    z   relAb) and creates a 2D array (m/z, z, relAb)
        :param (file) file: opened txt file
        '''
        spectrum = list()
        dtype = np.dtype([('m/z', np.float64), ('z', np.uint8), ('relAb', np.float64)])
        for line in file:
            line = line.rstrip()
            if line.startswith('m/z'):
                if len(spectrum) != 0:
                    self._data.append(np.array(spectrum, dtype=dtype))
                    spectrum = list()
            else:
                try:
                    lineList = line.split()
                    spectrum.append((lineList[0], lineList[1][:-1], lineList[2]))
                except:
                    print("problem in spectral pattern file: \nline", line)
                    continue
        self._data.append(np.array(spectrum, dtype=dtype))


    def getMz(self, mass, z):
        return mass / z + protonMass * self._mode


    '''@staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6'''

    def getErrorLimit(self,k, d, mz):
        '''
        calculates error threshold in ppm
        :param (float) k: slope of error threshold
        :param (float) d: intercept of error threshold
        :param (float) mz: corresponding (theoretical) m/z
        :return: (float) threshold
        '''
        return k / 1000 * mz + d


    def findIons(self, k, d, flag=False):
        '''
        Assigns ions in spectrum to corresponding ions:
        function loops over all possible charge states of the ion within the range minMz and maxMz and searches for the
        corresponding ion in the spectrum:
            * if it does not find the ion and the flag is True it also includes misassignments of the monoisotopic m/z
              (monosisotopic +/- 1.00266/z)
            * if more than one ion was found to be within the ppm - threshold and the flag is True the ppm-error
              threshold is set to 6.5. If there is still more than 1 ion or no ion within the threshold the spectral ion
              with the highest abundance is taken
        :param (float) k: slope of error threshold
        :param (float) d: intercept of error threshold
        :param (bool) flag: if set, errors in ion list in txt file (+/- 1 Da) are taken in account
        :return: (list[list[IntactIon]]) ions
        '''
        ionLists = list()
        for spectrum in self._data:
            ions = list()
            for modif, val in self._theoValues.items():
                mass = val[0]
                z = 1
                while True:
                    if self.getMz(mass,z) < self._configHandler.get('minMz'):
                        break
                    elif self.getMz(mass,z) < self._configHandler.get('maxMz'):
                        errorLimit = self.getErrorLimit(k, d, self.getMz(mass, z))
                        mask = np.where((abs(calculateError(spectrum['m/z'], self.getMz(mass,z))) < errorLimit)
                                        & (spectrum['z'] == z))
                        if (len(mask[0]) == 1):
                            ions.append(Ion(self._configHandler.get('sequName'), modif, spectrum[mask]['m/z'][0], self.getMz(mass, z),
                                            spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], val[1]))

                        elif flag:
                            if len(mask[0]) == 0:
                                mask = np.where(
                                    (abs(calculateError(spectrum['m/z'], self.getMz(mass+1.00266, z)))
                                        < errorLimit) & (spectrum['z'] == z))
                                if len(mask[0]) == 0:
                                    mask = np.where(
                                        (abs(calculateError(spectrum['m/z'], self.getMz(mass-1.00266, z)))
                                            < errorLimit) & (spectrum['z'] == z))

                                if (len(mask[0]) == 1):
                                    ions.append(
                                        Ion(self._configHandler.get('sequName'), modif, spectrum[mask]['m/z'][0], self.getMz(mass, z),
                                            spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], val[1]))
                            if len(mask[0]) > 1:
                                #print("more than one ion within error range:",spectralFile[mask])
                                ionPicked = 0
                                if errorLimit > 6.5:
                                    newMask = np.where(abs(calculateError(spectrum['m/z'],
                                                                               self.getMz(mass,z))) < 6.5)
                                    if (len(newMask[0]) == 1):
                                        ionPicked = 1
                                        ions.append(Ion(self._configHandler.get('sequName'), modif, spectrum[newMask]['m/z'][0],
                                                        self.getMz(mass,z), spectrum[newMask]['z'][0],
                                                        spectrum[newMask]['relAb'][0], val[1]))
                                    elif len(newMask[0]) > 1:
                                        mask = newMask
                                if ionPicked == 0:
                                    sortedArr = np.sort(spectrum[mask], order='relAb')
                                    ions.append(
                                        Ion(self._configHandler.get('sequName'), modif, sortedArr[-1]['m/z'], self.getMz(mass, z),
                                            sortedArr[-1]['z'], sortedArr[-1]['relAb'], val[1]))
                    z+=1
            ionLists.append(ions)
        return ionLists


    @staticmethod
    def fun_parabola(x,a,b,c):
        '''
        Quadratic calibration function: a * x^2 + b * x + c
        :param (float) x: m/z
        :param (float) a:
        :param (float) b:
        :param (float) c:
        :return: (float) value of the calibration function
        '''
        return a * x**2 + b * x + c


    def calibrate(self):
        '''
        Calibrates spectra internally using a quadratic calibration function:
        Loops over each spectral ion list :
            1.  Search for ions in uncalibrated spectral ion list using the user defined ppm threshold for calibration
                (errorLimitCalib)
            2.  Spectral ion list is calibrated by least square method
            3.  If the average ppm error is below 2.5 the spectrum the calibration is used. Otherwise the ppm threshold
                is decreased by 10 ppm and step 2 and 3 are repeated until the average ppm error is below 2.5
        '''
        calibrationValues = list()
        count = 1
        errorLimit = self._configHandler.get('errorLimitCalib')
        for ionList in self.findIons(0, errorLimit):
            limit = errorLimit
            solution = [0,1,0]
            while limit >=10 :
                y = list()
                x = list()
                errorList = list()
                print('new Limit',limit)
                for ion in ionList:
                    calibratedX = self.fun_parabola(ion.getMz(), solution[0], solution[1], solution[2])
                    theoMz = ion.getTheoMz()
                    print(abs(calculateError(calibratedX, theoMz)))
                    if abs(calculateError(calibratedX, theoMz)) < limit:
                        y.append(theoMz)
                        x.append(ion.getMz())
                        errorList.append(abs(calculateError(calibratedX, theoMz)))
                solution, pcov = curve_fit(self.fun_parabola, np.array(x), np.array(y))
                limit -= 10
                errorList = np.array(errorList)
                if np.average(errorList) < 1.0 and np.std(errorList)<2.0: #ToDo: to parameters
                    break
            count += 1
            calibrationValues.append(solution)
        newData = list()
        for spectrum,solution in zip(self._data, calibrationValues):
            spectrum['m/z'] = self.fun_parabola(spectrum['m/z'], solution[0],solution[1],solution[2])
            newData.append(spectrum)
        self._data = newData

