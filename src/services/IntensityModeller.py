'''
Created on 6 Aug 2020

@author: michael
'''
import logging
from math import exp
from re import findall
import numpy as np
from copy import deepcopy
from scipy.optimize import minimize, minimize_scalar

from src.services.assign_services.AbstractSpectrumHandler import getErrorLimit, calculateError, peaksArrType

logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename='logfile_IntensityModeller.log',level=logging.INFO)


def calcScore(intensity, quality, noiseLevel):
    if quality > 1.5:
        return 10 ** 6
    else:
        if noiseLevel != 0:
            return exp(10 * quality) / 20 * quality * intensity / noiseLevel
        else:
            print('Warning: noiseLevel = 0')
            return 0


class IntensityModeller(object):
    '''
    Class which models signal intensities (including ppm errors and qualities) and for storage of ion values
    '''
    def __init__(self, configurations, noiseLevel):
        '''
        :param (dict[str,Any]) configurations: configurations
        '''
        self._configs = configurations
        self._correctedIons = dict()
        self._deletedIons = dict()
        self._remodelledIons = list()
        self._monoisotopicList = list()
        self._noiseLevel = noiseLevel

    def getObservedIons(self):
        return self._correctedIons

    def getDeletedIons(self):
        return self._deletedIons

    def getRemodelledIons(self):
        return self._remodelledIons

    def addRemodelledIon(self, newIon, index):
        newIon.addComment('man.mod.')
        if index == 0:
            self._remodelledIons.append(self._correctedIons[newIon.getHash()])
            self._correctedIons[newIon.getHash()]= newIon
        else:
            self._remodelledIons.append(self._deletedIons[newIon.getHash()])
            self._deletedIons[newIon.getHash()]= newIon
        return newIon

    def addNewIon(self,ion):
        ion.addComment('new')
        ion.setScore(calcScore(ion.getIntensity(),ion.getQuality(),self._noiseLevel))
        newPattern = []
        for peak in ion.getIsotopePattern():
            row = [val for val in peak]
            newPattern.append(tuple(row[0:3]+[0.]+row[3:]))
        ion.setIsotopePattern(np.array(newPattern, dtype=peaksArrType))
        self._correctedIons[ion.getHash()] = ion

    def setMonoisotopicList(self, monoisotopicList):
        self._monoisotopicList = monoisotopicList

    '''@staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6'''

    '''@staticmethod
    def getHash(ion):
        return ion.getHash()'''


    @staticmethod
    def loss_1D_sum_square(x, spectralIntensities, theoIntensities):
        '''
        Sum of squares function for a linear 1D function
        :param (float) x: factor for theoIntensities (must be optimised - weight)
        :param (ndArray, dtype=float) spectralIntensities: intensities in spectrum
        :param (ndArray, dtype=float) theoIntensities: calculated intensities
        :return: (float) sum of squares
        '''
        '''sum_square = 0
        for spectralIntensity, theoIntensity in zip(spectralIntensities,theoIntensities):
            sum_square += (spectralIntensity-theoIntensity*x)**2
        return sum_square'''
        return np.sum(np.linalg.norm(spectralIntensities-theoIntensities*x)**2)


    def modelDistribution(self, spectralIntensities, theoInt, mzArray):
        '''
        Models the theoretical isotope distribution to the observed one in the spectrum using least square method
        Outliers are detected using a similar approach as the Grubbs test
        :param (ndArray, dtype=float) spectralIntensities: intensities in spectrum
        :param (ndArray, dtype=float) theoInt: calculated intensities
        :param (ndArray, dtype=float) mzArray:
        :return: (tuple[Any, list[float]) solution of scipy.optimize.minimize_scalar, m/z values which had an outlier intensity
        '''
        #x =np.sum(spectralIntensities)/len(spectralIntensities)
        solution = minimize_scalar(self.loss_1D_sum_square, args=(spectralIntensities, theoInt))
        calcIntensities = theoInt * solution.x
        #sumOfInt = np.sum(calcIntensities)
        #fitQuality = solution.fun**(0.5) / sumOfInt  # correct: (sum_square)^(1/2)/ion.intensity (but ion.intensity = n*I_av)
        # Grubbs('isch) test
        gValue = np.zeros(len(spectralIntensities))
        if solution.fun ** (0.5) > 0:
            gValue = (spectralIntensities - calcIntensities) / np.sqrt(solution.fun/len(spectralIntensities))
            #print(gValue, solution.fun, spectralIntensities,calcIntensities )
        outlier_index = np.where(gValue > self._configs['outlierLimit'])
        return solution, mzArray[outlier_index].tolist()


    def calcQuality(self, sumSquare, intensity):
        return sumSquare**(0.5) / intensity


    def calculateIntensity(self, ion):
        '''
        Models the theoretical isotope distribution of an ion to the observed one in the spectrum.
        Outliers (peaks with intensities much higher than expected) are detected and not used for modelling
        If the quality of the fit is below a certain threshold the ion is moved to deleted ions
        :param (FragmentIon) ion: corresponding (raw) ion
        :type ion: FragmentIon
        :return: (FragmentIon) ion with calculated intensity, quality, ppm error, etc.
        '''
        print(ion.getId())
        outlierList = list()
        ion, outliers = self.modelIon(ion)
        correctedIon = deepcopy(ion)
        if len(outliers) > 0:
            while len(outliers) > 0:
                outlierList += outliers
                print("outlier: ",outliers)
                noOutliers = np.isin(ion.getIsotopePattern()['m/z'],outlierList, invert=True)
                if np.all(ion.getIsotopePattern()['relAb'][noOutliers] == 0):
                    print("deleted:", ion.getName(), ion.getCharge(), ion.getIntensity(), round(ion.getQuality(), 2))
                    if ion.getComment() != "noise,":
                        ion.addComment("qual.")
                    if ion.getHash() not in self._deletedIons.keys():
                        self._deletedIons[ion.getHash()] = ion
                        return ion
                    else:
                        return ion
                else:
                    isoPattern = correctedIon.getIsotopePattern()
                    solution, outliers = self.modelDistribution(isoPattern['relAb'][noOutliers],
                                                                                   isoPattern['calcInt'][noOutliers],
                                                                                   isoPattern['m/z'][noOutliers])
                    correctedIon.setIntensity(np.sum(isoPattern['calcInt'] * solution.x))
                    #isoPattern['calcInt'] = correctedIon.getIsotopePattern()['calcInt'] * solution.x
                    correctedIon.setIsotopePatternPart('calcInt',correctedIon.getIsotopePattern()['calcInt']*solution.x)
            self.setQualityAndScore(correctedIon, solution)
            '''correctedIon.setQuality(self.calcQuality(solution.fun, correctedIon.getIntensity()))
            ion.setScore(calcScore(ion.getIntensity(), ion.getQuality(), self._noiseLevel))'''
            correctedIon.setError(np.average(ion.getIsotopePattern()['error'][noOutliers]
                                            [np.where(ion.getIsotopePattern()['relAb'][noOutliers] != 0)]))
            for peak in correctedIon.getIsotopePattern():
                if peak['m/z'] in outlierList:
                    peak['used'] = False
        return correctedIon

    def setQualityAndScore(self, ion, solution):
        intensity = ion.getIntensity()
        quality = self.calcQuality(solution.fun, intensity)
        ion.setQuality(quality)
        ion.setScore(calcScore(intensity, quality, self._noiseLevel))

    def modelIon(self, ion):
        '''
        :param (FragmentIon) ion: corresponding (raw) ion
        :type ion: FragmentIon
        :return: (FragmentIon) ion with calculated intensity, quality, ppm error, etc.
        '''
        print(ion.getName(),ion.getIsotopePattern())
        noOutliers = np.where(ion.getIsotopePattern()['used'])
        ion.setError(np.average(ion.getIsotopePattern()['error'][np.where(ion.getIsotopePattern()['relAb'][noOutliers] != 0)]))

        solution, outliers = \
            self.modelDistribution(ion.getIsotopePattern()['relAb'][noOutliers], ion.getIsotopePattern()['calcInt'][noOutliers],
                                   ion.getIsotopePattern()['m/z'][noOutliers])
        ion.setIntensity(np.sum(ion.getIsotopePattern()['calcInt'] * solution.x))
        #ion.isotopePattern['calcInt'] = ion.isotopePattern['calcInt'] * solution.x
        ion.setIsotopePatternPart('calcInt',ion.getIsotopePattern()['calcInt']*solution.x)
        if ion.getIntensity() != 0:
            '''ion.setQuality(self.calcQuality(solution.fun, ion.getIntensity()))
            ion.setScore(calcScore(ion.getIntensity(), ion.getQuality(), self._noiseLevel))'''
            self.setQualityAndScore(ion, solution)
        return ion, outliers

    def processIons(self, ion):
        '''
        Processes (calculates intensities, etc.) ions which are above the noise threshold
        :param (FragmentIon) ion: corresponding (raw) ion
        :type ion: FragmentIon
        '''
        correctedIon = self.calculateIntensity(ion)
        if correctedIon.getHash() in self._deletedIons.keys():
            return
        if (correctedIon.getQuality() > self._configs['shapeDel']) :
            correctedIon.addComment("qual.")
            self._deletedIons[correctedIon.getHash()] = correctedIon
        elif (correctedIon.getSignalToNoise() < self._configs['SNR']) :
            correctedIon.addComment("SNR")
            self._deletedIons[correctedIon.getHash()] = correctedIon
        else:
            self._correctedIons[correctedIon.getHash()] = correctedIon
            self._monoisotopicList.append(np.array(
                [(correctedIon.getName(), correctedIon.getCharge(), ion.getMonoisotopic())],
                dtype=[('name','U32'),('charge', np.uint8),('mono',float)]))
            '''self._monoisotopicList.append(
                (correctedIon.getName(), correctedIon.getCharge(), ion.getMonoisotopic()))'''
            print('\tqual',correctedIon.getQuality())

    def processNoiseIons(self, ion):
        '''
        Processes (calculates intensities, etc.) ions which are below the noise threshold
        :param (FragmentIon) ion: corresponding (raw) ion
        :type ion: FragmentIon
        '''
        correctedIon = self.calculateIntensity(ion)
        if correctedIon.getHash() not in self._deletedIons.keys():
            self._deletedIons[correctedIon.getHash()]=correctedIon

    def findSameMonoisotopics(self):
        '''
        Returns ions which show the same charge and monoistopic m/z
        :return: (list of list[FragmentIon]) list of list of ions with same charge and monoistopic m/z
        '''
        sameMonoisotopics = list()
        self._monoisotopicList = np.array(self._monoisotopicList,
                                          dtype=[('name','U32'),('charge', np.uint8),('mono',float)])
        for elem in self._monoisotopicList:
            same_mono_index = np.where((abs(calculateError(self._monoisotopicList['mono'], elem['mono']))
                 < getErrorLimit(elem['mono'], self._configs['k'], self._configs['d'])) & \
                                       (self._monoisotopicList['name'] != elem['name']) &
                                       (self._monoisotopicList['charge'] == elem['charge']))
            if len(self._monoisotopicList[same_mono_index]) > 0:    #direkte elemente von corrected spectrum uebernehmen
                sameMonoisotopic = [self._correctedIons[(elem['name'][0], elem['charge'][0])]]
                for elem2 in self._monoisotopicList[same_mono_index]:
                    sameMonoisotopic.append(self._correctedIons[(elem2['name'], elem2['charge'])])
                sameMonoisotopic.sort(key=lambda obj:(abs(obj.getError()),obj.getName()))
                if sameMonoisotopic not in sameMonoisotopics:
                    self.commentIonsInPatterns(([ion.getHash() for ion in sameMonoisotopic],))
                    sameMonoisotopics.append(sameMonoisotopic)
        return sameMonoisotopics

    def deleteSameMonoisotopics(self, ions):
        for ion in ions:
            self.deleteIon(ion.getHash(), "mono.")

    def deleteIon(self, ionHash, comment):
        if ionHash in self._correctedIons.keys():
            self._correctedIons[ionHash].addComment(comment)
            print('deleting',ionHash)
            self._deletedIons[ionHash] = self._correctedIons[ionHash]
            del self._correctedIons[ionHash]

    def remodelOverlaps(self, allAuto=False):
        '''
        Searches for overlaps (ions which have the same peaks) in spectrum. If the number of overlapping ions is below
        a threshold it re-models the combined isotope patterns of the overlapping ions to the peaks in the spectrum.
        The threshold is either the user defined one or 100
        :param (bool) allAuto: if true the threshold is set to 100
        :return: (list of list[FragmentIon]) all overlap patterns with more overlapping ions than the threshold
        '''
        maxOverlaps = 100
        if not allAuto:
            maxOverlaps = self._configs['manualDeletion']
        '''flag = 0
        if args and args[0]:
            flag = 1
            maxOverlaps = args[0]'''
        simplePatterns, complexPatterns = self.findOverlaps(maxOverlaps)
        if not allAuto:
            self.commentIonsInPatterns(simplePatterns)
        self.remodelIntensity(simplePatterns, [])
        return complexPatterns

    def findOverlaps(self,maxOverlaps):
        '''
        Searches for overlaps (ions which have the same peaks) in spectrum.
        :param (int) maxOverlaps: threshold for pattern to be complex
        :return: (tuple[list[list[FragmentIon]]], list[list[FragmentIon]]]) simple patterns, complex patterns
        '''
        self.usedPeaks = dict()
        overlappingPeaks = list()
        for ion in self._correctedIons.values():
            for peak in ion.getIsotopePattern():
                if peak['m/z'] in self.usedPeaks.keys():
                    overlappingPeaks.append(peak['m/z'])
                    self.usedPeaks.get(peak['m/z']).append(ion.getHash())
                else:
                    self.usedPeaks[peak['m/z']] = [ion.getHash()]
        overlappingPeaks.sort()
        revisedIons = list()
        simplePatterns = []
        complexPatterns = []
        for peak1 in overlappingPeaks:
            for firstIon in self.usedPeaks[peak1]:
                if firstIon in revisedIons:
                    continue
                pattern = [firstIon]
                index = 0
                while index < len(pattern):
                    revisedIons.append(pattern[index])
                    for peak2 in overlappingPeaks:
                        if pattern[index] in self.usedPeaks[peak2]:
                            [pattern.append(ion) for ion in self.usedPeaks[peak2] if ion not in pattern]
                    index += 1
                if len(pattern) > maxOverlaps:
                    self.commentIonsInPatterns((pattern,))
                    complexPatterns.append(sorted([self._correctedIons[ionTup] for ionTup in pattern],
                                                  key=lambda ion: ion.getIsotopePattern()['m/z'][0]))
                else:
                    simplePatterns.append(pattern)
        return simplePatterns,complexPatterns



    def commentIonsInPatterns(self, patterns):
        '''
        Adds comments to to overlapping ions
        :param (list of list[FragmentIon]) patterns: overlapping patterns
        '''
        for pattern in patterns:
            for ion1 in pattern:
                comment = "ov.:["
                for ion2 in pattern:
                    if ion2 != ion1:
                        comment += (str(ion2[0]) +"_"+ str(ion2[1]) + ",")
                self._correctedIons[ion1].addComment(comment[:-1] + "]")


    """for remodelling"""
    def setUpEquMatrix(self, ions, peaks, deletedIons):
        '''
        Sets up a (N_peaks x N_ions+1) matrix with:
        Each row corresponds to a peak in the spectrum
        Each column corresponds to an ion, the last is the spectral peak intensities
        The values (except the ones in the last column) are the calculated isotope peak intensities of the corresponding ion
        :param (list of tuple[str, int]) ions: ion-hashes of overlapping ions
        :param (ndarray, dtype = [float,float]) peaks: spectral peaks (m/z, int)
        :param (list of tuple[str, int]) deletedIons: ion-hashes of deleted ions
        :return: (ndarray(dtype = float), list tuples[str,int]) 2D array (N_peaks x N_ions+1), list of ion-hashes (N_ions)
        '''
        undeletedPeaks = list()
        undeletedIons = list()
        for ion in ions:
            if ion not in deletedIons:
                undeletedIons.append(ion)
        for peak in peaks:
            if peak[0] in self.usedPeaks:
                for ion in self.usedPeaks[peak[0]]:
                    if ion in undeletedIons:
                        undeletedPeaks.append(peak)
                        break
        equ_matrix = np.zeros((len(undeletedPeaks),len(undeletedIons)+1))
        for i in range(len(undeletedPeaks)):
            peak = undeletedPeaks[i]
            equ_matrix[i,-1] = peak[1]
            for j in range(len(undeletedIons)):
                ion = undeletedIons[j]
                if ion in self.usedPeaks[peak[0]]:
                    equ_matrix[i,j] = self._correctedIons[ion].getIsotopePattern()[
                        np.where(self._correctedIons[ion].getIsotopePattern()['m/z'] == peak[0])]['calcInt']
        return equ_matrix, undeletedIons

    @staticmethod
    def fun_sum_square(x, equ_matrix):
        '''
        Higher dimensional linear sum of square function for modelling the isotope peak intensities of overlapping ions
        :param (ndArray, dtype = float) x: weight vector
        :param (ndArray, dtype = [float,float]) equ_matrix: (N_peaks x N_ions+1) matrix (see setUpEquMatrix)
        :return: (float) sum of squares
        '''
        sum_square = 0
        for i in range(len(equ_matrix)):
            square = equ_matrix[i][-1]
            for j in range(len(x)):
                square -= equ_matrix[i][j] * x[j]
            sum_square += square ** 2
        return sum_square

    def remodelComplexPatterns(self, overlapPatterns, manDel):
        '''
        Processes lists of overlap patterns before the remodeling the combined isotope patterns of overlapping ions.
        :param (list of list[FragmentIon]) overlapPatterns: list of all patterns of overlapping ions
        :param (list of FragmentIon) manDel: ions which were deleted by the user
        '''
        hashedManDel = []
        for ion in manDel:
            ionHash = ion.getHash()
            hashedManDel.append(ionHash)
        hashedPatterns = []
        for pattern in overlapPatterns:
            hashedPatterns.append([ion.getHash() for ion in pattern])
        self.remodelIntensity(hashedPatterns, hashedManDel)
        self.deleteIons(manDel)

    def deleteIons(self, ions):
        [self.deleteIon(ion.getHash(), ",man.del.") for ion in ions]

    def remodelIntensity(self, overlapPatterns, manDel):
        '''
        Re-models the combined isotope patterns of the overlapping ions to the peaks in the spectrum.
        1. Array (spectr_peaks) of corresponding spectral peaks is created
        2. Abundances of ions are re-modelled by least square method (intensity multiplication factor is determined)
        3. If the factor multiplied by the number of overlapping ions in the pattern is below a threshold and the ion
            was not priorly undeleted by the user, the ion is transferred to the deleted ions
        4. Step 2 and 3 are repeated with all remaining ions as long as further ions are deleted in step 3
            If all ions except one were deleted the intensity of the remaining ion is not changed
        5. Calculated isotope peak intensities and summed intensities of the corresponding ions are changed
            Multiplication factors below 1.05 are reset to 1.05 to take overlaps with unkown ion species into account.
        6. Qualities of the fit are calculated (square root of the sum of squares devided by the summed intensity of
            all overlapping ions in the pattern)
        :param (list of list[tuple[str,int]]) overlapPatterns: list of all patterns of overlapping ions (as ion hash)
        :param (list of tuple[str,int]]) manDel: ions (as ion hash) which were deleted by the user
        '''
        for pattern in overlapPatterns:
            print(pattern)
            del_ions = []
            spectr_peaks = list()
            for ion in pattern:
                for peak in self._correctedIons[ion].getIsotopePattern():  # spectral list
                    if (peak['m/z'], peak['relAb']) not in spectr_peaks:
                        spectr_peaks.append((peak['m/z'], peak['relAb']))
            spectr_peaks = np.array(sorted(spectr_peaks, key=lambda tup: tup[0]))
            while True:
                equ_matrix, undeletedIons = self.setUpEquMatrix(pattern,spectr_peaks,del_ions+manDel)
                #print(equ_matrix)
                bnds = len(undeletedIons)*[(0.,None)]
                solution = minimize(self.fun_sum_square,np.ones(len(undeletedIons)),equ_matrix, bounds=bnds)
                del_so_far = len(del_ions)
                for ion, val in zip(undeletedIons, solution.x):
                    overlapThreshold = self._configs['overlapThreshold']
                    if 'man.undel,.' in self._correctedIons[ion].getComment():
                        overlapThreshold = 0
                    if val * len(undeletedIons) < overlapThreshold:
                        self._remodelledIons.append(deepcopy(self._correctedIons[ion]))
                        self._correctedIons[ion].addComment("low:" + str(round(val, 2)))
                        factor = val
                        if val <= 0:
                            #intensity is not directly set set to 0 because otherwise the isotope pattern would disappear
                            factor = 1/(10*self._correctedIons[ion].getIntensity())
                        self._correctedIons[ion].setIsotopePatternPart('calcInt',
                                                       self._correctedIons[ion].getIsotopePattern()['calcInt']*factor)
                        self._correctedIons[ion].setIntensity(self._correctedIons[ion].getIntensity() * factor)
                        del_ions.append(ion)
                        print("  ", ion, round(val, 2), 'deleted')
                if len(pattern)-len(del_ions) < 2:
                    for i in range(len(undeletedIons)):
                        if undeletedIons[i] not in del_ions:
                            print(" ", undeletedIons[i], "not re-modeled (no overlaps)")
                    break
                elif len(del_ions) - del_so_far > 0:
                    continue
                else:
                    sum_int = 0
                    for ion, val in zip(undeletedIons,solution.x):
                        self._remodelledIons.append(deepcopy(self._correctedIons[ion]))
                        if val < 1.05:  # no outlier calculation during remodelling --> results can be higher than without remodelling
                            factor = val
                        elif 'high' not in self._correctedIons[ion].getComment():
                            factor = 1.05
                            print("  ", ion, " not remodeled (val=", round(val,2), ")")
                            self._correctedIons[ion].addComment("high," + str(round(val, 2)))
                        else:
                            factor = 1
                            print("  ", ion, " not remodeled (val=", round(val,2), ")")
                        self._correctedIons[ion].setIsotopePatternPart('calcInt',
                            self._correctedIons[ion].getIsotopePattern()['calcInt'] * factor)
                        self._correctedIons[ion].setIntensity(self._correctedIons[ion].getIntensity() * factor)
                        sum_int += self._correctedIons[ion].getIntensity()  #for error calc
                    for ion in undeletedIons:
                        quality = self.calcQuality(solution.fun, sum_int)
                        self._correctedIons[ion].setQuality(quality)
                        self._correctedIons[ion].setScore(calcScore(sum_int, quality, self._noiseLevel))
                        if self._correctedIons[ion].getSignalToNoise() < self._configs['SNR']:
                            self.deleteIon(ion, 'SNR')
                    print("\tqual:",round(solution.fun**(0.5) / sum_int,2))
                    break
            for ion in del_ions:
                self._deletedIons[ion] = self._correctedIons[ion]
                print('deleting ',ion)
                del self._correctedIons[ion]
            print('')


    def switchIon(self, ion):
        '''
        Either deletes an ion or restores an deleted ion
        :param (FragmentIon) ion: corresponding ion
        '''
        hash = ion.getHash()
        returnedHash=None
        if hash in self._correctedIons.keys():
            comment = 'man.del.'
            oldDict, newDict = self._correctedIons, self._deletedIons
            returnedHash = self.checkForOverlaps(ion)
        elif hash in self._deletedIons.keys():
            comment = 'man.undel.'
            oldDict, newDict = self._deletedIons, self._correctedIons
        else:
            raise Exception("Ion " + ion.getName() + ", " + str(ion.getCharge()) + " unknown!")
        ion.addComment(comment)
        newDict[hash] = ion
        del oldDict[hash]
        return returnedHash

    def checkForOverlaps(self, ion):
        '''
        Checks if an ion which should be deleted overlaps with another ion
        :param (FragmentIon) ion: corresponding ion
        :return: (str) hash of overlapping ion
        '''
        overlappingIons = findall('\[(.*?)\]', ion.getComment())
        if len(overlappingIons)>0:
            ionStrings = overlappingIons[-1].split(',')
            counter=0
            returnedHash=None
            for ionString in ionStrings:
                vals = ionString.split('_')
                ionHash = (vals[0], int(vals[1]))
                if ionHash in self._correctedIons.keys():
                    counter+=1
                    returnedHash=ionHash
            if counter==1:
                return returnedHash
        return None

    def resetIon(self, ionHash):
        '''
        Repeats modelling step for one ion
        :param ionHash:
        :return:
        '''
        ion = self._correctedIons[ionHash]
        self._correctedIons[ionHash] = self.calculateIntensity(ion)
        self._correctedIons[ionHash].addComment(ion.getComment())
        self._correctedIons[ionHash].addComment('reset')
        return self._correctedIons[ionHash]

    def getAdjacentIons(self, ionHash):
        '''
        Returns all neighbouring ions (max 20) to a given ion within a max m/z range of 100 in the spectrum:
        :param (tuple[str,int]) ionHash: hash of the corresponding ion
        '''
        #sortedIons = sorted(list(self._correctedIons.values()), key=lambda ion: ion.isotopePattern['m/z'][0])
        monoisotopics = np.array([ion.getIsotopePattern()['m/z'][0] for ion in self._correctedIons.values()])
        distance = 100
        flag = 0
        if ionHash not in self._correctedIons.keys():
            flag = 1
        ion = self.getIon(ionHash)
        median = ion.getIsotopePattern()['m/z'][0]
        while True:
            monoisotopics = monoisotopics[np.where(abs(monoisotopics - median) < distance)]
            if len(monoisotopics) < 20:
                adjacentIons = [ion for ion in self._correctedIons.values() if abs(ion.getIsotopePattern()['m/z'][0] - median)<distance]
                if flag == 1:
                    adjacentIons.append(ion)
                return sorted(adjacentIons, key=lambda obj:obj.getIsotopePattern()['m/z'][0]), median-distance, median+distance
            elif len(monoisotopics) < 30:
                distance /= 1.5
            else:
                distance /= 2

    def getIon(self, ionHash):
        '''
        Returns an ion from the corresponding dict
        :param (tuple[str,int]) ionHash: hash of the corresponding ion
        :return: (FragmentIon) corresponding ion
        '''
        if ionHash in self._correctedIons.keys():
            return self._correctedIons[ionHash]
        elif ionHash in self._deletedIons.keys():
            return self._deletedIons[ionHash]
        raise Exception("Ion " + ionHash[0] + ", " + str(ionHash[1]) + " unknown!")

    def getRemodelledIon(self, ionHash):
        for ion in self.getRemodelledIons():
            if ion.getHash() == ionHash:
                return ion

    @staticmethod
    def getLimits(ions):
        '''
        Returns the m/z range of the isotope peaks of list of ions and the intensity of the highest isotope peak
        :param (list of FragmentIon) ions: list of ions
        :return: tuple[float,float,float] lowest m/z, highest m/z, intensity of the highest (spectral) isotope peak
        '''
        limits = np.array([(np.min(ion.getIsotopePattern()['m/z']), np.max(ion.getIsotopePattern()['m/z']),
                            np.max(ion.getIsotopePattern()['relAb'])) for ion in ions])
        return np.min(limits[:,0]), np.max(limits[:,1]), np.max(limits[:,2])


    def getPrecRegion(self, precName, precCharge):
        '''
        Returns the m/z area where precursor ions occur
        :param precName: name of the sequence
        :param precCharge: charge of the precursor
        :return: (tuple[float,float]) lowest m/z, m/z of precursor +70/precCharge (to include cationic adducts)
        '''
        precursorList = list()
        for ion in self._correctedIons.values():
            if (ion.getType() == precName) and (ion.getCharge() == precCharge):
                precursorList.append(ion.getMonoisotopic())
        if len(precursorList)<2:
            return (0,0)
        precursorList.sort()
        return (precursorList[0],precursorList[-1]+70/precCharge)

    def remodelSingleIon(self, ion, values):
        '''
        For modelling an ion manually
        :param (FragmentIon) ion: corresponding ion
        :param (ndarray, dtype = [float,bool]) values: 2D array of spectral peak intensities and bools if peak should be
            used for modelling
        :return: (float) modelled intensity of the ion
        '''
        values = np.array(values)
        ion.setIsotopePatternPart('relAb', values[:,0])
        ion.setIsotopePatternPart('used', values[:,1])
        return self.modelIon(ion)[0]

    def modelSimply(self, peakArray):
        '''
        Models a theroretical isotope pattern to a given peak list
        :param (ndarray, dtype = [float, float, float, bool]) peakArray: input array (m/z, relAb (spectral),
            calcInt (theo.), used)
        :return: (tuple[ndarray(dtype=[float, float, float, bool]), float, float]) output array (with modelled calcInt),
            summed intensity, quality of the fit
        '''
        noOutliers = np.where(peakArray['used'])
        solution, outliers = \
            self.modelDistribution(peakArray['relAb'][noOutliers], peakArray['calcInt'][noOutliers],
                                   peakArray['m/z'][noOutliers])
        peakArray['calcInt'] = np.around(peakArray['calcInt'] * solution.x)
        intensity = np.sum(peakArray['calcInt'])
        if intensity != 0:
            quality = self.calcQuality(solution.fun, intensity)
            return peakArray, intensity, quality
        else:
            return peakArray, intensity, 0.


    def setIonLists(self, observedIons, deletedIons, remIons):
        self._correctedIons = {ion.getHash():ion for ion in observedIons}
        self._deletedIons = {ion.getHash():ion for ion in deletedIons}
        self._remodelledIons = remIons