'''
Created on 27 Jul 2020

@author: michael
'''
from os.path import join
from re import findall
import numpy as np
import copy

from src.data.Constants import E_MASS, P_MASS
from src.entities.Ions import FragmentIon
from src import path
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory

configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()

def getErrorLimit(mz):
    return configs['k']/1000 * mz + configs['d']

class SpectrumHandler(object):
    '''
    Reads spectra, calculates noise and finds peaks in __spectrum
    '''
    protonMass = 1.00727647
    eMass = 5.48579909065 * 10 ** (-4)
    #ToDo:
    basicAA = {'H': 3, 'R': 10, 'K': 10,
               'D': 0.5, 'E': 0.5}
    acidicAA = {'D': 10, 'E': 10,
                'H': 0.9, 'R': 0.5, 'K': 0.5, }

    def __init__(self, filePath, sequence, molecule, fragmentLibrary, precursor, chargedModifications, fragmentation, settings):
        '''
        Constructor
        :param molecule: RNA/DNA/P (String)
        :param sequence: sequential list of monomers
        :param fragmentLibrary: list of fragments from AbstractLibraryBuilder
        :param chargedModifications: output of getChargedModifications()-fct (AbstractLibraryBuilder): dict
        '''
        self.__sequence = sequence
        self.__molecule = molecule
        self.__fragmentLibrary = fragmentLibrary
        self.__chargedModifications = chargedModifications
        self.__fragTemplates = fragmentation
        self.__settings = settings
        self.__charge = abs(self.__settings['charge'])
        self.__sprayMode = 1
        if self.__settings['charge'] < 0:
            self.__sprayMode = -1
        #self.precMz = 0
        self.__upperBound=0
        #self.__spectrum=list()
        self.precursor = precursor
        #self.normalizationFactor = 1
        #self.normalizationFactor = 0
        self.normalizationFactor = None

        self.addSpectrum(filePath)
        self.foundIons = list()
        self.ionsInNoise = list()
        self.searchedChargeStates = dict()
        self.peaksArrType = np.dtype([('m/z', np.float64), ('relAb', np.float64),('m/z_theo', np.float64),
                             ('calcInt', np.float64), ('error', np.float32), ('used', np.bool_)])

    def getSpectrum(self, *args):
        if args and args[1]:
            return self.__spectrum[np.where((self.__spectrum[:, 0] > args[0]) & (self.__spectrum[:, 0] < args[1]))]
        return self.__spectrum

    def getUpperBound(self):
        return self.__upperBound


    def addSpectrum(self,filePath):
        with open(filePath, mode='r') as f:
            if filePath[-4:] == '.csv':
                self.__spectrum = self.addSpectrumFromCsv(f)
            else:
                self.__spectrum = self.addSpectrumFromTxt(f)
        self.resizeSpectrum()

    def addSpectrumFromCsv(self, file):
        try:
            return np.loadtxt(file, delimiter=',', skiprows=1, usecols=[0, 2])
        except IndexError:
            return np.loadtxt(file, delimiter=';', skiprows=1, usecols=[0, 2])

    def addSpectrumFromTxt(self, file):
        spectralList = list()
        for line in file:
            if line.startswith("m/z"):
                continue
            line = line.rstrip().split()
            if len(line)>1:
                spectralList.append((float(line[0]),float(line[1])))
        return np.array(spectralList)

    def resizeSpectrum(self):
        #self.precMz = self.getMz(self.precursor.formula.calculateMonoIsotopic(), self.__charge, self.precursor.radicals)
        self.__spectrum = self.__spectrum[np.where(self.__spectrum[:, 0] < (self.findUpperBound() + 10))]
        print("\nmax m/z:", self.__upperBound)

    def getMz(self, mass, z, radicals):
        #print(z ,mass/z + self.protonMass*self.mode)
        return mass/z + self.protonMass*self.__sprayMode + radicals*(E_MASS + P_MASS)


    def findUpperBound(self):
        print("\n********** Finding upper bound m/z - Window in spectralFile containing fragments ********** ")
        windowSize = configs['upperBoundWindowSize']
        currentMz = configs['minUpperBound']
        #tolerance = 50
        peaksHigherThanNoise = list()
        while currentMz < 2500:
            noise = self.calculateNoise(currentMz,windowSize)
            currentWindow = self.returnArrayInWindow(self.__spectrum, currentMz, windowSize)
            peaksHigherThanNoise.append((currentMz, currentWindow[np.where(currentWindow > (noise * 5))].size))
            currentMz += 1
        peaksHigherThanNoise = np.array(peaksHigherThanNoise)
        windowSize, currentMz = 100 , 1200
        while currentMz < 2500:
            currentWindow = self.returnArrayInWindow(peaksHigherThanNoise, currentMz, windowSize)
            sumInt = np.sum(currentWindow[:, 1])
            print(currentMz, sumInt)
            if sumInt < 5:
                currentMz += configs['upperBoundTolerance']
                break
            elif sumInt < 10:
                currentMz += 2* configs['upperBoundTolerance']
                break
            currentMz += windowSize / 2
        self.__upperBound = currentMz
        return currentMz

    def calculateNoise(self, point, windowSize):
        noise = self.__settings['noiseLimit']
        currentWindow = self.returnArrayInWindow(self.__spectrum, point, windowSize)
        if currentWindow[:, 1].size < 11:
            currentWindow = self.returnArrayInWindow(self.__spectrum, point, windowSize*2)
        if currentWindow[:,1].size > 10:     #parameter
            peakInt = currentWindow[:, 1]
            avPeakInt = np.average(peakInt)
            #stdDevPeakInt = np.std(peakInt)
            while True:
                avPeakInt0 = avPeakInt
                lowAbundendantPeaks = peakInt[np.where(peakInt < (avPeakInt + 2* 10**6))]#2 * stdDevPeakInt))]
                avPeakInt = np.average(lowAbundendantPeaks)
                if len(lowAbundendantPeaks) == 1:
                    #print(avPeakInt,stdDevPeakInt)
                    #print('exit 1')
                    return avPeakInt * 0.67
                if avPeakInt - avPeakInt0 == 0:
                    #print('exit 2')
                    break
                #else:
                    #stdDevPeakInt = np.std(lowAbundendantPeaks)
            if avPeakInt > noise*0.67:
                noise = avPeakInt
            #print(avPeakInt,stdDevPeakInt)
        return noise*0.6

    @staticmethod
    def returnArrayInWindow(array, point, windowSize):
        spectralWindowIndex = np.where(abs(array[:, 0] - point) < (windowSize / 2))
        return array[spectralWindowIndex]


    @staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6

    def getNormalizationFactor(self):
        molecule = self.__molecule.getName()
        if molecule in ['RNA', 'DNA'] and self.__sprayMode == -1:
            return self.__charge / self.precursor.formula.formulaDict['P']
        elif molecule == 'Protein':
            return self.__charge / self.getPeptideScore(self.__sequence)
        #elif molecule in ['RNA', 'DNA'] and self.__sprayMode == 1:
        #    return self.__charge / len(self.__sequence)
        else:
            return self.__charge / len(self.__sequence)

    def getPeptideScore(self, fragment): #ToDo
        if self.__sprayMode== -1:
                chargeDict = self.acidicAA
        else:
            chargeDict = self.basicAA
        score = 0
        """if self.__fragTemplates[fragment.type].getDirection() == 1 and self.__sprayMode== 1:
            score ="""
        for aa in fragment.sequenceList:
            if aa in chargeDict:
                score += chargeDict[aa]
            else:
                score += 1
        return score

    def getModCharge(self, fragment):
        modCharge = 0
        for mod, charge in self.__chargedModifications.items():
            if mod in fragment.modification:
                nrMod = 1
                if len(findall(r"(\d+)"+mod, fragment.modification)) > 0:
                    nrMod = int(findall(r"(\d+)"+mod, fragment.modification)[0])
                modCharge += charge * nrMod * self.__sprayMode
        return modCharge

    #ToDo: Test SearchParameters, Proteins!, Parameters
    def getSearchParameters(self, fragment,precModCharge):
        molecule = self.__molecule.getName()
        if molecule in ['RNA' ,'DNA'] and self.__sprayMode == -1:
            if fragment.formula.formulaDict['P'] == 0:
                return None
            probableZ = fragment.formula.formulaDict['P'] * self.normalizationFactor
        elif molecule == 'Protein':
            probableZ = self.getPeptideScore(fragment) * self.normalizationFactor
        elif molecule in ['RNA' ,'DNA'] and self.__sprayMode == 1:
            probableZ = fragment.number * self.normalizationFactor
        else:
            probableZ = fragment.number * self.normalizationFactor
        probableZ -= fragment.radicals
        tolerance = configs['zTolerance']
        lowZ, highZ = 1, self.__charge
        zEffect = (precModCharge - self.getModCharge(fragment)) * self.__sprayMode
        if (probableZ-tolerance + zEffect)> 1:
            lowZ = round(probableZ-tolerance + zEffect)
        if (probableZ+tolerance + precModCharge)< self.__charge:
            highZ = round(probableZ + tolerance + zEffect)
        print(fragment.getName(),lowZ,highZ)
        return range(lowZ,highZ+1)


    #ToDo: Refactor
    def findPeaks(self):
        """finds fragments and isotope distribution; parameters:
        low_limit  ... peaks with a lower m/z will be neglected
        high_limit ... peaks with a higher m/z will be neglected
        peakQuantitiy ... how many isotope peaks are used for basic calculation of pattern1 (highest peakQuantitiy used)"""
        np.set_printoptions(suppress=True)
        precModCharge = self.getModCharge(self.precursor)
        self.normalizationFactor = self.getNormalizationFactor()
        for fragment in self.__fragmentLibrary:
            self.searchedChargeStates[fragment.getName()] = []
            fragment.isotopePattern = np.sort(fragment.isotopePattern, order='calcInt')[::-1]
            zRange = self.getSearchParameters(fragment,precModCharge)
            peakQuantitiy = fragment.getNumberOfHighestIsotopes()
            if zRange == None:
                continue
            for z in zRange:
                print(fragment.getName(),z)
                theoreticalPeaks = copy.deepcopy(fragment.isotopePattern)
                #if self.__settings['dissociation'] in ['ECD', 'EDD', 'ETD'] and fragment.number == 0:
                #    theoreticalPeaks['mass'] += ((self.protonMass-self.eMass) * (self.__charge - z))
                    #print("heeeeee\n",fragment.getName(),z, theoreticalPeaks['mass'])
                theoreticalPeaks['m/z'] = self.getMz(theoreticalPeaks['m/z'], z, fragment.radicals)
                if (configs['lowerBound'] < theoreticalPeaks[0]['m/z'] < self.__upperBound):
                    self.searchedChargeStates[fragment.getName()].append(z)
                    #make a guess of the ion abundance based on number in range
                    sumInt = 0
                    sumIntTheo = 0
                    foundMainPeaks = list()
                    for i in range(peakQuantitiy):
                        searchMask = np.where(abs(self.calculateError(self.__spectrum[:, 0], theoreticalPeaks[i]['m/z']))
                                              < getErrorLimit(self.__spectrum[:, 0]))
                        spectralPeak = self.getCorrectPeak(self.__spectrum[searchMask], theoreticalPeaks[i])
                        sumInt += spectralPeak[1]
                        """if fragment.getName() == 'c16':
                            print('c16:',theoreticalPeaks[i]['m/z'])"""
                        foundMainPeaks.append(spectralPeak)
                        sumIntTheo += theoreticalPeaks[i]['calcInt']
                    """if fragment.getName() == 'c16':
                        print('c16:',sumInt)"""
                    if sumInt > 0:
                        noise = self.calculateNoise(theoreticalPeaks[0]['m/z'], 4)
                        #print('\twent through',round(noise))
                        sumInt += (peakQuantitiy - 1 - len(foundMainPeaks)) * noise * 0.5              #if one or more isotope peaks were not found noise added #parameter
                        notInNoise = np.where(theoreticalPeaks['calcInt'] >noise*
                                              configs['thresholdFactor'] / (sumInt/sumIntTheo))
                        '''inNoise = np.where(theoreticalPeaks['calcInt'] <= noise*
                                           configs['thresholdFactor'] / (sumInt/sumIntTheo))'''
                        if theoreticalPeaks[notInNoise].size != 0:
                            foundPeaks = list()
                            #find other isotope Peaks
                            for theoPeak in theoreticalPeaks[notInNoise]:
                                searchMask = np.where(abs(self.calculateError(self.__spectrum[:, 0], theoPeak['m/z']))
                                                      < (getErrorLimit(self.__spectrum[:, 0]) + configs['errorTolerance']))
                                foundPeaks.append(self.getCorrectPeak(self.__spectrum[searchMask], theoPeak))

                            """for theoPeak in theoreticalPeaks[inNoise]:
                                foundPeaks.append((theoPeak['m/z'],0,theoPeak['m/z'],theoPeak['calcInt'],0,1))"""
                            foundPeaksArr = np.sort(np.array(foundPeaks, dtype=self.peaksArrType),order=['m/z'])
                            if not np.all(foundPeaksArr['relAb']==0):
                                self.foundIons.append(FragmentIon(fragment, z, foundPeaksArr, noise))
                                #print(fragment.getName(),z,'\n', theoreticalPeaks[0]['m/z'], z, "{:.2e}".format(noise))
                                #print(fragment.getName(),foundPeaksArr)
                                for peak in foundPeaksArr:
                                    if peak['relAb']>0:
                                        print("\t",np.around(peak['m/z'],4),"\t",peak['relAb'])
                            else:
                                self.addToDeletedIons(fragment, foundMainPeaks, noise, z)
                        else:
                            """for theoPeak in theoreticalPeaks[inNoise]:
                                foundMainPeaks.append((theoPeak['m/z'],0,theoPeak['m/z'],theoPeak['relAb'],0,1))"""
                            self.addToDeletedIons(fragment, foundMainPeaks, noise, z)


    def addToDeletedIons(self, fragment, foundMainPeaks, noise, z):
        foundMainPeaksArr = np.sort(np.array(foundMainPeaks, dtype=self.peaksArrType), order=['m/z'])
        noiseIon = FragmentIon(fragment, z, foundMainPeaksArr, noise)
        noiseIon.comment = 'noise,'
        self.ionsInNoise.append(noiseIon)

    def getCorrectPeak(self, foundIsotopePeaks, theoPeak):
        if len(foundIsotopePeaks) == 0:
            return (theoPeak['m/z'], 0, theoPeak['m/z'], theoPeak['calcInt'], 0, True)  # passt mir noch nicht
        elif len(foundIsotopePeaks) == 1:
            return (foundIsotopePeaks[0][0], foundIsotopePeaks[0][1], theoPeak['m/z'], theoPeak['calcInt'],
                    self.calculateError(foundIsotopePeaks[0][0], theoPeak['m/z']), True)
        else:
            lowestError = 100
            for peak in foundIsotopePeaks:
                error = self.calculateError(peak[0], theoPeak[0])
                if abs(error) < abs(lowestError):
                    lowestError = error
                    lowestErrorPeak = peak
            return (lowestErrorPeak[0], lowestErrorPeak[1], theoPeak['m/z'], theoPeak['calcInt'], lowestError, True)
