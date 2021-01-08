'''
Created on 27 Jul 2020

@author: michael
'''
from os.path import join
from re import findall
import numpy as np
import copy
from src.FragmentHunter.Fragment import Ion
from src import path
from src.ConfigurationHandler import ConfigHandler

configs = ConfigHandler(join(path, "src","FragmentHunter","Repository","configurations.json")).getAll()

def getErrorLimit(mz):
    return configs['k']/1000 * mz + configs['d']

class SpectrumHandler(object):
    '''
    Reads spectra, calculates noise and finds peaks in spectrum
    '''
    protonMass = 1.00727647
    eMass = 5.48579909065 * 10 ** (-4)
    basicAA = {'H': 3, 'R': 10, 'K': 10,
               'D': 0.5, 'E': 0.5}
    acidicAA = {'D': 10, 'E': 10,
                'H': 0.9, 'R': 0.5, 'K': 0.5, }

    def __init__(self, molecule, sequence, fragmentLibrary, chargedModifications, settings):
        '''
        Constructor
        :param molecule: RNA/DNA/P (String)
        :param sequence: sequential list of monomers
        :param fragmentLibrary: list of fragments from AbstractLibraryBuilder
        :param chargedModifications: output of getChargedModifications()-fct (AbstractLibraryBuilder): dict
        '''
        self.molecule = molecule
        self.sequence = sequence
        self.fragmentLibrary = fragmentLibrary
        self.chargedModifications = chargedModifications
        self.settings = settings
        if self.settings['sprayMode'] == 'negative': #ToDo: change in parameterFile
            self.mode = -1
        elif self.settings['sprayMode'] == 'positive':
            self.mode = 1
        else:
            #ToDo Parameter Exception
            raise Exception("par")
        self.precMz = 0
        self.upperBound=0
        self.spectrum=0
        self.precursor = None
        self.spectrum = None
        self.normalizationFactor = 1
        self.normalizationFactor = 0
        self.foundIons = list()
        self.ionsInNoise = list()
        self.searchedChargeStates = dict()
        self.peaksArrType = np.dtype([('m/z', np.float64), ('int', np.float64),('m/z_theo', np.float64),
                             ('calcInt', np.float64), ('error', np.float32), ('used', np.uint8)])

    def addSpectrumFromCsv(self, file):
        #spectralList = list()
        try:
            self.spectrum = np.loadtxt(file, delimiter=',', skiprows=1, usecols=[0, 2])
        except IndexError:
            self.spectrum = np.loadtxt(file, delimiter=';', skiprows=1, usecols=[0, 2])
        self.resizeSpectrum()
        #print(self.spectralFile)
        #file = np.loadtxt(file, delimiter=',', skiprows=1, usecols=[0, 2])
        #highMz = np.where(file[:, 0] > self.maxMz)
        #self.spectralFile = file[0:highMz[0][0], :]
        #self.spectralFile = np.hstack((filteredFile, np.zeros((filteredFile.shape[0], 1), dtype=filteredFile.dtype)))


    def addSpectrum(self, file):
        spectralList = list()
        for line in file:
            if line.startswith("m/z"):
                continue
            line = line.rstrip().split()
            #if float(line[0]) < self.maxMz:
            spectralList.append((float(line[0]),float(line[1])))
            #print(line[0],line[2])
        self.spectrum = np.array(spectralList)
        self.resizeSpectrum()


    @staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6


    def findPrecursor(self):
        precursorMass = 0
        for fragment in self.fragmentLibrary:
            fragmentMass = fragment.formula.calculateMonoIsotopic()
            if fragmentMass > precursorMass:
                precursorMass = fragmentMass
                precursor = fragment
        self.precursor = precursor
        return precursor


    def getMz(self, mass, z):
        #print(z ,mass/z + self.protonMass*self.mode)
        return mass/z + self.protonMass*self.mode




    @staticmethod
    def returnArrayInWindow(array, point, windowSize):
        spectralWindowIndex = np.where(abs(array[:, 0] - point) < (windowSize / 2))
        return array[spectralWindowIndex]


    def calculateNoise(self, point, windowSize):
        noise = self.settings['noiseLimit']
        #spectralWindowIndex = np.where(abs(self.spectralFile[:, 0] - point) < (windowSize / 2))
        currentWindow = self.returnArrayInWindow(self.spectrum, point, windowSize)
        if currentWindow[:,1].size > 10:     #parameter
            peakInt = currentWindow[:, 1]
            avPeakInt = np.average(peakInt)
            #stdDevPeakInt = np.std(peakInt)
            while True:
                avPeakInt0 = avPeakInt
                lowAbundendantPeaks = peakInt[np.where(peakInt < (avPeakInt + 10**6))]#2 * stdDevPeakInt))]
                avPeakInt = np.average(lowAbundendantPeaks)
                if len(lowAbundendantPeaks) == 1:
                    #print(avPeakInt,stdDevPeakInt)
                    #print('exit 1')
                    return avPeakInt * 0.67
                if avPeakInt - avPeakInt0 == 0:
                    #print('exit 2')
                    break
                else:
                    stdDevPeakInt = np.std(lowAbundendantPeaks)
            if avPeakInt > noise*0.67:
                noise = avPeakInt
            #print(avPeakInt,stdDevPeakInt)
        return noise*0.6


    def findUpperBound(self):
        print("\n********** Finding upper bound m/z - Window in spectralFile containing fragments ********** ")
        windowSize = configs['upperBoundWindowSize']
        currentMz = configs['minUpperBound']
        #tolerance = 50
        peaksHigherThanNoise = list()
        while currentMz < 2500:
            noise = self.calculateNoise(currentMz,windowSize)
            currentWindow = self.returnArrayInWindow(self.spectrum, currentMz, windowSize)
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
        self.upperBound = currentMz
        return currentMz


    def resizeSpectrum(self):
        self.precMz = self.getMz(self.findPrecursor().formula.calculateMonoIsotopic(), self.settings['charge'])
        self.spectrum = self.spectrum[np.where(self.spectrum[:,0]<(self.findUpperBound()+10))]
        print("\nmax m/z:", self.upperBound)

    def getNormalizationFactor(self):
        if self.molecule in ['RNA', 'DNA'] and self.mode == -1:
            return self.settings['charge'] / self.precursor.formula.formulaDict['P']
        elif self.molecule == 'protein':
            return self.settings['charge'] / self.getPeptideScore(self.sequence)
        elif self.molecule in ['RNA', 'DNA'] and self.mode == 1:
            return self.settings['charge'] / len(self.sequence)

    def getPeptideScore(self, sequence):
        if self.mode== -1:
                chargeDict = self.acidicAA
        else:
            chargeDict = self.basicAA
        score = 0
        for aa in sequence:
            if aa in chargeDict:
                score += chargeDict[aa]
            else:
                score += 1
        return score

    def getModCharge(self, fragment):
        modCharge = 0
        for mod, charge in self.chargedModifications.items():
            if mod in fragment.modification:
                nrMod = 1
                if len(findall(r"(\d+)"+mod, fragment.modification)) > 0:
                    nrMod = int(findall(r"(\d+)"+mod, fragment.modification)[0])
                modCharge += charge * nrMod
        return modCharge

    #ToDo: Test SearchParameters, Proteins!, Parameters
    def getSearchParameters(self, fragment,precModCharge):
        if self.molecule in ['RNA' ,'DNA'] and self.mode == -1:
            if fragment.formula.formulaDict['P'] == 0:
                return None
            probableZ = fragment.formula.formulaDict['P'] * self.normalizationFactor
        elif self.molecule == 'protein':
            probableZ = self.getPeptideScore(fragment.sequence) * self.normalizationFactor
        elif self.molecule in ['RNA' ,'DNA'] and self.mode == 1:
            probableZ = fragment.number * self.normalizationFactor
        else:
            raise Exception('Unknown molecule:',self.molecule)
        tolerance = configs['zTolerance']
        lowZ, highZ = 1, self.settings['charge']
        zEffect = (precModCharge - self.getModCharge(fragment)) * self.mode
        if (probableZ-tolerance + zEffect)> 1:
            lowZ = round(probableZ-tolerance + zEffect)
        if (probableZ+tolerance + precModCharge)< self.settings['charge']:
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
        for fragment in self.fragmentLibrary:
            self.searchedChargeStates[fragment.getName()] = []
            fragment.isotopePattern = np.sort(fragment.isotopePattern, order='int')[::-1]
            zRange = self.getSearchParameters(fragment,precModCharge)
            peakQuantitiy = fragment.getNumberOfHighestIsotopes()
            if zRange == None:
                continue
            for z in zRange:
                print(fragment.getName(),z)
                theoreticalPeaks = copy.deepcopy(fragment.isotopePattern)
                if self.settings['dissociation'] in ['ECD','EDD','ETD'] and fragment.number == 0:
                    theoreticalPeaks['mass'] += ((self.protonMass-self.eMass) * (self.settings['charge'] - z))
                    #print("heeeeee\n",fragment.getName(),z, theoreticalPeaks['mass'])
                theoreticalPeaks['mass'] = self.getMz(theoreticalPeaks['mass'], z)
                if (configs['lowerBound'] < theoreticalPeaks[0]['mass'] < self.upperBound):
                    self.searchedChargeStates[fragment.getName()].append(z)
                    #make a guess of the ion abundance based on number in range
                    sumInt = 0
                    sumIntTheo = 0
                    foundMainPeaks = list()
                    for i in range(peakQuantitiy):
                        searchMask = np.where(abs(self.calculateError(self.spectrum[:, 0], theoreticalPeaks[i]['mass']))
                                              < getErrorLimit(self.spectrum[:, 0]))
                        spectralPeak = self.getCorrectPeak(self.spectrum[searchMask],theoreticalPeaks[i])
                        sumInt += spectralPeak[1]
                        """if fragment.getName() == 'c16':
                            print('c16:',theoreticalPeaks[i]['mass'])"""
                        foundMainPeaks.append(spectralPeak)
                        sumIntTheo += theoreticalPeaks[i]['int']
                    """if fragment.getName() == 'c16':
                        print('c16:',sumInt)"""
                    if sumInt > 0:
                        noise = self.calculateNoise(theoreticalPeaks[0]['mass'], 4)
                        #print('\twent through',round(noise))
                        sumInt += (peakQuantitiy - 1 - len(foundMainPeaks)) * noise * 0.5              #if one or more isotope peaks were not found noise added #parameter
                        notInNoise = np.where(theoreticalPeaks['int'] >noise*
                                              configs['thresholdFactor'] / (sumInt/sumIntTheo))
                        inNoise = np.where(theoreticalPeaks['int'] <= noise*
                                           configs['thresholdFactor'] / (sumInt/sumIntTheo))


                        if theoreticalPeaks[notInNoise].size != 0:
                            foundPeaks = list()
                            #find other isotope Peaks
                            for theoPeak in theoreticalPeaks[notInNoise]:
                                searchMask = np.where(abs(self.calculateError(self.spectrum[:, 0], theoPeak['mass']))
                                                      < (getErrorLimit(self.spectrum[:, 0]) + configs['errorTolerance']))
                                foundPeaks.append(self.getCorrectPeak(self.spectrum[searchMask], theoPeak))

                            """for theoPeak in theoreticalPeaks[inNoise]:
                                foundPeaks.append((theoPeak['mass'],0,theoPeak['mass'],theoPeak['int'],0,1))"""
                            foundPeaksArr = np.sort(np.array(foundPeaks, dtype=self.peaksArrType),order=['m/z'])
                            if not np.all(foundPeaksArr['int']==0):
                                self.foundIons.append(Ion(fragment,z,foundPeaksArr, noise))
                                #print(fragment.getName(),z,'\n', theoreticalPeaks[0]['mass'], z, "{:.2e}".format(noise))
                                #print(fragment.getName(),foundPeaksArr)
                                for peak in foundPeaksArr:
                                    if peak['int']>0:
                                        print("\t",np.around(peak['m/z'],4),"\t",peak['int'])
                            else:
                                self.addToDeletedIons(fragment, foundMainPeaks, noise, z)
                        else:
                            """for theoPeak in theoreticalPeaks[inNoise]:
                                foundMainPeaks.append((theoPeak['mass'],0,theoPeak['mass'],theoPeak['int'],0,1))"""
                            self.addToDeletedIons(fragment, foundMainPeaks, noise, z)


    def addToDeletedIons(self, fragment, foundMainPeaks, noise, z):
        foundMainPeaksArr = np.sort(np.array(foundMainPeaks, dtype=self.peaksArrType), order=['m/z'])
        noiseIon = Ion(fragment, z, foundMainPeaksArr, noise)
        noiseIon.comment = 'noise'
        self.ionsInNoise.append(noiseIon)

    def getCorrectPeak(self, foundIsotopePeaks, theoPeak):
        if len(foundIsotopePeaks) == 0:
            return (theoPeak['mass'], 0, theoPeak['mass'], theoPeak['int'], 0, 1)  # passt mir noch nicht
        elif len(foundIsotopePeaks) == 1:
            return (foundIsotopePeaks[0][0], foundIsotopePeaks[0][1], theoPeak['mass'], theoPeak['int'],
                    self.calculateError(foundIsotopePeaks[0][0], theoPeak['mass']), 1)
        else:
            lowestError = 100
            for peak in foundIsotopePeaks:
                error = self.calculateError(peak[0], theoPeak[0])
                if abs(error) < abs(lowestError):
                    lowestError = error
                    lowestErrorPeak = peak
            return (lowestErrorPeak[0], lowestErrorPeak[1], theoPeak['mass'], theoPeak['int'], lowestError, 1)