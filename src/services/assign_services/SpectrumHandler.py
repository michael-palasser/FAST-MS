'''
Created on 27 Jul 2020

@author: michael
'''
from abc import ABC
from math import exp
from re import findall
from subprocess import call
import logging
import numpy as np
import copy
from scipy.constants import R

from src.Exceptions import InvalidInputException
from src.FormulaFunctions import eMass, protMass
from src.MolecularFormula import MolecularFormula
from src.entities.Ions import FragmentIon
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
#from Other.simpleFunctions import eMass, protMass

configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename='logfile_SpectrumHandler.log',level=logging.INFO)

def getErrorLimit(mz):
    return configs['k']/1000 * mz + configs['d']


def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6

def getMz(mass, z, radicals):
    '''
    Calculates m/z
    :param (float) mass: neutral mass
    :param (int) z: charge
    :param (int) radicals: number of radicals
    :return: (float) m/z
    '''
    if z != 0:
        return abs(mass / z + protMass) + radicals * (eMass + protMass) / z
    else:
        return abs(mass) + radicals*(eMass + protMass)

class AbstractSpectrumHandler(ABC):
    '''
    Abstract superclass for reading a spectrum (peak list), calculating the noise and finding isotope peaks
    '''
    def __init__(self, settings, spraymode, IonClass, peaks=None):
        self._settings = settings
        self._sprayMode = spraymode
        self._upperBound = 0
        self._normalizationFactor = None
        self._foundIons = list()
        self._ionsInNoise = list()
        self._searchedChargeStates = dict()
        if peaks == None:
            print('hey', self._settings['spectralData'])
            self.addSpectrum(self._settings['spectralData'])
        else:
            self._spectrum = np.array(sorted(list(peaks), key=lambda tup: tup[0]))
            self._upperBound = np.max(peaks)
        self._IonClass = IonClass
        self._foundIons = list()
        self._ionsInNoise = list()
        self._searchedChargeStates = dict()
        # self.expectedChargeStates = dict()
        self._peaksArrType = np.dtype([('m/z', float), ('relAb', float),
                                       ('calcInt', float), ('error', np.float32), ('used', bool)])
        self._peaksArrType = np.dtype([('m/z', float), ('relAb', float),
                                       ('calcInt', float), ('error', np.float32), ('used', bool)])

    def getSpectrum(self, *args):
        '''
        Returns either full or part of spectrum (peak list)
        :param (tuple of float) args: if args (lowerbound, upperbound), just part of the spectrum is returned
        :return: (ndarray(dtype=float, ndim=2)) spectrum
        '''
        if args and args[1]:
            return self._spectrum[np.where((self._spectrum[:, 0] > args[0]) & (self._spectrum[:, 0] < args[1]))]
        return self._spectrum

    def setSpectrum(self, spectrum):
        self._spectrum = spectrum

    def getSprayMode(self):
        return self._sprayMode

    def getUpperBound(self):
        return self._upperBound

    def getFoundIons(self):
        return self._foundIons

    def getIonsInNoise(self):
        return self._ionsInNoise

    def getSearchedChargeStates(self):
        return self._searchedChargeStates

    def emptyLists(self):
        self._foundIons = None
        self._ionsInNoise = None

    def addSpectrum(self,filePath):
        '''
        Add spectrum from file
        :param (str) filePath: path of txt or csv file
        '''
        with open(filePath, mode='r', encoding='utf_8_sig') as f:
            if filePath[-4:] == '.csv':
                self._spectrum = self.addSpectrumFromCsv(f)
            else:
                self._spectrum = self.addSpectrumFromTxt(f)
        self.resizeSpectrum()

    def addSpectrumFromCsv(self, file):
        '''
        :param file: opended csv-file
        :return: (ndarray(dtype=float, ndim=2)) [(m/z, int)]
        '''
        #skip = 0
        #lines = file.readlines()
        '''print(lines)
        if 'm/z' in lines[0]:
            skip = 1
        else:
            print(lines[0])
            raw = lines[0].split(',')
            print(raw)
            toAdd = np.empty(2,dtype=float)
            toAdd[0] = float(raw[0].encode('utf-8-sig').decode('utf-8-sig'))
            toAdd[1] = float(raw[1][:-2])
            print('dsf',toAdd)'''
        try:
            #print(np.loadtxt(lines[1:], delimiter=',', skiprows=1, usecols=[0, 1]))
            #return np.loadtxt(lines, delimiter=',', skiprows=skip, usecols=[0, 2])
            return np.loadtxt(file, delimiter=',', skiprows=1, usecols=[0, 1])
        except IndexError:
            #return np.loadtxt(lines, delimiter=';', skiprows=skip, usecols=[0, 2])
            return np.loadtxt(file, delimiter=';', skiprows=1, usecols=[0, 1])
        except ValueError:
            raise InvalidInputException('Incorrect Format of spectral data', '\nThe format must be "m/z,int" or "m/z;int"')

    def addSpectrumFromTxt(self, file):
        '''
        :param file: opended txt-file
        :return: (ndarray(dtype=float, ndim=2)) [(m/z, int)]
        '''
        spectralList = list()
        for i,line in enumerate(file):
            if line.startswith("m/z"):
                continue
            line = line.rstrip().split()
            if len(line)>1:
                try:
                    spectralList.append((float(line[0]),float(line[1])))
                except ValueError:
                    try:
                        call(['open', self._settings['spectralData']])
                    except:
                        pass
                    raise InvalidInputException('Problem with format in spectral data', '  '.join(line) + ' (line ' + str(i) +
                                                ') Format must be  "m/z    Int." !')
        return np.array(spectralList)

    def resizeSpectrum(self):
        '''
        Truncates spectrum
        '''
        self._spectrum = self._spectrum[np.where(self._spectrum[:, 0] < (self.findUpperBound() + 10))]
        print("\nmax m/z:", self._upperBound)


    def findUpperBound(self):
        '''
        Finds the highest m/z in spectrum where non-noise peaks occur
        :return: (int) m/z (upperBound)
        '''
        print("\n********** Finding upper bound m/z - Window in spectralFile containing fragments ********** ")
        windowSize = configs['upperBoundWindowSize']
        currentMz = configs['minUpperBound']
        #tolerance = 50

        peaksHigherThanNoise = list()
        logging.debug('********** Calculating noise **********\nm/z\tnoise')
        while currentMz < np.max(self._spectrum[:,0]):#2500:
            currentWindow = self.getPeaksInWindow(self._spectrum, currentMz, windowSize)
            noise = self.calculateNoise(currentMz,windowSize,currentWindow)
            logging.debug(str(currentMz)+'\t'+ str(noise))
            #currentWindow = self.getPeaksInWindow(self._spectrum, currentMz, windowSize)
            peaksHigherThanNoise.append((currentMz, currentWindow[np.where(currentWindow > (noise * 5))].size))
            currentMz += 1
        peaksHigherThanNoise = np.array(peaksHigherThanNoise)
        windowSize, currentMz = 100 , configs['minUpperBound']
        logging.info('********** Finding upper bound m/z - Window in spectralFile containing fragments **********')
        logging.info('m/z\tpeaks')
        while True:#currentMz < 2500:
            currentWindow = self.getPeaksInWindow(peaksHigherThanNoise, currentMz, windowSize)
            numPeaks = np.sum(currentWindow[:, 1])
            #logging.info(str(currentMz)+'\t'+ str(numPeaks))
            logging.info(str(currentMz)+'\t'+ str(numPeaks))
            #print(currentMz, numPeaks)
            if numPeaks < 5:
                currentMz += configs['upperBoundTolerance']
                break
            elif numPeaks < 10:
                currentMz += 2* configs['upperBoundTolerance']
                break
            currentMz += windowSize / 2

        logging.info('Final upper m/z limit: '+ str(currentMz))
        self._upperBound = currentMz
        return currentMz

    def calculateNoise(self, point, windowSize, currentWindow=None):
        '''
        Calculates the noise within a certain window in the spectrum
        Noise is calculated by averaging the lowest peaks within window multiplied by a factor (0.67).
        Lowest peaks are filtered by iteratively filtering out peaks with intensities higher than average+tolerance
        If the number of peaks is below a threshold, the user indicated noise level is used
        :param (float) point: m/z (median)
        :param (float) windowSize: window: [point-windowSize/2, point+windowSize/2]
        :param (ndarray(dtype=float, ndim=2) | None) currentWindow: peaks within window
        :return: (float) noise
        '''
        noise = self._settings['noiseLimit']
        if currentWindow is None:
            currentWindow = self.getPeaksInWindow(self._spectrum, point, windowSize)
        if currentWindow[:, 1].size < 11:
            currentWindow = self.getPeaksInWindow(self._spectrum, point, windowSize * 2)
        if currentWindow[:,1].size > 10:     #parameter
            peakInt = currentWindow[:, 1]
            avPeakInt = np.average(peakInt)
            #stdDevPeakInt = np.std(peakInt)
            while True:
                avPeakInt0 = avPeakInt
                lowAbundendantPeaks = peakInt[np.where(peakInt < (avPeakInt +noise))]# 2* 10**6))]#2 * stdDevPeakInt))] #ToDo parameter
                avPeakInt = np.average(lowAbundendantPeaks)
                if (len(lowAbundendantPeaks) == 1) or (avPeakInt - avPeakInt0 == 0):
                    #print(avPeakInt,stdDevPeakInt)
                    #print('exit 1')
                    #return avPeakInt * 0.67
                    break
                '''if avPeakInt - avPeakInt0 == 0:
                    #print('exit 2')
                    break'''
                #else:
                    #stdDevPeakInt = np.std(lowAbundendantPeaks)
            avPeakInt *= 0.6
            if avPeakInt > noise:#*0.67:
                noise = avPeakInt
            #print(avPeakInt,stdDevPeakInt)
        return noise

    @staticmethod
    def getPeaksInWindow(allPeaks, point, windowSize):
        '''
        Returns all peaks within a given m/z window
        :param (ndarray(dtype=float, ndim=2)) allPeaks: spectral peaks
        :param (float) point: m/z (median)
        :param (float) windowSize: window: [point-windowSize/2, point+windowSize/2]
        :return: (ndarray(dtype=float, ndim=2)) peaks within window
        '''
        spectralWindowIndex = np.where(abs(allPeaks[:, 0] - point) < (windowSize / 2))
        return allPeaks[spectralWindowIndex]


    def getNormalizationFactor(self):
        pass


    def findIon(self, neutral, zRange):
        '''
        Assigns peaks in spectrum to isotope peaks of corresponding ion
        1. Possible charges of species are calculated
        2. Search for n highest isotope peaks in spectrum: n either 1, 2 or 3 (see Fragment.getNumberOfHighestIsotopes)
        3. If found noise is calculated and the isotope peaks which could theoretically be above the noise are calculated:
            Programm searches for these peaks in spectrum
            If all isotope peaks are calculated to be below noise threshold, ion is added to deleted ion (comment = noise)
        :param (list) fragmentLibrary: list of Fragment-objects
        '''
        '''np.set_printoptions(suppress=True)
        precModCharge = self.getModCharge(self._precursor)
        self._normalizationFactor = self.getNormalizationFactor()
        logging.debug('Normalisation factor: '+ str(self._normalizationFactor))
        self.getProtonIsotopePatterns()
        for fragment in fragmentLibrary:
        formula =neutral.getFormula()
        neutralPatternFFT = formula.calculateIsotopePatternFFT(1, )
        zRange = self.getChargeRange(neutral, precModCharge)'''
        logging.info(neutral.getName())
        self._searchedChargeStates[neutral.getName()] = []
        sortedPattern = np.sort(neutral.getIsotopePattern(), order='calcInt')[::-1]
        peakQuantity = neutral.getNumberOfHighestIsotopes()
        logging.debug('* Nr of main peaks:'+str(peakQuantity))
        radicals = neutral.getRadicals()
        for z in zRange:
            logging.debug('* z'+str(z))
            theoreticalPeaks = copy.deepcopy(sortedPattern)
            theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * self._sprayMode, radicals)
            theoreticalPeaks = self.getChargedIsotopePattern(sortedPattern, z, radicals)
            if (configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < self._upperBound):
                self._searchedChargeStates[neutral.getName()].append(z)
                #make a guess of the ion abundance based on number in range
                sumInt = 0
                sumIntTheo = 0
                foundMainPeaks = list()
                logging.debug('* Main Peaks:')
                notFound = 0
                for i in range(peakQuantity):
                    spectralPeak = self.findPeak(theoreticalPeaks[i])
                    if spectralPeak[1]==0:
                        notFound+=1
                    sumInt += spectralPeak[1]
                    foundMainPeaks.append(spectralPeak)
                    sumIntTheo += theoreticalPeaks[i]['calcInt']
                    logging.debug(str(spectralPeak[0])+'\t'+str(spectralPeak[1])+'\t'+str(spectralPeak[2])+'\t'+
                                  str(spectralPeak[3]))
                if sumInt > 0:
                    #theoreticalPeaks=self.getChargedIsotopePattern2(formula, theoreticalPeaks, z-radicals)
                    noise = self.calculateNoise(theoreticalPeaks[0]['m/z'], configs['noiseWindowSize'])
                    logging.debug('Noise:'+str(noise))
                    sumInt += notFound * noise * 0.5              #if one or more isotope peaks were not found noise added #parameter
                    notInNoise = np.where(theoreticalPeaks['calcInt'] >noise*
                                          configs['thresholdFactor'] / (sumInt/sumIntTheo))
                    if theoreticalPeaks[notInNoise].size > peakQuantity:
                        logging.debug('* All Peaks:')
                        foundPeaks = [self.findPeak(theoPeak, configs['errorTolerance']) for theoPeak in theoreticalPeaks[notInNoise]]
                        #find other isotope Peaks
                        foundPeaksArr = np.sort(np.array(foundPeaks, dtype=self._peaksArrType), order=['m/z'])
                        if not np.all(foundPeaksArr['relAb']==0):
                            self._foundIons.append(self._IonClass(neutral, np.min(theoreticalPeaks['m/z']), z, foundPeaksArr, noise))
                            [print("\t",np.around(peak['m/z'],4),"\t",peak['relAb']) for peak in foundPeaksArr if peak['relAb']>0]
                            [logging.info(neutral.getName()+"\t"+str(z)+"\t"+str(np.around(peak['m/z'],4))+"\t"+str(peak['relAb']) )for peak in foundPeaksArr if peak['relAb']>0]
                        else:
                            self.addToDeletedIons(neutral, foundMainPeaks, noise, np.min(theoreticalPeaks['m/z']), z)
                    elif theoreticalPeaks[notInNoise].size > 0:
                        foundMainPeaksArr = np.sort(np.array(foundMainPeaks, dtype=self._peaksArrType), order=['m/z'])
                        self._foundIons.append(self._IonClass(neutral, np.min(theoreticalPeaks['m/z']), z,
                                                           foundMainPeaksArr, noise))
                        [print("\t",np.around(peak['m/z'],4),"\t",peak['relAb']) for peak in foundMainPeaksArr if peak['relAb']>0]
                        [logging.info(neutral.getName()+"\t"+str(z)+"\t"+str(np.around(peak['m/z'], 4)) + "\t" +
                                      str(peak['relAb'])) for peak in foundMainPeaksArr if peak['relAb'] > 0]
                    else:
                        print('deleting: '+neutral.getName()+", "+str(z))
                        self.addToDeletedIons(neutral, foundMainPeaks, noise, np.min(theoreticalPeaks['m/z']), z)


    def getProtonIsotopePatterns(self):
        '''
        Calculates the isotope patterns (rel.abundances) of various numbers of protons
        :return: (ndArray[float,float]) array with 2 columns: rows represent proton nr + 1, column 1: monoisotopic,
            column 2: M+1 peak
        '''
        maxZ = abs(self._settings['charge'])+1
        protonIsotopePatterns = np.zeros((maxZ,2))
        for i in range(maxZ):
            protonIsotopePatterns[i] = MolecularFormula({'H':i+1}).calcIsotopePatternPart(2)['calcInt']
            logging.debug(str(protonIsotopePatterns[i][0])+'\t'+str(protonIsotopePatterns[i][1]))
        self._protonIsoPatterns = protonIsotopePatterns

    def getChargedIsotopePattern(self, neutralPattern, z, radicals):
        '''
        Calculates the final theoretical isotope pattern of an ion
        :param (ndArray) neutralPattern: isotope pattern of the neutral species,
                structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param (int) z: charge of the ion
        :param (int) radicals: nr of radicals of the ion
        :return: (ndArray) isotope pattern of the ion,
                structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        '''
        theoreticalPeaks = copy.deepcopy(neutralPattern)
        theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * self._sprayMode, radicals)
        theoreticalPeaks['calcInt'][0] *= self._protonIsoPatterns[z-1][0] ** self._sprayMode
        if self._sprayMode == 1:
            regressionVals = neutralPattern['calcInt']
        else:
            regressionVals = theoreticalPeaks['calcInt']
        for i in range(1,len(theoreticalPeaks)):
            theoreticalPeaks['calcInt'][i] += self._protonIsoPatterns[z-1][1]*regressionVals[i-1]*self._sprayMode
        theoreticalPeaks['calcInt'] /= np.sum(theoreticalPeaks['calcInt'])
        return theoreticalPeaks

    def getChargedIsotopePattern2(self, formula, neutralPattern, nrHs):#, neutralFFT):
        sortedNeutralPattern = np.sort(neutralPattern, order='m/z')
        if self._sprayMode:
            #print('old',neutralPattern[0])
            ionPatternFFT = formula.addFormula({'H': nrHs}).calculateIsotopePatternFFT(2,neutralPattern) #Warum besser mit neutral???
        else:
            ionPatternFFT = formula.subtractFormula({'H': nrHs}).calculateIsotopePatternFFT(2,neutralPattern)
        ionPattern = sortedNeutralPattern
        maxIndexArr = np.array((len(ionPattern),len(ionPatternFFT)))
        maxIndex = np.min(maxIndexArr)
        if np.max(maxIndexArr) == np.min(maxIndexArr):
            #ionPattern['calcInt'] += (ionPatternFFT['calcInt']-neutralFFT['calcInt'])
            ionPattern['calcInt'] = ionPatternFFT['calcInt']
        else:
            #print('maxIndex',maxIndex,maxIndexArr)
            #ionPattern['calcInt'][:maxIndex] += (ionPatternFFT['calcInt'][:maxIndex]-neutralFFT['calcInt'][:maxIndex])
            ionPattern['calcInt'][:maxIndex] = ionPatternFFT['calcInt'][:maxIndex]
        ionPattern['calcInt'] /= np.sum(ionPattern['calcInt'])
        return ionPattern#np.sort(ionPattern, order='calcInt')[::-1]


    def findPeak(self, theoPeak, tolerance=0):
        searchMask = np.where(abs(calculateError(self._spectrum[:, 0], theoPeak['m/z']))
                              < getErrorLimit(self._spectrum[:, 0])+tolerance)
        return self.getCorrectPeak(self._spectrum[searchMask], theoPeak)



    def addToDeletedIons(self, fragment, foundMainPeaks, noise, monoisotopic, z):
        '''
        Adds an ion to deleted ions (_ionsInNoise), (comment "noise")
        :param fragment: fragment where one charge state should be deleted
        :type fragment: Fragment
        :param (list of tuples) foundMainPeaks: isotope peaks which could be assigned to ion
        :param (int) noise: calculated noise
        :param (float) monoisotopic: theoretical m/z of monoisotopic peak
        :param (int) z: charge of ion
        '''
        foundMainPeaksArr = np.sort(np.array(foundMainPeaks, dtype=self._peaksArrType), order=['m/z'])
        noiseIon = self._IonClass(fragment, monoisotopic, z, foundMainPeaksArr, noise)
        noiseIon.addComment('noise')
        self._ionsInNoise.append(noiseIon)

    def getCorrectPeak(self, foundIsotopePeaks, theoPeak):
        '''
        Selects the correct peak in spectrum for a theoretical isotope peak
        Correct is the peak with the lowest ppm error
        :param (ndArray (dtype=float)) foundIsotopePeaks:
        :param (ndArray (dtype=[float,float]) theoPeak: calculated peak (structured array [m/z,calcInt])
        :return: (Tuple[float, int, float, float, bool]) m/z, z, int, error, used
        '''
        if len(foundIsotopePeaks) == 0:
            return (theoPeak['m/z'], 0, theoPeak['calcInt'], 0, True)  # passt mir noch nicht
        elif len(foundIsotopePeaks) == 1:
            return (foundIsotopePeaks[0][0], foundIsotopePeaks[0][1], theoPeak['calcInt'],
                    calculateError(foundIsotopePeaks[0][0], theoPeak['m/z']), True)
        else:
            lowestError = 100
            logging.debug('More than one peak found: '+str(len(foundIsotopePeaks)))
            for peak in foundIsotopePeaks: #ToDo
                logging.debug(str(peak[0]), str(peak[1]))
                error = calculateError(peak[0], theoPeak[0])
                if abs(error) < abs(lowestError):
                    lowestError = error
                    lowestErrorPeak = peak
            logging.debug('Selected Peak: '+'\t'+str(lowestErrorPeak[0])+'\t'+ str(lowestErrorPeak[1])+'\t'+
                          str(theoPeak['calcInt'])+'\t'+str(lowestError))
            return (lowestErrorPeak[0], lowestErrorPeak[1], theoPeak['calcInt'], lowestError, True)


class SpectrumHandler(AbstractSpectrumHandler):
    '''
    Reads a top-down spectrum (peak list), calculates noise and finds peaks in the spectrum
    '''
    #ToDo:
    basicAA = {'H': 3, 'R': 10, 'K': 10,
               'D': 0.5, 'E': 0.5}
    acidicAA = {'D': 10, 'E': 10,
                'H': 0.9, 'R': 0.5, 'K': 0.5, }

    def __init__(self, properties, precursor, settings, peaks=None):
        '''
        Constructor, also processes spectrum
        :param properties: propertyStorage of search
        :type properties: SearchSettings
        :param precursor: precursor Fragment
        :type precursor: Fragment
        :param (dict[str,Any]) settings: search settings
        :param (set[tuple[float]] | None) peaks: set of peak tuples (m/z, I)
        '''
        sprayMode = 1
        if settings['charge'] < 0:
            sprayMode = -1
        super(SpectrumHandler, self).__init__(settings, sprayMode, FragmentIon, peaks)
        self._sequList = properties.getSequenceList()
        self._properties = properties
        '''
        self._settings = settings
        self._sprayMode = 1
        if self._settings['charge'] < 0:
            self._sprayMode = -1
        self._upperBound=0'''
        '''self._normalizationFactor = None'''
        self._precursor = precursor
        self._charge = self.calcPrecCharge(self._settings['charge'], self._precursor.getRadicals())


    def calcPrecCharge(self, charge, radicals):
        return abs(charge) - radicals #must be changed if radicals turns to electrons

    def setNormalizationFactor(self, factor):
        self._normalizationFactor = factor

    '''def getSprayMode(self):
        return self._sprayMode'''

    """def getSpectrum(self, *args):
        '''
        Returns either full or part of spectrum (peak list)
        :param (tuple of float) args: if args (lowerbound, upperbound), just part of the spectrum is returned
        :return: (ndarray(dtype=float, ndim=2)) spectrum
        '''
        if args and args[1]:
            return self._spectrum[np.where((self._spectrum[:, 0] > args[0]) & (self._spectrum[:, 0] < args[1]))]
        return self._spectrum

    def setSpectrum(self, spectrum):
        self._spectrum = spectrum

    def getUpperBound(self):
        return self._upperBound

    def getFoundIons(self):
        return self._foundIons

    def getIonsInNoise(self):
        return self._ionsInNoise

    def getSearchedChargeStates(self):
        return self._searchedChargeStates

    def emptyLists(self):
        self._foundIons = None
        self._ionsInNoise = None

    def addSpectrum(self,filePath):
        '''
        Add spectrum from file
        :param (str) filePath: path of txt or csv file
        '''
        with open(filePath, mode='r', encoding='utf_8_sig') as f:
            if filePath[-4:] == '.csv':
                self._spectrum = self.addSpectrumFromCsv(f)
            else:
                self._spectrum = self.addSpectrumFromTxt(f)
        self.resizeSpectrum()

    def addSpectrumFromCsv(self, file):
        '''
        :param file: opended csv-file
        :return: (ndarray(dtype=float, ndim=2)) [(m/z, int)]
        '''
        #skip = 0
        #lines = file.readlines()
        '''print(lines)
        if 'm/z' in lines[0]:
            skip = 1
        else:
            print(lines[0])
            raw = lines[0].split(',')
            print(raw)
            toAdd = np.empty(2,dtype=float)
            toAdd[0] = float(raw[0].encode('utf-8-sig').decode('utf-8-sig'))
            toAdd[1] = float(raw[1][:-2])
            print('dsf',toAdd)'''
        try:
            #print(np.loadtxt(lines[1:], delimiter=',', skiprows=1, usecols=[0, 1]))
            #return np.loadtxt(lines, delimiter=',', skiprows=skip, usecols=[0, 2])
            return np.loadtxt(file, delimiter=',', skiprows=1, usecols=[0, 1])
        except IndexError:
            #return np.loadtxt(lines, delimiter=';', skiprows=skip, usecols=[0, 2])
            return np.loadtxt(file, delimiter=';', skiprows=1, usecols=[0, 1])
        except ValueError:
            raise InvalidInputException('Incorrect Format of spectral data', '\nThe format must be "m/z,int" or "m/z;int"')

    def addSpectrumFromTxt(self, file):
        '''
        :param file: opended txt-file
        :return: (ndarray(dtype=float, ndim=2)) [(m/z, int)]
        '''
        spectralList = list()
        for i,line in enumerate(file):
            if line.startswith("m/z"):
                continue
            line = line.rstrip().split()
            if len(line)>1:
                try:
                    spectralList.append((float(line[0]),float(line[1])))
                except ValueError:
                    try:
                        call(['open', self._settings['spectralData']])
                    except:
                        pass
                    raise InvalidInputException('Problem with format in spectral data', '  '.join(line) + ' (line ' + str(i) +
                                                ') Format must be  "m/z    Int." !')
        return np.array(spectralList)

    def resizeSpectrum(self):
        '''
        Truncates spectrum
        '''
        self._spectrum = self._spectrum[np.where(self._spectrum[:, 0] < (self.findUpperBound() + 10))]
        print("\nmax m/z:", self._upperBound)"""

    """@staticmethod
    def getMz(mass, z, radicals):
        '''
        Calculates m/z
        :param (float) mass:
        :param (int) z:
        :param (int) radicals:
        :return: (float) m/z
        '''
        if z != 0:
            return abs(mass/z + protMass) + radicals*(eMass + protMass)/z
        else:
            return abs(mass) + radicals*(eMass + protMass)"""


    """def findUpperBound(self):
        '''
        Finds the highest m/z in spectrum where non-noise peaks occur
        :return: (int) m/z (upperBound)
        '''
        print("\n********** Finding upper bound m/z - Window in spectralFile containing fragments ********** ")
        windowSize = configs['upperBoundWindowSize']
        currentMz = configs['minUpperBound']
        #tolerance = 50

        peaksHigherThanNoise = list()
        logging.debug('********** Calculating noise **********\nm/z\tnoise')
        while currentMz < np.max(self._spectrum[:,0]):#2500:
            currentWindow = self.getPeaksInWindow(self._spectrum, currentMz, windowSize)
            noise = self.calculateNoise(currentMz,windowSize,currentWindow)
            logging.debug(str(currentMz)+'\t'+ str(noise))
            #currentWindow = self.getPeaksInWindow(self._spectrum, currentMz, windowSize)
            peaksHigherThanNoise.append((currentMz, currentWindow[np.where(currentWindow > (noise * 5))].size))
            currentMz += 1
        peaksHigherThanNoise = np.array(peaksHigherThanNoise)
        windowSize, currentMz = 100 , configs['minUpperBound']
        logging.info('********** Finding upper bound m/z - Window in spectralFile containing fragments **********')
        logging.info('m/z\tpeaks')
        while True:#currentMz < 2500:
            currentWindow = self.getPeaksInWindow(peaksHigherThanNoise, currentMz, windowSize)
            numPeaks = np.sum(currentWindow[:, 1])
            #logging.info(str(currentMz)+'\t'+ str(numPeaks))
            logging.info(str(currentMz)+'\t'+ str(numPeaks))
            #print(currentMz, numPeaks)
            if numPeaks < 5:
                currentMz += configs['upperBoundTolerance']
                break
            elif numPeaks < 10:
                currentMz += 2* configs['upperBoundTolerance']
                break
            currentMz += windowSize / 2

        logging.info('Final upper m/z limit: '+ str(currentMz))
        self._upperBound = currentMz
        return currentMz

    def calculateNoise(self, point, windowSize, currentWindow=None):
        '''
        Calculates the noise within a certain window in the spectrum
        Noise is calculated by averaging the lowest peaks within window multiplied by a factor (0.67).
        Lowest peaks are filtered by iteratively filtering out peaks with intensities higher than average+tolerance
        If the number of peaks is below a threshold, the user indicated noise level is used
        :param (float) point: m/z (median)
        :param (float) windowSize: window: [point-windowSize/2, point+windowSize/2]
        :param (ndarray(dtype=float, ndim=2) | None) currentWindow: peaks within window
        :return: (float) noise
        '''
        noise = self._settings['noiseLimit']
        if currentWindow is None:
            currentWindow = self.getPeaksInWindow(self._spectrum, point, windowSize)
        if currentWindow[:, 1].size < 11:
            currentWindow = self.getPeaksInWindow(self._spectrum, point, windowSize * 2)
        if currentWindow[:,1].size > 10:     #parameter
            peakInt = currentWindow[:, 1]
            avPeakInt = np.average(peakInt)
            #stdDevPeakInt = np.std(peakInt)
            while True:
                avPeakInt0 = avPeakInt
                lowAbundendantPeaks = peakInt[np.where(peakInt < (avPeakInt +noise))]# 2* 10**6))]#2 * stdDevPeakInt))] #ToDo parameter
                avPeakInt = np.average(lowAbundendantPeaks)
                if (len(lowAbundendantPeaks) == 1) or (avPeakInt - avPeakInt0 == 0):
                    #print(avPeakInt,stdDevPeakInt)
                    #print('exit 1')
                    #return avPeakInt * 0.67
                    break
                '''if avPeakInt - avPeakInt0 == 0:
                    #print('exit 2')
                    break'''
                #else:
                    #stdDevPeakInt = np.std(lowAbundendantPeaks)
            avPeakInt *= 0.6
            if avPeakInt > noise:#*0.67:
                noise = avPeakInt
            #print(avPeakInt,stdDevPeakInt)
        return noise

    @staticmethod
    def getPeaksInWindow(allPeaks, point, windowSize):
        '''
        Returns all peaks within a given m/z window
        :param (ndarray(dtype=float, ndim=2)) allPeaks: spectral peaks
        :param (float) point: m/z (median)
        :param (float) windowSize: window: [point-windowSize/2, point+windowSize/2]
        :return: (ndarray(dtype=float, ndim=2)) peaks within window
        '''
        spectralWindowIndex = np.where(abs(allPeaks[:, 0] - point) < (windowSize / 2))
        return allPeaks[spectralWindowIndex]"""


    '''@staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6'''

    def getNormalizationFactor(self):
        '''
        Calculates factor to normalise charge to number of precursor charges
        :return: (float) normalisation factor
        '''
        molecule = self._properties.getMolecule().getName()
        if molecule in ['RNA', 'DNA'] and self._sprayMode == -1:
            return self._charge / self._precursor.getFormula().getFormulaDict()['P']
            #return self._charge / len(self._sequList)
        #elif molecule == 'Protein' and self._sprayMode == 1:
         #   return self._charge / self.getChargeScore(self._sequList)
        #elif molecule in ['RNA', 'DNA'] and self._sprayMode == 1:
        #    return self._charge / len(self._sequList)
        else:
            return self._charge  / len(self._sequList)#self.getChargeScore(self._sequList)

    def getChargeScore(self, fragment): #ToDo: For proteins, currently not use
        chargeDict = self._properties.getGPBsOfBBs(self._sprayMode)
        score = 0
        """if self._properties.getFragmentation()[fragment.type].getDirection() == 1 and self._sprayMode== 1:
            score ="""
        #if self._sprayMode == 1:
        for bb in fragment.sequenceList:
            score += exp(self._sprayMode*chargeDict[bb]/(R*298))
        return score

    def getModCharge(self, fragment):
        '''
        Calculates the charge altering effect by the modification of a fragment
        :param fragment: concerning fragment
        :type fragment: Fragment
        :return: (float) charge shift
        '''
        modCharge = 0
        for mod, charge in self._properties.getChargedModifications().items():
            if mod[1:] in fragment.getModification():
                nrMod = 1
                if len(findall(r"(\d+)"+mod, fragment.getModification())) > 0:
                    nrMod = int(findall(r"(\d+)"+mod, fragment.getModification())[0])
                modCharge += charge * nrMod# * self._sprayMode
        logging.debug('Charge of modification: '+ str(modCharge))
        return modCharge

    #ToDo: Test SearchParameters, Proteins!, Parameters
    def getChargeRange(self, fragment, precModCharge):
        '''
        Calculates the most probable charge (z) for a given fragment and returns a range of this z +/- a tolerance
        The charge is calculated using the number of phosphates (RNA/DNA) or using the length of the sequence (proteins)
        :param fragment: corresponding fragment
        :type fragment: Fragment
        :param (float) precModCharge: charge effect of precursor modification
        :return: (generator) range between lowest possible z and highest possible z
        '''
        molecule = self._properties.getMolecule().getName()
        if molecule in ['RNA' ,'DNA'] and self._sprayMode == -1:
            #probableZ = (fragment.number-1) * self._normalizationFactor
            formula = fragment.getFormula().getFormulaDict()
            if ('P' not in formula.keys()) or (fragment.getFormula().getFormulaDict()['P'] == 0):
                return range(0,0)
            probableZ = fragment.getFormula().getFormulaDict()['P']* self._normalizationFactor
            #probableZ = fragment.formula.formulaDict['P'] * self._normalizationFactor
        elif molecule == 'Protein':
            #probableZ = self.getChargeScore(fragment) * self._normalizationFactor
            probableZ = len(fragment.getSequence()) * self._normalizationFactor
        elif molecule in ['RNA' ,'DNA'] and self._sprayMode == 1:
            probableZ = len(fragment.getSequence()) * self._normalizationFactor
        else:
            probableZ = len(fragment.getSequence()) * self._normalizationFactor
        probableZ -= fragment.getRadicals()
        tolerance = configs['zTolerance']
        lowZ, highZ = 1, self._charge
        zEffect = (self.getModCharge(fragment)-precModCharge) * self._sprayMode
        #print(1,fragment.getName(),probableZ)
        probableZ += zEffect
        #print(2,fragment.getName(),probableZ)
        if (probableZ-tolerance)> lowZ:
            lowZ = round(probableZ-tolerance)
        if (probableZ+tolerance)< highZ:
            highZ = round(probableZ + tolerance)
        #print(fragment.getName(),lowZ,round(probableZ,2),highZ)
        logging.info(fragment.getName()+'\tmin z: '+str(lowZ)+'\tcalc. z: '+str(round(probableZ,2))+'\tmax z: '+str(highZ))
        return range(lowZ,highZ+1)


    def findIons(self, fragmentLibrary):
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
        precModCharge = self.getModCharge(self._precursor)
        self._normalizationFactor = self.getNormalizationFactor()
        logging.debug('Normalisation factor: '+ str(self._normalizationFactor))
        self.getProtonIsotopePatterns()
        for fragment in fragmentLibrary:
            #neutralPatternFFT = formula.calculateIsotopePatternFFT(1, )
            logging.info(fragment.getName())
            self._searchedChargeStates[fragment.getName()] = []
            zRange = self.getChargeRange(fragment, precModCharge)
            self.findIon(fragment, zRange)

            '''sortedPattern = np.sort(fragment.getIsotopePattern(), order='calcInt')[::-1]
            peakQuantitiy = fragment.getNumberOfHighestIsotopes()
            logging.debug('* Nr of main peaks:'+str(peakQuantitiy))
            radicals = fragment.getRadicals()
            for z in zRange:
                print('old',z)
                logging.debug('* z'+str(z))
                theoreticalPeaks = copy.deepcopy(sortedPattern)
                theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * self._sprayMode, radicals)
                theoreticalPeaks = self.getChargedIsotopePattern(sortedPattern, z, radicals)
                if (configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < self._upperBound):
                    self._searchedChargeStates[fragment.getName()].append(z)
                    #make a guess of the ion abundance based on number in range
                    sumInt = 0
                    sumIntTheo = 0
                    foundMainPeaks = list()
                    logging.debug('* Main Peaks:')
                    notFound = 0
                    for i in range(peakQuantitiy):
                        spectralPeak = self.findPeak(theoreticalPeaks[i])
                        if spectralPeak[1]==0:
                            notFound+=1
                        sumInt += spectralPeak[1]
                        foundMainPeaks.append(spectralPeak)
                        sumIntTheo += theoreticalPeaks[i]['calcInt']
                        logging.debug(str(spectralPeak[0])+'\t'+str(spectralPeak[1])+'\t'+str(spectralPeak[2])+'\t'+
                                      str(spectralPeak[3]))
                    if sumInt > 0:
                        #theoreticalPeaks=self.getChargedIsotopePattern2(formula, theoreticalPeaks, z-radicals)
                        noise = self.calculateNoise(theoreticalPeaks[0]['m/z'], configs['noiseWindowSize'])
                        logging.debug('Noise:'+str(noise))
                        sumInt += notFound * noise * 0.5              #if one or more isotope peaks were not found noise added #parameter
                        notInNoise = np.where(theoreticalPeaks['calcInt'] >noise*
                                              configs['thresholdFactor'] / (sumInt/sumIntTheo))
                        if theoreticalPeaks[notInNoise].size > peakQuantitiy:
                            logging.debug('* All Peaks:')
                            foundPeaks = [self.findPeak(theoPeak, configs['errorTolerance']) for theoPeak in theoreticalPeaks[notInNoise]]
                            #find other isotope Peaks
                            foundPeaksArr = np.sort(np.array(foundPeaks, dtype=self._peaksArrType), order=['m/z'])
                            if not np.all(foundPeaksArr['relAb']==0):
                                self._foundIons.append(FragmentIon(fragment, np.min(theoreticalPeaks['m/z']), z, foundPeaksArr, noise))
                                [print("\t",np.around(peak['m/z'],4),"\t",peak['relAb']) for peak in foundPeaksArr if peak['relAb']>0]
                                [logging.info(fragment.getName()+"\t"+str(z)+"\t"+str(np.around(peak['m/z'],4))+"\t"+str(peak['relAb']) )for peak in foundPeaksArr if peak['relAb']>0]
                            else:
                                self.addToDeletedIons(fragment, foundMainPeaks, noise, np.min(theoreticalPeaks['m/z']), z)
                        elif theoreticalPeaks[notInNoise].size > 0:
                            foundMainPeaksArr = np.sort(np.array(foundMainPeaks, dtype=self._peaksArrType), order=['m/z'])
                            self._foundIons.append(FragmentIon(fragment, np.min(theoreticalPeaks['m/z']), z,
                                                               foundMainPeaksArr, noise))
                            [print("\t",np.around(peak['m/z'],4),"\t",peak['relAb']) for peak in foundMainPeaksArr if peak['relAb']>0]
                            [logging.info(fragment.getName()+"\t"+str(z)+"\t"+str(np.around(peak['m/z'], 4)) + "\t" +
                                          str(peak['relAb'])) for peak in foundMainPeaksArr if peak['relAb'] > 0]
                        else:
                            print('deleting: '+fragment.getName()+", "+str(z))
                            self.addToDeletedIons(fragment, foundMainPeaks, noise, np.min(theoreticalPeaks['m/z']), z)'''


    """def getProtonIsotopePatterns(self):
        '''
        Calculates the isotope patterns (rel.abundances) of various numbers of protons
        :return: (ndArray[float,float]) array with 2 columns: rows represent proton nr + 1, column 1: monoisotopic,
            column 2: M+1 peak
        '''
        maxZ = abs(self._settings['charge'])+1
        protonIsotopePatterns = np.zeros((maxZ,2))
        for i in range(maxZ):
            protonIsotopePatterns[i] = MolecularFormula({'H':i+1}).calcIsotopePatternPart(2)['calcInt']
            logging.debug(str(protonIsotopePatterns[i][0])+'\t'+str(protonIsotopePatterns[i][1]))
        self._protonIsoPatterns = protonIsotopePatterns

    def getChargedIsotopePattern(self, neutralPattern, z, radicals):
        '''
        Calculates the final theoretical isotope pattern of an ion
        :param (ndArray) neutralPattern: isotope pattern of the neutral species,
                structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param (int) z: charge of the ion
        :param (int) radicals: nr of radicals of the ion
        :return: (ndArray) isotope pattern of the ion,
                structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        '''
        theoreticalPeaks = copy.deepcopy(neutralPattern)
        theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * self._sprayMode, radicals)
        theoreticalPeaks['calcInt'][0] *= self._protonIsoPatterns[z-1][0] ** self._sprayMode
        if self._sprayMode == 1:
            regressionVals = neutralPattern['calcInt']
        else:
            regressionVals = theoreticalPeaks['calcInt']
        for i in range(1,len(theoreticalPeaks)):
            theoreticalPeaks['calcInt'][i] += self._protonIsoPatterns[z-1][1]*regressionVals[i-1]*self._sprayMode
        theoreticalPeaks['calcInt'] /= np.sum(theoreticalPeaks['calcInt'])
        return theoreticalPeaks

    def getChargedIsotopePattern2(self, formula, neutralPattern, nrHs):#, neutralFFT):
        sortedNeutralPattern = np.sort(neutralPattern, order='m/z')
        if self._sprayMode:
            #print('old',neutralPattern[0])
            ionPatternFFT = formula.addFormula({'H': nrHs}).calculateIsotopePatternFFT(2,neutralPattern) #Warum besser mit neutral???
        else:
            ionPatternFFT = formula.subtractFormula({'H': nrHs}).calculateIsotopePatternFFT(2,neutralPattern)
        ionPattern = sortedNeutralPattern
        maxIndexArr = np.array((len(ionPattern),len(ionPatternFFT)))
        maxIndex = np.min(maxIndexArr)
        if np.max(maxIndexArr) == np.min(maxIndexArr):
            #ionPattern['calcInt'] += (ionPatternFFT['calcInt']-neutralFFT['calcInt'])
            ionPattern['calcInt'] = ionPatternFFT['calcInt']
        else:
            #print('maxIndex',maxIndex,maxIndexArr)
            #ionPattern['calcInt'][:maxIndex] += (ionPatternFFT['calcInt'][:maxIndex]-neutralFFT['calcInt'][:maxIndex])
            ionPattern['calcInt'][:maxIndex] = ionPatternFFT['calcInt'][:maxIndex]
        ionPattern['calcInt'] /= np.sum(ionPattern['calcInt'])
        return ionPattern#np.sort(ionPattern, order='calcInt')[::-1]"""


    """def findPeak(self, theoPeak, tolerance=0):
        searchMask = np.where(abs(calculateError(self._spectrum[:, 0], theoPeak['m/z']))
                              < getErrorLimit(self._spectrum[:, 0])+tolerance)
        return self.getCorrectPeak(self._spectrum[searchMask], theoPeak)



    def addToDeletedIons(self, fragment, foundMainPeaks, noise, monoisotopic, z):
        '''
        Adds an ion to deleted ions (_ionsInNoise), (comment "noise")
        :param fragment: fragment where one charge state should be deleted
        :type fragment: Fragment
        :param (list of tuples) foundMainPeaks: isotope peaks which could be assigned to ion
        :param (int) noise: calculated noise
        :param (float) monoisotopic: theoretical m/z of monoisotopic peak
        :param (int) z: charge of ion
        '''
        foundMainPeaksArr = np.sort(np.array(foundMainPeaks, dtype=self._peaksArrType), order=['m/z'])
        noiseIon = FragmentIon(fragment, monoisotopic, z, foundMainPeaksArr, noise)
        noiseIon.addComment('noise')
        self._ionsInNoise.append(noiseIon)

    def getCorrectPeak(self, foundIsotopePeaks, theoPeak):
        '''
        Selects the correct peak in spectrum for a theoretical isotope peak
        Correct is the peak with the lowest ppm error
        :param (ndArray (dtype=float)) foundIsotopePeaks:
        :param (ndArray (dtype=[float,float]) theoPeak: calculated peak (structured array [m/z,calcInt])
        :return: (Tuple[float, int, float, float, bool]) m/z, z, int, error, used
        '''
        if len(foundIsotopePeaks) == 0:
            return (theoPeak['m/z'], 0, theoPeak['calcInt'], 0, True)  # passt mir noch nicht
        elif len(foundIsotopePeaks) == 1:
            return (foundIsotopePeaks[0][0], foundIsotopePeaks[0][1], theoPeak['calcInt'],
                    calculateError(foundIsotopePeaks[0][0], theoPeak['m/z']), True)
        else:
            lowestError = 100
            logging.debug('More than one peak found: '+str(len(foundIsotopePeaks)))
            for peak in foundIsotopePeaks: #ToDo
                logging.debug(str(peak[0]), str(peak[1]))
                error = calculateError(peak[0], theoPeak[0])
                if abs(error) < abs(lowestError):
                    lowestError = error
                    lowestErrorPeak = peak
            logging.debug('Selected Peak: '+'\t'+str(lowestErrorPeak[0])+'\t'+ str(lowestErrorPeak[1])+'\t'+
                          str(theoPeak['calcInt'])+'\t'+str(lowestError))
            return (lowestErrorPeak[0], lowestErrorPeak[1], theoPeak['calcInt'], lowestError, True)"""

    def setSearchedChargeStates(self, searchedZStates):
        self._searchedChargeStates = searchedZStates