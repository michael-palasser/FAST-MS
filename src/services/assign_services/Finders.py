'''
Created on 1 Oct 2020

@author: michael
'''
from abc import ABC, abstractmethod

import numpy as np
from scipy.optimize import least_squares

from src.Exceptions import InvalidInputException
from src.entities.Ions import SimpleIntactIon, SimpleIon
from src.services.assign_services.AbstractSpectrumHandler import calculateError, getMz, getErrorLimit

#protonMass = 1.00727647


dtype = np.dtype([('m/z', float), ('z', np.uint8), ('relAb', float)])

class AbstractFinder(ABC):
    '''
    Abstract superclass for all finders
    '''
    def __init__(self, theoValues, settings, getZRange):
        '''
        :param (list[IntactNeutral]) theoValues: library of neutrals
        :param dict[str,Any]: settings for intact ions
        '''
        self._theoValues = theoValues
        self._settings = settings
        self._sprayMode = 1
        self._data = list()
        #self._foundIons = None
        self._listOfCalibrationValues = []
        self.getZRange = getZRange

    def getData(self):
        return self._data

    def readFile(self, path):
        '''
        Reads a file with unassigned ion data
        :param (str) path: path of the file
        :return: (list[ndarray]) list of spectra: dtype = [('m/z', float), ('z', np.uint8), ('relAb', float)]
        '''
        if path[-4:] == '.csv':
            return self.openCsvFile(path)
        else:
            return self.openTxtFile(path)
    
    def openTxtFile(self, path, csv=False):
        '''
        Reads a text file with unassigned ion data
        :param (str) path: path of the file
        :return: (list[ndarray]) list of spectra: dtype = [('m/z', float), ('z', np.uint8), ('relAb', float)]
        '''
        data = []
        spectrum = list()
        delimiter = ','
        with open(path) as file:
            for i,line in enumerate(file):
                line = line.rstrip()
                if (i == 0) and (';' in line):
                    delimiter = ';'
                if line.startswith('m/z'):  # ToDo
                    if len(spectrum) != 0:
                        data.append(np.array(spectrum, dtype=dtype))
                        spectrum = list()
                else:
                    try:
                        if not csv:
                            lineList = line.split()
                        else:
                            lineList = line.split(delimiter)
                        charge = lineList[1].replace('+', '').replace('-', '')
                        spectrum.append((lineList[0], charge, lineList[2]))
                    except:
                        print("problem in spectral pattern file: \nline "+str(i), line)
                        continue
            data.append(np.array(spectrum, dtype=dtype))
        return data

    def openCsvFile(self, path):
        '''
        Reads a csv file with unassigned ion data
        :param path: path of csv file
        :return: (list[ndarray]) list of spectra: dtype = [('m/z', float), ('z', np.uint8), ('relAb', float)]
        '''
        with open(path) as file:
            try:
                return [np.loadtxt(path, delimiter=',', usecols=[0, 1, 2],dtype=dtype)]
            except IndexError:
                return [np.loadtxt(path, delimiter=';', usecols=[0, 1, 2],dtype=dtype)]
            except ValueError:
                return self.openTxtFile(path, True)
                #raise InvalidInputException('Incorrect Format of spectral data', '\nThe format must be "m/z,z,int" or "m/z;z;int"')

    def findIonsInSpectrum(self, k, d, spectrum, flag=False):
        '''
        Assigns ions in spectra to corresponding ions:
        function loops over all possible charge states of the ion within the range minMz and maxMz and searches for the
        corresponding ion in the spectrum:
            * if it does not find the ion and the flag is True it also includes misassignments of the monoisotopic m/z
              (monosisotopic +/- 1.00266/z)
            * if more than one ion was found to be within the ppm - threshold and the flag is True the ppm-error
              threshold is set to 6.5. If there is still more than 1 ion or no ion within the threshold the spectral ion
              with the highest abundance is taken
        :param (float) k: slope of error threshold
        :param (float) d: intercept of error threshold
        :param (ndarray[float,float,float]) spectrum: structured array,
            dtype=([('m/z', float), ('z', np.uint8), ('relAb', float)])
        :param (bool) flag: if set, errors in ion list in txt file (+/- 1 Da) are taken in account
        :return: (list[SimpleIntactIon]) assigned ions
        :return:
        '''
        ions = list()
        for neutral in self._theoValues:
            mass = neutral.getMonoisotopicMass()
            radicals = neutral.getRadicals()
            for z in self.getZRange(neutral):
                mz = getMz(mass, z * self._sprayMode, radicals)
                errorLimit = getErrorLimit(mz,k, d)
                mask = np.where((abs(calculateError(spectrum['m/z'], mz)) < errorLimit)
                                & (spectrum['z'] == z))
                if (len(mask[0]) == 1):
                    ions.append(self.getIon(mz, neutral, spectrum[mask][0]))
                elif flag:
                    if len(mask[0]) == 0:
                        mask = np.where(
                            (abs(calculateError(spectrum['m/z'], getMz(mass + 1.00266, z * self._sprayMode, radicals)))
                             < errorLimit) & (spectrum['z'] == z))
                        if len(mask[0]) == 0:
                            mask = np.where(
                                (abs(calculateError(spectrum['m/z'], getMz(mass - 1.00266, z * self._sprayMode, radicals)))
                                 < errorLimit) & (spectrum['z'] == z))

                        if (len(mask[0]) == 1):
                            ions.append(self.getIon(mz, neutral, spectrum[mask][0]))
                            '''Ion(self._settings['sequName'], modif, spectrum[mask]['m/z'][0], mz,
                                spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], nrMod, radicals))'''
                    if len(mask[0]) > 1:
                        # print("more than one ion within error range:",spectralFile[mask])
                        ionPicked = 0
                        if errorLimit > 6.5:
                            newMask = np.where(abs(calculateError(spectrum['m/z'],mz)) < 6.5)
                            if (len(newMask[0]) == 1):
                                ionPicked = 1
                                ions.append(self.getIon(mz, neutral, spectrum[mask][0]))
                                #Ion(self._settings['sequName'], modif, spectrum[newMask]['m/z'][0],
                                #    mz, spectrum[newMask]['z'][0],
                                #   spectrum[newMask]['relAb'][0], nrMod, radicals))
                            elif len(newMask[0]) > 1:
                                mask = newMask
                        if ionPicked == 0:
                            sortedArr = np.sort(spectrum[mask], order='relAb')
                            ions.append(self.getIon(mz, neutral, sortedArr[-1]))
                            #    Ion(self._settings['sequName'], modif, sortedArr[-1]['m/z'], mz,
                            #        sortedArr[-1]['z'], sortedArr[-1]['relAb'], nrMod, radicals))
        '''for i in ions:
            print(i.getName(), i.getModification())'''
        return ions

    @abstractmethod
    def getIon(self, mz, neutral, found):
        pass

    def findCalibrationFunction(self, ionList, errorLimit, maxStd):
        '''
        Calibrates an ion list (spectrum) internally using a quadratic calibration function: m/z_cal=a*(m/z)^2+b*m/z+c
        Loops over each spectral ion list :
            1.  Search for ions in uncalibrated spectral ion list using the user defined ppm threshold for calibration
                (errorLimitCalib)
            2.  Spectral ion list is calibrated by least square method
            3.  If the average ppm error is below 2.5 the spectrum the calibration is used. Otherwise the ppm threshold
                is decreased by 10 ppm and step 2 and 3 are repeated until the average ppm error is below 2.5
        :param (list[SimpleIntactIon]) ionList: list of ions
        :param (float) errorLimit: ppm error threshold
        :param (float) maxStd: max. standard deviation of errors of the ions used for calibration
        :return: ([ndArray[float], ndArray[float], tuple[float], list[SimpleIntactIon]]) calibration variables (a,b,c),
            errors of calibration var., tuple of (av. error, std.dev. of errors), list of ions used for the calibration
        '''
        limit = errorLimit
        solution = [0, 1, 0]
        length = len(ionList)
        while length > 4:
            usedIons = []
            y = list()
            x = list()
            errorList = list()
            for ion in ionList:
                calibratedX = self.fun_parabola(ion.getMonoisotopic(), solution[0], solution[1], solution[2])
                theoMz = ion.getTheoMz()
                if abs(calculateError(calibratedX, theoMz)) < limit:
                    y.append(theoMz)
                    x.append(ion.getMonoisotopic())
                    #errorList.append(abs(getError(calibratedX, theoMz)))
                    errorList.append(calculateError(calibratedX, theoMz))
                    usedIons.append(ion)
            length = len(usedIons)
            if length<6 and limit != errorLimit:
                break
            try:
                #solution, pcov = curve_fit(self.fun_parabola, np.array(x), np.array(y))
                x0 = np.array((0,1,0))
                res_robust = least_squares(self.getLoss, x0, loss='soft_l1', f_scale=0.1, args=(np.array(x), np.array(y)))
                solution = res_robust.x
                J = res_robust.jac
                pcov = np.linalg.inv(J.T.dot(J))
                #print(solution,solution2, np.std(errorList), np.sqrt(res_robust.cost))
                #print(pcov,pcov2)
                limit *= 0.67
            except ValueError:
                if limit < 100:
                    limit += 5
                else:
                    raise InvalidInputException('Calibration not possible',
                                                'Nr of found ions is too low to calibrate (' + str(len(ionList)) +
                                                ').    Are you sure you picked the correct settings?')
            errorList = np.array(errorList)
            #if np.average(np.abs(errorList)) < 1.0 and np.std(errorList) < 2.0:
            if np.std(errorList) < maxStd:
                break
        if solution[0] == 0:
            raise InvalidInputException('Calibration not possible',
                                        'Nr of found ions is too low to calibrate (' + str(len(ionList)) +
                                        ').    Are you sure you picked the correct settings?')
        return solution, np.sqrt(np.diag(pcov)), (np.average(np.abs(errorList)), np.std(errorList)), usedIons



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

    @staticmethod
    def getLoss(solution, x, y):
        '''
        Quadratic calibration function: a * x^2 + b * x + c
        :param (float) x: m/z
        :param (float) a:
        :param (float) b:
        :param (float) c:
        :return: (float) value of the calibration function
        '''
        return solution[0] * x ** 2 + solution[1] * x + solution[2] -y

    def calibrate(self, uncalibrated, solution):
        return self.fun_parabola(uncalibrated, solution[0],solution[1],solution[2])


class IntactFinder(AbstractFinder):
    '''
    Responsible for assigning ions
    '''
    def __init__(self, theoValues, settings):
        '''
        :param (list[IntactNeutral]) theoValues: library of neutrals
        :param dict[str,Any]: settings for intact ions
        '''
        super(IntactFinder, self).__init__(theoValues, settings, self.getChargeRange)
        if self._settings['sprayMode'] == 'negative':
            self._sprayMode *= -1
        self._abundanceInput = False
        if 'inputMode' in settings.keys():
            self._abundanceInput = settings['inputMode']


    def getChargeRange(self, neutral):
        '''
        Calculates possible charge states (z) in the given m/z window
        :param (float) mass: mass of the unmodified species
        :return: (generator) range between lowest possible z and highest possible z
        '''
        mass = neutral.getMonoisotopicMass()
        minMz = self._settings['minMz']
        maxMz = self._settings['maxMz']
        return range(int(mass/maxMz+1), int(mass/minMz)+1)


    def readData(self,files):
        '''
        Reads txt files containing ion data (format: m/z    z   relAb) and creates a 2D array (m/z, z, relAb)
        :param (list[str]) files: paths of txt files
        '''
        self._files = files
        #dtype = np.dtype([('m/z', float), ('z', np.uint8), ('relAb', float)])
        for path in files:
            '''data = []
            spectrum = list()
            with open(path) as file:
                for line in file:
                    line = line.rstrip()
                    if line.startswith('m/z'): #ToDo
                        if len(spectrum) != 0:
                            data.append(np.array(spectrum, dtype=dtype))
                            spectrum = list()
                    else:
                        try:
                            lineList = line.split()
                            charge = lineList[1].replace('+','').replace('-','')
                            spectrum.append((lineList[0], charge, lineList[2]))
                        except:
                            print("problem in spectral pattern file: \nline", line)
                            continue
            data.append(np.array(spectrum, dtype=dtype))'''
            self._data.append(self.readFile(path))


    """def getMz(self, mass, z):
        return mass / z + protonMass * self._sprayMode"""

    '''@staticmethod
    def getError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6'''

    """def getErrorLimit(self,k, d, mz):
        '''
        calculates error threshold in ppm
        :param (float) k: slope of error threshold
        :param (float) d: intercept of error threshold
        :param (float) mz: corresponding (theoretical) m/z
        :return: (float) threshold
        '''
        return k / 1000 * mz + d"""


    def findIons(self, k, d, flag=False):
        '''
        Assigns ions in spectrum to corresponding ions:
        function loops over all possible charge states of the ion within the range minMz and maxMz and searches for the
        corresponding ion in the spectrum:
            * if it does not find the ion and the flag is True it also includes misassignments of the monoisotopic m/z
              (monoisotopic +/- 1.00266/z)
            * if more than one ion was found to be within the ppm - threshold and the flag is True the ppm-error
              threshold is set to 6.5. If there is still more than 1 ion or no ion within the threshold the spectral ion
              with the highest abundance is taken
        :param (float) k: slope of error threshold
        :param (float) d: intercept of error threshold
        :param (bool) flag: if set, errors in ion list in txt file (+/- 1 Da) are taken in account
        :return: (list[list[list[SimpleIntactIon]]]) list (files) of list (spectra in 1 file) of ions
        '''
        listOfIonLists = []
        for spectra in self._data:
            ionLists = list()
            for spectrum in spectra:
                '''ions = list()
                for modif, val in self._theoValues.items():
                    mass = val[0]
                    z = 1
                    while True:
                        if self.getMonoisotopicMass(mass,z) < self._settings['minMz']:
                            break
                        elif self.getMonoisotopicMass(mass,z) < self._settings['maxMz']:
                            errorLimit = self.getErrorLimit(k, d, self.getMonoisotopicMass(mass, z))
                            mask = np.where((abs(getError(spectrum['m/z'], self.getMonoisotopicMass(mass,z))) < errorLimit)
                                            & (spectrum['z'] == z))
                            if (len(mask[0]) == 1):
                                ions.append(Ion(self._settings['sequName'], modif, spectrum[mask]['m/z'][0], self.getMonoisotopicMass(mass, z),
                                                spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], val[1]))

                            elif flag:
                                if len(mask[0]) == 0:
                                    mask = np.where(
                                        (abs(getError(spectrum['m/z'], self.getMonoisotopicMass(mass+1.00266, z)))
                                            < errorLimit) & (spectrum['z'] == z))
                                    if len(mask[0]) == 0:
                                        mask = np.where(
                                            (abs(getError(spectrum['m/z'], self.getMonoisotopicMass(mass-1.00266, z)))
                                                < errorLimit) & (spectrum['z'] == z))

                                    if (len(mask[0]) == 1):
                                        ions.append(
                                            Ion(self._settings['sequName'], modif, spectrum[mask]['m/z'][0], self.getMonoisotopicMass(mass, z),
                                                spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], val[1]))
                                if len(mask[0]) > 1:
                                    #print("more than one ion within error range:",spectralFile[mask])
                                    ionPicked = 0
                                    if errorLimit > 6.5:
                                        newMask = np.where(abs(getError(spectrum['m/z'],
                                                                                   self.getMonoisotopicMass(mass,z))) < 6.5)
                                        if (len(newMask[0]) == 1):
                                            ionPicked = 1
                                            ions.append(Ion(self._settings['sequName'], modif, spectrum[newMask]['m/z'][0],
                                                            self.getMonoisotopicMass(mass,z), spectrum[newMask]['z'][0],
                                                            spectrum[newMask]['relAb'][0], val[1]))
                                        elif len(newMask[0]) > 1:
                                            mask = newMask
                                    if ionPicked == 0:
                                        sortedArr = np.sort(spectrum[mask], order='relAb')
                                        ions.append(
                                            Ion(self._settings['sequName'], modif, sortedArr[-1]['m/z'], self.getMonoisotopicMass(mass, z),
                                                sortedArr[-1]['z'], sortedArr[-1]['relAb'], val[1]))
                        z+=1'''
                ionLists.append(self.findIonsInSpectrum(k, d, spectrum, flag))
            listOfIonLists.append(ionLists)
        return listOfIonLists

    """def findIonsInSpectrum(self, k, d, spectrum, flag=False):
        '''
        Assigns ions in spectra to corresponding ions:
        function loops over all possible charge states of the ion within the range minMz and maxMz and searches for the
        corresponding ion in the spectrum:
            * if it does not find the ion and the flag is True it also includes misassignments of the monoisotopic m/z
              (monosisotopic +/- 1.00266/z)
            * if more than one ion was found to be within the ppm - threshold and the flag is True the ppm-error
              threshold is set to 6.5. If there is still more than 1 ion or no ion within the threshold the spectral ion
              with the highest abundance is taken
        :param (float) k: slope of error threshold
        :param (float) d: intercept of error threshold
        :param (ndarray[float,float,float]) spectrum: structured array,
            dtype=([('m/z', float), ('z', np.uint8), ('relAb', float)])
        :param (bool) flag: if set, errors in ion list in txt file (+/- 1 Da) are taken in account
        :return: (list[SimpleIntactIon]) assigned ions
        :return:
        '''
        ions = list()
        for neutral in self._theoValues:
            mass = neutral.getMonoisotopicMass()
            modif = neutral.getModification()
            nrMod = neutral.getNrOfModifications()
            radicals = neutral.getRadicals()
            z = 1
            while True:
                mz = getMz(mass, z*self._sprayMode, radicals)
                if mz < self._settings['minMz']:
                    break
                elif mz < self._settings['maxMz']:
                    errorLimit = getErrorLimit(k, d, mz)
                    mask = np.where((abs(calculateError(spectrum['m/z'], mz)) < errorLimit)
                                    & (spectrum['z'] == z))
                    if (len(mask[0]) == 1):
                        ions.append(Ion(self._settings['sequName'], modif, spectrum[mask]['m/z'][0],
                                        mz, spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], nrMod, radicals))
                    elif flag:
                        if len(mask[0]) == 0:
                            mask = np.where(
                                (abs(calculateError(spectrum['m/z'], getMz(mass + 1.00266, z*self._sprayMode, radicals)))
                                 < errorLimit) & (spectrum['z'] == z))
                            if len(mask[0]) == 0:
                                mask = np.where(
                                    (abs(calculateError(spectrum['m/z'], getMz(mass - 1.00266, z*self._sprayMode, radicals)))
                                     < errorLimit) & (spectrum['z'] == z))

                            if (len(mask[0]) == 1):
                                ions.append(
                                    Ion(self._settings['sequName'], modif, spectrum[mask]['m/z'][0], mz,
                                        spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], nrMod, radicals))
                        if len(mask[0]) > 1:
                            # print("more than one ion within error range:",spectralFile[mask])
                            ionPicked = 0
                            if errorLimit > 6.5:
                                newMask = np.where(abs(calculateError(spectrum['m/z'],mz)) < 6.5)
                                if (len(newMask[0]) == 1):
                                    ionPicked = 1
                                    ions.append(
                                        Ion(self._settings['sequName'], modif, spectrum[newMask]['m/z'][0],
                                            mz, spectrum[newMask]['z'][0],
                                            spectrum[newMask]['relAb'][0], nrMod, radicals))
                                elif len(newMask[0]) > 1:
                                    mask = newMask
                            if ionPicked == 0:
                                sortedArr = np.sort(spectrum[mask], order='relAb')
                                ions.append(
                                    Ion(self._settings['sequName'], modif, sortedArr[-1]['m/z'], mz,
                                        sortedArr[-1]['z'], sortedArr[-1]['relAb'], nrMod, radicals))
                z += 1
        return ions"""

    def getIon(self, mz, neutral, found):
        intensity = found['relAb']
        if self._abundanceInput:
            intensity *= found['z']
        return SimpleIntactIon(self._settings['sequName'], neutral.getModification(), found['m/z'], mz, found['z'],
                               intensity, neutral.getNrOfModifications(), neutral.getRadicals())

    def calibrateAll(self):
        '''
        Calibrates spectra internally using a quadratic calibration function:
        Loops over each spectral ion list :
            1.  Search for ions in uncalibrated spectral ion list using the user defined ppm threshold for calibration
                (errorLimitCalib)
            2.  Spectral ion list is calibrated by least square method
            3.  If the average ppm error is below 2.5 the spectrum the calibration is used. Otherwise the ppm threshold
                is decreased by 10 ppm and step 2 and 3 are repeated until the average ppm error is below 2.5
        '''
        #count = 1
        errorLimit = self._settings['errorLimitCalib']
        maxStd = self._settings['maxStd']
        '''for fileNr, ionLists in enumerate(self.findIons(0, errorLimit)):'''
        for fileNr, spectra in enumerate(self._data):
            calibrationValues = []
            for i, spectrum in enumerate(spectra):
                ionList = self.findIonsInSpectrum(0, errorLimit, spectrum)
                '''limit = errorLimit
                solution = [0,1,0]
                while limit >=10 :
                    y = list()
                    x = list()
                    errorList = list()
                    for ion in ionList:
                        calibratedX = self.fun_parabola(ion.getMonoisotopicMass(), solution[0], solution[1], solution[2])
                        theoMz = ion.getTheoMz()
                        if abs(getError(calibratedX, theoMz)) < limit:
                            y.append(theoMz)
                            x.append(ion.getMonoisotopicMass())
                            errorList.append(abs(getError(calibratedX, theoMz)))
                    try:
                        solution, pcov = curve_fit(self.fun_parabola, np.array(x), np.array(y))
                        limit -= 10
                    except ValueError:
                        if limit<100:
                            limit +=5
                        else:
                            raise InvalidInputException(self._files[fileNr],
                                                        'Nr of found ions in spectrum '+str(i)+
                                                        ' is too low to calibrate ('+str(len(ionList))+').    '
                                                       'Are you sure you picked the correct settings?')
                    errorList = np.array(errorList)
                    if np.average(errorList) < 1.0 and np.std(errorList)<2.0: #ToDo: to parameters
                        break'''
                #count += 1
                try:
                    calibrationValues.append(self.findCalibrationFunction(ionList,errorLimit, maxStd)[0])
                except InvalidInputException:
                    raise InvalidInputException(self._files[fileNr],
                                                'Nr of found ions in spectrum ' + str(i) +
                                                ' is too low to calibrate (' + str(len(ionList)) + ').    '
                                                                    'Are you sure you picked the correct settings?')
            self._listOfCalibrationValues.append(calibrationValues)
        newData = list()
        for spectrumFile, calibrationValues in zip(self._data, self._listOfCalibrationValues):
            newFileData = []
            for spectrum,solution in zip(spectrumFile, calibrationValues):
                spectrum['m/z'] = self.fun_parabola(spectrum['m/z'], solution[0],solution[1],solution[2])
                newFileData.append(spectrum)
            newData.append(newFileData)
        self._data = newData
        return self._listOfCalibrationValues



    """def findCalibrationFunctionManually(self,ionList):
        '''

        :param (ndarray[float,float,float]) ionList: structured array, dtype=([('m/z', float), ('z', np.uint8), ('relAb', float)])
        :return: ([ndArray[float], ndArray[float], tuple[float], list[SimpleIntactIon]]) calibration variables (a,b,c), 
            errors of calibration var., tuple of (av. error, std.dev. of errors), list of ions used for the calibration
        '''
        x,y, errorList = [],[], []
        for ion in ionList:
            theoMz = ion.getTheoMz()
            y.append(theoMz)
            x.append(ion.getMonoisotopicMass())
        try:
            solution, pcov = curve_fit(self.fun_parabola, np.array(x), np.array(y))
        except ValueError:
            raise InvalidInputException('Calibration not possible',
                                        'Nr of ions is too low to calibrate (' + str(len(ionList)) +').')
        for ion in ionList:
            calibratedX = self.calibrate(ion.getMonoisotopicMass(), solution)
            errorList.append(calculateError(calibratedX, ion.getTheoMz()))
        return solution, pcov, errorList"""


class TD_Finder(AbstractFinder):
    '''
    Responsible for assigning ions in top-down spectrum
    '''

    def __init__(self, theoValues, settings, getZRange):
        '''
        :param (list[Fragment]) theoValues: library of fragments
        :param dict[str,Any]: settings
        '''
        super(TD_Finder, self).__init__(theoValues, settings, getZRange)
        if self._settings['charge'] < 0:
            self._sprayMode *= -1


    def getIon(self, mz, neutral, found):
        '''return FragmentIon(neutral, found['m/z'], found['z'], [], mz,
                               ,
                               found['relAb'], neutral.getNrOfModifications(), neutral.getRadicals())'''
        return SimpleIon(neutral, found['m/z'], mz, found['z'],found['relAb'])