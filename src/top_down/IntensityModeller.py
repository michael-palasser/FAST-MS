'''
Created on 6 Aug 2020

@author: michael
'''
import numpy as np
from copy import deepcopy
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from src.top_down.SpectrumHandler import getErrorLimit

class IntensityModeller(object):
    '''
    classdocs
    '''
    def __init__(self, configurations):
        #self.outlierLimit = outlierLimit
        #self.shapeLimit = shapeLimit
        self.configs = configurations
        self.correctedIons = dict()
        self.deletedIons = list()
        self.remodelledIons = list()
        self.monoisotopicList = list()
        self.usedPeaks = dict()

    @staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6

    @staticmethod
    def getHash(ion):
        return (ion.getName(),ion.charge)


    @staticmethod
    def fun_sum_square_scalar(x,spectralIntensities,theoIntensities):
        sum_square = 0
        for spectralIntensity, theoIntensities in zip(spectralIntensities,theoIntensities):
            sum_square += (spectralIntensity-theoIntensities*x)**2
        return sum_square


    def modelDistribution(self, spectralIntensities, theoInt, mzArray):
        #x =np.sum(spectralIntensities)/len(spectralIntensities)
        solution = minimize_scalar(self.fun_sum_square_scalar, args=(spectralIntensities, theoInt))
        calcIntensities = theoInt * solution.x
        sumOfInt = np.sum(calcIntensities)
        #fitQuality = solution.fun**(0.5) / sumOfInt  # correct: (sum_square)^(1/2)/ion.intensity (but ion.intensity = n*I_av)
        # Grubbs'isch test
        gValue = np.zeros(len(spectralIntensities))
        if solution.fun ** (0.5) > 0:
            gValue = (spectralIntensities - calcIntensities) / solution.fun ** (0.5)
            #print(gValue, solution.fun, spectralIntensities,calcIntensities )
        outlier_index = np.where(gValue > self.configs['outlierLimit'])
        return solution, sumOfInt, gValue, mzArray[outlier_index].tolist()


    def calculateIntensity(self, ion):
        """models the Isotope distribution for the calculation of intensity and standard deviation and kicks out non real
        results (due to overlaps, noise etc.)"""
        print(ion.getName(), ion.charge)
        outlierList = list()
        ion.error = np.average(ion.isotopePattern['error'][np.where(ion.isotopePattern['error'] != 0)])
        solution, ion.intensity, gValue, outliers = \
            self.modelDistribution(ion.isotopePattern['relAb'], ion.isotopePattern['calcInt'], ion.isotopePattern['m/z'])
        ion.isotopePattern['calcInt'] = ion.isotopePattern['calcInt'] * solution.x
        ion.quality = solution.fun**(0.5) / ion.intensity
        ion.getScore()
        #ToDo: corrected ion not necessary?
        correctedIon = deepcopy(ion)
        if len(outliers) > 0:
            while len(outliers) > 0:
                outlierList += outliers
                print("outlier: ",outliers)
                noOutliers = np.isin(ion.isotopePattern['m/z'],outlierList, invert=True)
                if np.all(ion.isotopePattern['relAb][noOutliers] == 0):
                    print("deleted:", ion.getName(), ion.charge, ion.intensity, round(ion.quality, 2))
                    if ion.comment != "noise":
                        ion.comment = "qual."
                    if ion not in self.deletedIons:
                        self.deletedIons.append(ion)
                        return ion
                    else:
                        return ion
                else:
                    solution, correctedIon.intensity, gValue, outliers = \
                        self.modelDistribution(correctedIon.isotopePattern['relAb][noOutliers],
                                               correctedIon.isotopePattern['calcInt'][noOutliers],
                                               correctedIon.isotopePattern['m/z'][noOutliers])
                    correctedIon.isotopePattern['calcInt'] = correctedIon.isotopePattern['calcInt'] * solution.x
            correctedIon.quality = solution.fun**(0.5) / ion.intensity
            correctedIon.getScore()
            correctedIon.error = np.average(ion.isotopePattern['error'][noOutliers]
                                            [np.where(ion.isotopePattern['error'][noOutliers] != 0)])
            for peak in correctedIon.isotopePattern:
                if peak['m/z'] in outlierList:
                    peak['used'] = 0
        return correctedIon

    def processIons(self, ion):
        correctedIon = self.calculateIntensity(ion)
        if correctedIon in self.deletedIons:
            return
        if (correctedIon.quality < self.configs['shapeDel']) :
            self.correctedIons[self.getHash(correctedIon)] = correctedIon
            self.monoisotopicList.append(np.array(
                [(correctedIon.getName(), correctedIon.charge, ion.getMonoisotopic())],
                dtype=[('name','U32'),('charge', np.uint8),('mono',np.float64)]))
            print('\tqual',correctedIon.quality)
        else:
            correctedIon.comment = "qual."
            self.deletedIons.append(correctedIon)

    def processNoiseIons(self, ion):
        correctedIon = self.calculateIntensity(ion)
        if correctedIon not in self.deletedIons:
            self.deletedIons.append(correctedIon)

    def findSameMonoisotopics(self):
        sameMonoisotopics = list()
        self.monoisotopicList = np.array(self.monoisotopicList)
        for elem in self.monoisotopicList:
            same_mono_index = np.where((abs(self.calculateError(self.monoisotopicList['mono'], elem['mono']))
                 < getErrorLimit(elem['mono'])) & \
                    (self.monoisotopicList['name'] != elem['name']) &
                    (self.monoisotopicList['charge'] == elem['charge']))
            if len(self.monoisotopicList[same_mono_index]) > 0:    #direkte elemente von corrected spectrum uebernehmen
                sameMonoisotopic = [self.correctedIons[(elem['name'][0],elem['charge'][0])]]
                for elem2 in self.monoisotopicList[same_mono_index]:
                    sameMonoisotopic.append(self.correctedIons[(elem2['name'],elem2['charge'])])
                sameMonoisotopic.sort(key=lambda obj:abs(obj.error))
                if sameMonoisotopic not in sameMonoisotopics:
                    sameMonoisotopics.append(sameMonoisotopic)
        if len(sameMonoisotopics) > 0:
            print("Warning: These spectrum share the same monoisotopic peak and charge:")
        return sameMonoisotopics

    def deleteIon(self, ion):
        self.correctedIons[self.getHash(ion)].comment = "mono."
        self.deletedIons.append(ion)
        del self.correctedIons[self.getHash(ion)]

    def findOverlaps(self):
        overlappingPeaks = list()
        for ion in self.correctedIons.values():
            for peak in ion.isotopePattern:
                if peak['m/z'] in self.usedPeaks.keys():
                    overlappingPeaks.append(peak['m/z'])
                    self.usedPeaks.get(peak['m/z']).append(self.getHash(ion))
                else:
                    self.usedPeaks[peak['m/z']] = [self.getHash(ion)]
        overlappingPeaks.sort()
        revisedIons = list()
        patterns = list()
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
                patterns.append(pattern)
        self.commentIonsInPatterns(patterns)
        return patterns


    def commentIonsInPatterns(self, patterns):
        for pattern in patterns:
            for ion1 in pattern:
                comment = "ov.:["
                for ion2 in pattern:
                    if ion2 != ion1:
                        comment += (str(ion2[0]) +"_"+ str(ion2[1]) + ",")
                self.correctedIons[ion1].comment = (comment[:-1]+ "]")


    """for remodelling"""
    def setUpEquMatrix(self, ions, peaks, deletedIons):
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
                    equ_matrix[i,j] = self.correctedIons[ion].isotopePattern[
                        np.where(self.correctedIons[ion].isotopePattern['m/z'] == peak[0])]['calcInt']
        return equ_matrix, undeletedIons

    @staticmethod
    def fun_sum_square(x, equ_matrix):
        sum_square = 0
        for i in range(len(equ_matrix)):
            square = equ_matrix[i][-1]
            for j in range(len(x)):
                square -= equ_matrix[i][j] * x[j]
            sum_square += square ** 2
        return sum_square


    def remodelIntensity(self):
        for pattern in self.findOverlaps():
            print(pattern)
            del_ions = list()
            if len(pattern) > self.configs['manualDeletion']:
                indexToDelete = self.getIndexToDelete(pattern)
                count = 0
                for ion in pattern:
                    count += 1
                    if count in indexToDelete:
                        print("Deleting ", ion)
                        self.correctedIons[ion].comment += ",man.del."
                        del_ions.append(ion)
            spectr_peaks = list()
            for ion in pattern:
                for peak in self.correctedIons[ion].isotopePattern:  # spectral list
                    if (peak['m/z'], peak['relAb']) not in spectr_peaks:
                        spectr_peaks.append((peak['m/z'], peak['relAb']))
            spectr_peaks = np.array(sorted(spectr_peaks, key=lambda tup: tup[0]))
            while True:
                equ_matrix, undeletedIons = self.setUpEquMatrix(pattern,spectr_peaks,del_ions)
                #print(equ_matrix)
                solution = minimize(self.fun_sum_square,np.ones(len(undeletedIons)),equ_matrix)
                del_so_far = len(del_ions)
                for ion, val in zip(undeletedIons, solution.x):
                    if val * len(undeletedIons) < self.configs['overlapThreshold']:
                        del_ions.append(ion)
                        self.correctedIons[ion].comment += (",low" + str(round(val, 2)))
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
                        if val < 1.05:  # no outlier calculation during remodelling --> results can be higher than without remodelling
                            factor = val
                        else:
                            factor = 1.05
                            print("  ", ion, " not remodeled (val=", round(val,2), ")")
                            self.correctedIons[ion].comment += (",high" + str(round(val, 2)))
                        self.remodelledIons.append(deepcopy(self.correctedIons[ion]))
                        self.correctedIons[ion].isotopePattern['calcInt'] *= factor
                        self.correctedIons[ion].intensity *= factor
                        sum_int += self.correctedIons[ion].intensity  #for error calc
                    for ion in undeletedIons:
                        self.correctedIons[ion].quality = solution.fun**(0.5) / sum_int
                        self.correctedIons[ion].getScore()
                    print("\tqual:",round(solution.fun**(0.5) / sum_int,2))
                    break
            for ion in del_ions:
                self.deletedIons.append(self.correctedIons[ion])
                del self.correctedIons[ion]
            print('')



    def getIndexToDelete(self, overlapPattern):
        print("Complicated Overlap pattern1: Do you want to delete an ion before modelling?")
        print('index\t m/z\t\t\tz\tI\t\t\tfragment\t\terror /ppm\tquality')
        count = 1
        for ion in overlapPattern:
            print("{:>2}".format(count), "\t", self.correctedIons[ion].toString())
            count += 1
        indexToDelete = list()
        while True:
            ionIndex = input("Enter the index of the ion:")
            if (ionIndex == ""):
                break
            else:
                try:
                    if (ionIndex.startswith("+")):
                        indexToDelete.remove(int(ionIndex[1:]))
                        print("ion with index", ionIndex[1:], "not deleted")
                    elif (int(ionIndex) > len(overlapPattern)):
                        print("index too high")
                        continue
                    else:
                        indexToDelete.append(int(ionIndex))
                except:
                    print("non valid input")
                    continue
        return indexToDelete


    def getPrecRegion(self, precName, precCharge):
        precursorList = list()
        for ion in self.correctedIons.values():
            if (ion.type == precName) and (ion.charge == precCharge):
                precursorList.append(ion.getMonoisotopic())
        precursorList.sort()
        print()
        return ((precursorList[0],precursorList[-1]+70/precCharge))