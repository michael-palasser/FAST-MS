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
        self._configs = configurations
        self._correctedIons = dict()
        self._deletedIons = dict()
        self._remodelledIons = list()
        self._monoisotopicList = list()

    def getObservedIons(self):
        return self._correctedIons

    def getDeletedIons(self):
        return self._deletedIons

    def getRemodelledIons(self):
        return self._remodelledIons

    def addRemodelledIon(self, ion):
        self._remodelledIons.append(ion)

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
        outlier_index = np.where(gValue > self._configs['outlierLimit'])
        return solution, sumOfInt, gValue, mzArray[outlier_index].tolist()


    def calculateIntensity(self, ion):
        """models the Isotope distribution for the calculation of intensity and standard deviation and kicks out non real
        results (due to overlaps, noise etc.)"""
        print(ion.getName(), ion.charge)
        outlierList = list()
        '''ion.error = np.average(ion.isotopePattern['error'][np.where((ion.isotopePattern['relAb'] != 0) & (ion.isotopePattern['used']))])
        solution, ion.intensity, gValue, outliers = \
            self.modelDistribution(ion.isotopePattern['relAb'], ion.isotopePattern['calcInt'], ion.isotopePattern['m/z'])
        ion.isotopePattern['calcInt'] = ion.isotopePattern['calcInt'] * solution.x
        ion.quality = solution.fun**(0.5) / ion.intensity
        ion.getScore()'''
        ion, outliers = self.modelIon(ion)
        #ToDo: corrected ion not necessary?
        correctedIon = deepcopy(ion)
        if len(outliers) > 0:
            while len(outliers) > 0:
                outlierList += outliers
                print("outlier: ",outliers)
                noOutliers = np.isin(ion.isotopePattern['m/z'],outlierList, invert=True)
                if np.all(ion.isotopePattern['relAb'][noOutliers] == 0):
                    print("deleted:", ion.getName(), ion.charge, ion.intensity, round(ion.quality, 2))
                    if ion.comment != "noise,":
                        ion.comment = "qual.,"
                    if self.getHash(ion) not in self._deletedIons.keys():
                        self._deletedIons[self.getHash(ion)] = ion
                        return ion
                    else:
                        return ion
                else:
                    solution, correctedIon.intensity, gValue, outliers = \
                        self.modelDistribution(correctedIon.isotopePattern['relAb'][noOutliers],
                                               correctedIon.isotopePattern['calcInt'][noOutliers],
                                               correctedIon.isotopePattern['m/z'][noOutliers])
                    correctedIon.isotopePattern['calcInt'] = correctedIon.isotopePattern['calcInt'] * solution.x
            correctedIon.quality = solution.fun**(0.5) / ion.intensity
            correctedIon.getScore()
            correctedIon.error = np.average(ion.isotopePattern['error'][noOutliers]
                                            [np.where(ion.isotopePattern['relAb'][noOutliers] != 0)])
            for peak in correctedIon.isotopePattern:
                if peak['m/z'] in outlierList:
                    peak['used'] = False
        return correctedIon


    def modelIon(self, ion):
        noOutliers = np.where(ion.isotopePattern['used'])
        ion.error = np.average(ion.isotopePattern['error'][np.where(ion.isotopePattern['relAb'][noOutliers] != 0)])
        solution, ion.intensity, gValue, outliers = \
            self.modelDistribution(ion.isotopePattern['relAb'][noOutliers], ion.isotopePattern['calcInt'][noOutliers],
                                   ion.isotopePattern['m/z'][noOutliers])
        ion.isotopePattern['calcInt'] = ion.isotopePattern['calcInt'] * solution.x
        if ion.getIntensity() != 0:
            ion.quality = solution.fun ** (0.5) / ion.intensity
            ion.getScore()
        return ion, outliers

    def processIons(self, ion):
        correctedIon = self.calculateIntensity(ion)
        if self.getHash(correctedIon) in self._deletedIons.keys():
            return
        if (correctedIon.quality < self._configs['shapeDel']) :
            self._correctedIons[self.getHash(correctedIon)] = correctedIon
            self._monoisotopicList.append(np.array(
                [(correctedIon.getName(), correctedIon.charge, ion.getMonoisotopic())],
                dtype=[('name','U32'),('charge', np.uint8),('mono',np.float64)]))
            print('\tqual',correctedIon.quality)
        else:
            correctedIon.comment = "qual.,"
            self._deletedIons[self.getHash(correctedIon)]=correctedIon

    def processNoiseIons(self, ion):
        correctedIon = self.calculateIntensity(ion)
        if self.getHash(correctedIon) not in self._deletedIons.keys():
            self._deletedIons[self.getHash(correctedIon)]=correctedIon

    def findSameMonoisotopics(self):
        sameMonoisotopics = list()
        self._monoisotopicList = np.array(self._monoisotopicList)
        for elem in self._monoisotopicList:
            same_mono_index = np.where((abs(self.calculateError(self._monoisotopicList['mono'], elem['mono']))
                 < getErrorLimit(elem['mono'])) & \
                                       (self._monoisotopicList['name'] != elem['name']) &
                                       (self._monoisotopicList['charge'] == elem['charge']))
            if len(self._monoisotopicList[same_mono_index]) > 0:    #direkte elemente von corrected spectrum uebernehmen
                sameMonoisotopic = [self._correctedIons[(elem['name'][0], elem['charge'][0])]]
                for elem2 in self._monoisotopicList[same_mono_index]:
                    sameMonoisotopic.append(self._correctedIons[(elem2['name'], elem2['charge'])])
                sameMonoisotopic.sort(key=lambda obj:(abs(obj.error),obj.getName()))
                if sameMonoisotopic not in sameMonoisotopics:
                    self.commentIonsInPatterns(([self.getHash(ion) for ion in sameMonoisotopic],))
                    sameMonoisotopics.append(sameMonoisotopic)
        return sameMonoisotopics

    def deleteSameMonoisotopics(self, ions):
        for ion in ions:
            self.deleteIon(self.getHash(ion), ",mono.,")

    def deleteIon(self, ionHash, comment):
        self._correctedIons[ionHash].comment += comment
        print('deleting',ionHash)
        self._deletedIons[ionHash] = self._correctedIons[ionHash]
        del self._correctedIons[ionHash]

    def findOverlaps(self, *args):
        maxOverlaps = self._configs['manualDeletion']
        flag = 0
        if args and args[0]:
            flag = 1
            maxOverlaps = args[0]
        self.usedPeaks = dict()
        overlappingPeaks = list()
        for ion in self._correctedIons.values():
            for peak in ion.isotopePattern:
                if peak['m/z'] in self.usedPeaks.keys():
                    overlappingPeaks.append(peak['m/z'])
                    self.usedPeaks.get(peak['m/z']).append(self.getHash(ion))
                else:
                    self.usedPeaks[peak['m/z']] = [self.getHash(ion)]
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
                print(pattern)
                if len(pattern) > maxOverlaps:
                    self.commentIonsInPatterns((pattern,))
                    complexPatterns.append(sorted([self._correctedIons[ionTup] for ionTup in pattern],
                                                  key=lambda ion: ion.isotopePattern['m/z'][0]))
                else:
                    simplePatterns.append(pattern)
        if flag == 0:
            self.commentIonsInPatterns(simplePatterns)
        self.remodelIntensity(simplePatterns, [])
        return complexPatterns


    def commentIonsInPatterns(self, patterns):
        for pattern in patterns:
            for ion1 in pattern:
                comment = "ov.:["
                for ion2 in pattern:
                    if ion2 != ion1:
                        comment += (str(ion2[0]) +"_"+ str(ion2[1]) + ",")
                self._correctedIons[ion1].comment = (comment[:-1] + "],")


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
                    equ_matrix[i,j] = self._correctedIons[ion].isotopePattern[
                        np.where(self._correctedIons[ion].isotopePattern['m/z'] == peak[0])]['calcInt']
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

    def remodelComplexPatterns(self, overlapPatterns, manDel):
        hashedManDel = []
        for ion in manDel:
            ionHash = self.getHash(ion)
            hashedManDel.append(ionHash)
        hashedPatterns = []
        for pattern in overlapPatterns:
            hashedPatterns.append([self.getHash(ion) for ion in pattern])
        self.remodelIntensity(hashedPatterns, hashedManDel)
        self.deleteIons(manDel)

    def deleteIons(self, ions):
        [self.deleteIon(self.getHash(ion), ",man.del.") for ion in ions]

    def remodelIntensity(self, overlapPatterns, manDel):
        for pattern in overlapPatterns:
            print(pattern)
            del_ions = []
            spectr_peaks = list()
            for ion in pattern:
                for peak in self._correctedIons[ion].isotopePattern:  # spectral list
                    if (peak['m/z'], peak['relAb']) not in spectr_peaks:
                        spectr_peaks.append((peak['m/z'], peak['relAb']))
            spectr_peaks = np.array(sorted(spectr_peaks, key=lambda tup: tup[0]))
            while True:
                equ_matrix, undeletedIons = self.setUpEquMatrix(pattern,spectr_peaks,del_ions+manDel)
                #print(equ_matrix)
                solution = minimize(self.fun_sum_square,np.ones(len(undeletedIons)),equ_matrix)
                del_so_far = len(del_ions)
                for ion, val in zip(undeletedIons, solution.x):
                    overlapThreshold = self._configs['overlapThreshold']
                    if 'man.undel.' in self._correctedIons[ion].comment:
                        overlapThreshold = 0
                    if val * len(undeletedIons) < overlapThreshold:
                        self._remodelledIons.append(deepcopy(self._correctedIons[ion]))
                        self._correctedIons[ion].comment += ("low," + str(round(val, 2)))
                        factor=0
                        if val > 0:
                            factor = val
                        self._correctedIons[ion].isotopePattern['calcInt'] *= factor
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
                        if val < 1.05:  # no outlier calculation during remodelling --> results can be higher than without remodelling
                            factor = val
                        else:
                            factor = 1.05
                            print("  ", ion, " not remodeled (val=", round(val,2), ")")
                            self._correctedIons[ion].comment += ("high," + str(round(val, 2)))
                        self._remodelledIons.append(deepcopy(self._correctedIons[ion]))
                        self._correctedIons[ion].isotopePattern['calcInt'] *= factor
                        self._correctedIons[ion].intensity *= factor
                        sum_int += self._correctedIons[ion].intensity  #for error calc
                    for ion in undeletedIons:
                        self._correctedIons[ion].quality = solution.fun ** (0.5) / sum_int
                        self._correctedIons[ion].getScore()
                    print("\tqual:",round(solution.fun**(0.5) / sum_int,2))
                    break
            for ion in del_ions:
                self._deletedIons[ion] = self._correctedIons[ion]
                print('deleting ',ion)
                del self._correctedIons[ion]
            print('')


    def getIndexToDelete(self, overlapPattern):
        print("Complicated Overlap pattern1: Do you want to delete an ion before modelling?")
        print('index\t m/z\t\t\tz\tI\t\t\tfragment\t\terror /ppm\tquality')
        count = 1
        for ion in overlapPattern:
            print("{:>2}".format(count), "\t", self._correctedIons[ion].toString())
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

    def switchIon(self, ionToDelete):
        hash = self.getHash(ionToDelete)
        if hash in self._correctedIons.keys():
            comment = 'man.del.,'
            oldDict, newDict = self._correctedIons, self._deletedIons
        elif hash in self._deletedIons.keys():
            comment = 'man.undel.,'
            oldDict, newDict = self._deletedIons, self._correctedIons
        else:
            raise Exception("Ion " + ionToDelete.getName() + ", " + str(ionToDelete.charge) + " unknown!")
        ionToDelete.comment += comment
        newDict[hash] = ionToDelete
        del oldDict[hash]

    def getAdjacentIons(self, ionHash):
        monoisotopicDict = {ion.isotopePattern['m/z'][0]: key for key, ion in self._correctedIons.items()}
        monoisotopics = np.array(sorted(list(monoisotopicDict.keys())))
        distance = 100
        flag = 0
        if ionHash not in self._correctedIons.keys():
            flag = 1
        ion = self.getIon(ionHash)
        median = ion.isotopePattern['m/z'][0]
        while True:
            monoisotopics = monoisotopics[np.where(abs(monoisotopics - median) < distance)]
            if len(monoisotopics) < 20:
                adjacentIons = [self._correctedIons[monoisotopicDict[mono]] for mono in monoisotopics]
                if flag == 1:
                    adjacentIons.append(ion)
                    return sorted(adjacentIons, key=lambda obj:obj.isotopePattern['m/z'][0]), median-distance, median+distance
                else:
                    return adjacentIons, median-distance, median+distance
            elif len(monoisotopics) < 30:
                distance /= 1.5
            else:
                distance /= 2

    def getIon(self, ionHash):
        if ionHash in self._correctedIons.keys():
            return self._correctedIons[ionHash]
        elif ionHash in self._deletedIons.keys():
            return self._deletedIons[ionHash]
        raise Exception("Ion " + ionHash[0] + ", " + str(ionHash[1]) + " unknown!")

    def getRemodelledIon(self, ionHash):
        for ion in self.getRemodelledIons():
            if self.getHash(ion) == ionHash:
                return ion

    @staticmethod
    def getLimits(ions):
        limits = np.array([(np.min(ion.isotopePattern['m/z']), np.max(ion.isotopePattern['m/z']),
                            np.max(ion.isotopePattern['relAb'])) for ion in ions])
        return np.min(limits[:,0]), np.max(limits[:,1]), np.max(limits[:,2])


    def getPrecRegion(self, precName, precCharge):
        precursorList = list()
        for ion in self._correctedIons.values():
            if (ion.type == precName) and (ion.charge == precCharge):
                precursorList.append(ion.getMonoisotopic())
        if len(precursorList)<2:
            return (0,0)
        precursorList.sort()
        return (precursorList[0],precursorList[-1]+70/precCharge)

    def remodelSingleIon(self, ion, values):
        values = np.array(values)
        ion.isotopePattern['relAb'] = values[:,0]
        ion.isotopePattern['used'] = values[:,1]
        return self.modelIon(ion)[0]

    def modelSimply(self, peakArray):
        '''

        :param peakArray: m/z,relAb,calcInt,used
        :return:
        '''
        noOutliers = np.where(peakArray['used'])
        solution, intensity, gValue, outliers = \
            self.modelDistribution(peakArray['relAb'][noOutliers], peakArray['calcInt'][noOutliers],
                                   peakArray['m/z'][noOutliers])
        peakArray['calcInt'] = np.around(peakArray['calcInt'] * solution.x)
        print('modelled',peakArray, intensity)
        if intensity != 0:
            quality = solution.fun ** (0.5) / intensity
            return peakArray, intensity, quality
        else:
            return peakArray, intensity, 0

    def setIonLists(self, observedIons, deletedIons, remIons):
        self._correctedIons = {self.getHash(ion):ion for ion in observedIons}
        self._deletedIons = {self.getHash(ion):ion for ion in deletedIons}
        self._remodelledIons = remIons