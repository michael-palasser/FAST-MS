'''
Created on 2 Oct 2020

@author: michael
'''

import numpy as np

class IntactAnalyser(object):
    '''
    Responsible for analysing lists of observed ion
    '''
    def __init__(self, listOfIonLists, useAbundances=True):
        '''
        :param (list[list[list[SimpleIntactIon]]]) listOfIonLists: nested lists of IntactIons (ions in each spectrum in each file)
        :param (bool) useIntensities
        '''
        self._listOfIonLists = listOfIonLists
        self._useAbundances = useAbundances
        self._minCharge = 250
        self._maxCharge = 0

    def calculateAvChargeAndError(self):
        '''
        Calculates average charges and errors of each spectrum in each file
        :return: (tuple[list[list[float]], list[list[float]]]) average charges, average errors
        '''
        #value changed if reduced intensities are used
        listOfAverageCharges, listOfAverageErrors, listOfStddevOfErrors = [], [], []
        for ionlists in self._listOfIonLists:
            averageCharges, averageErrors, stddevOfErrors = [], [], []
            for ionList in ionlists:
                #exclude SNAP misassignments
                errors = np.array([ion.getError() for ion in ionList if abs(ion.getError()) < 30])
                averageErrors.append(np.average(errors))
                stddevOfErrors.append(np.std(errors))
                arr = np.array([(ion.getIntensity(),ion.getCharge()) for ion in ionList], dtype=np.int64)
                #if abundanceMode:
                #    arr[:,0] *= arr[:,1]
                averageCharges.append((np.sum(arr[:,0]*arr[:,1])/np.sum(arr[:,0]),
                                       np.sum(arr[:,0])/np.sum(arr[:,0]/arr[:,1])))
                minCharge, maxCharge = np.min(arr[:,1]), np.max(arr[:,1])
                if minCharge < self._minCharge:
                    self._minCharge = int(minCharge)
                if maxCharge > self._maxCharge:
                    self._maxCharge = int(maxCharge)
            listOfAverageCharges.append(averageCharges)
            listOfAverageErrors.append(averageErrors)
            listOfStddevOfErrors.append(stddevOfErrors)
        return listOfAverageCharges, listOfAverageErrors, listOfStddevOfErrors

    def calculateAverageModification(self):
        '''
        Calculates average numbers of modifications for each charge  and in total of each spectrum in each file
        :return: (list[list[dict[int,float]]] , list[list[float]]) tuple of list of {z:av.modification per z} and
            list of av.modification
        '''
        listOfAverageModifications = []
        listOfTotalAverageModifications = []
        for ionlists in self._listOfIonLists:
            averageModifications = list()
            totalAverageModifications = []
            for ionList in ionlists:
                averageModificationPerZ = dict()
                totalModified = 0
                total = 0
                for ion in ionList:
                    charge = ion.getCharge()
                    if self._useAbundances:
                        intensity = ion.getRelAbundance()
                    else:
                        intensity = ion.getIntensity()
                    if charge in averageModificationPerZ:
                        averageModificationPerZ[charge] += np.array([float(ion.getNrOfModifications()) * intensity, intensity])
                    else:
                        averageModificationPerZ[charge] = np.array([float(ion.getNrOfModifications()) * intensity, intensity])
                    #if self._useIntensities:
                    totalModified += float(ion.getNrOfModifications()) * intensity
                    total += intensity
                    '''else:
                        totalModified += float(ion.getNrOfModifications()) * intensity / charge
                        total += intensity / charge'''
                for z,val in averageModificationPerZ.items():
                    averageModificationPerZ[z] = val[0]/val[1]  #ToDo: check if robust
                averageModifications.append(averageModificationPerZ)
                totalAverageModifications.append(totalModified/total)
            listOfAverageModifications.append(averageModifications)
            listOfTotalAverageModifications.append(totalAverageModifications)
        return listOfAverageModifications, listOfTotalAverageModifications

    def makeChargeArray(self):
        '''
        Makes an array filled with observed charges
        :return: (ndarray(dtype = [int,int]) [(charge, 0)]
        '''
        arr = np.zeros((self._maxCharge - self._minCharge + 1, 2))
        for i in range(self._maxCharge - self._minCharge + 1):
            arr[i][0] = self._minCharge + i
        return arr

    def calculateModifications(self):
        '''
        Calculates the abundance of each modification for each charge state and in total in each spectrum in each file
        :return: (list[list[dict[str,ndarray(dtype=(int,float)])]], list[list[dict[str,float]]]) tuple of
            list of dicts of proportion of a modification per charge {modification: array([charge, percentage])}
            list of dicts of proportion of a modification {modification: percentage}
        '''
        listOfModificationsPerZInSpectra = []
        listOfModificationsInSpectra = []
        for ionlists in self._listOfIonLists:
            modificationsPerZInSpectra = list()
            modificationsInSpectra = list()
            #avOfModInSpectra = list()
            for ionList in ionlists:
                modificationsPerZ = dict()
                intensitiesPerCharge = self.makeChargeArray()
                for ion in ionList:
                    currentModification = ion.getModification()
                    if self._useAbundances:
                        intensity = ion.getRelAbundance()
                    else:
                        intensity = ion.getIntensity()
                    if currentModification not in modificationsPerZ:
                        modificationsPerZ[currentModification] = self.makeChargeArray()
                    modificationsPerZ[currentModification][ion.getCharge() - self._minCharge][1] = intensity
                    intensitiesPerCharge[ion.getCharge() - self._minCharge][1] += intensity
                nonZero = np.where(intensitiesPerCharge[:,1] != 0)
                dataLength = len(intensitiesPerCharge[nonZero])
                #averageOfModifications = dict()
                modificationsPerZ2 = dict()
                modifications = dict()
                #if abundanceMode:
                total = np.sum(intensitiesPerCharge[:,1])
                #else:
                #    total = np.sum(intensitiesPerCharge[:,1]/intensitiesPerCharge[:,0])
                for mod,arr in modificationsPerZ.items():
                    newArr = np.zeros((dataLength,2))
                    for i in range(dataLength):
                        newArr[i] = [intensitiesPerCharge[nonZero][i,0],
                                     arr[nonZero][i,1]/intensitiesPerCharge[nonZero][i,1]]
                    #averageOfModifications[mod] = np.average(newArr[:,1])
                    modificationsPerZ2[mod] = newArr
                    #if abundanceMode:
                    modifications[mod] = np.sum(arr[:,1])/ total
                    #else:
                    #    modifications[mod] = np.sum(arr[:,1]/arr[:,0])/ total
                modificationsPerZInSpectra.append(modificationsPerZ2)
                modificationsInSpectra.append(modifications)
                #avOfModInSpectra.append(averageOfModifications)
            listOfModificationsPerZInSpectra.append(modificationsPerZInSpectra)
            listOfModificationsInSpectra.append(modificationsInSpectra)
        return listOfModificationsPerZInSpectra, listOfModificationsInSpectra

    def getSortedIonList(self):
        '''
        Returns lists of ionLists with sorted ions
        :return: (list[list[list[SimpleIntactIon]]])
        '''
        returnedLists = list()
        for ionlists in self._listOfIonLists:
            currentLists = list()
            for ionList in ionlists:
                currentLists.append(sorted(ionList, key=lambda obj:obj.getMonoisotopic()))
            returnedLists.append(currentLists)
        return returnedLists