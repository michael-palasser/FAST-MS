'''
Created on 2 Oct 2020

@author: michael
'''

import numpy as np

class IntactAnalyser(object):
    '''
    Responsible for analysing lists of observed ion
    '''
    def __init__(self, listOfIonLists):
        '''
        :param (list[list[list[SimpleIntactIon]]]) listOfIonLists: nested lists of IntactIons (ions in each spectrum in each file)
        '''
        self._listOfIonLists = listOfIonLists
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
            print(ionlists)
            averageCharges, averageErrors, stddevOfErrors = [], [], []
            for ionList in ionlists:
                print('hey',ionList)
                #exclude SNAP misassignments
                errors = np.array([ion.getError() for ion in ionList if abs(ion.getError()) < 30])
                averageErrors.append(np.average(errors))
                stddevOfErrors.append(np.std(errors))
                intensities = np.array([(ion.getIntensity(),ion.getCharge()) for ion in ionList])
                averageCharges.append((np.sum(intensities[:,0]*intensities[:,1])/np.sum(intensities[:,0]),
                                       np.sum(intensities[:,0])/np.sum(intensities[:,0]/intensities[:,1])))
                minCharge, maxCharge = np.min(intensities[:,1]), np.max(intensities[:,1])
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
        Calculates average numbers of modifications for each charge of each spectrum in each file
        :return: (list[list[dict[int,float]]]) list of {charge:av.modification}
        '''
        listOfAverageModifications = []
        for ionlists in self._listOfIonLists:
            averageModifications = list()
            for ionList in ionlists:
                averageModificationPerZ = dict()
                for ion in ionList:
                    charge = ion.getCharge()
                    intensity = ion.getIntensity()
                    if charge in averageModificationPerZ:
                        averageModificationPerZ[charge] += np.array([float(ion.getNrOfModifications()) * intensity, intensity])
                    else:
                        averageModificationPerZ[charge] = np.array([float(ion.getNrOfModifications()) * intensity, intensity])
                for z,val in averageModificationPerZ.items():
                    averageModificationPerZ[z] = val[0]/val[1]  #ToDo: check if robust
                averageModifications.append(averageModificationPerZ)
            listOfAverageModifications.append(averageModifications)
        return listOfAverageModifications

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
        Calculates the abundance of each modification for each charge state in each spectrum in each file
        :return: (list[list[dict[str,ndarray(dtype=(int,float)])]]) list of dicts {modification: array([charge, percentage])}
        '''
        listOfModificationsInSpectra = []
        for ionlists in self._listOfIonLists:
            modificationsInSpectra = list()
            #avOfModInSpectra = list()
            for ionList in ionlists:
                modifications = dict()
                intensitiesPerCharge = self.makeChargeArray()
                for ion in ionList:
                    if ion.getModification() not in modifications:
                        modifications[ion.getModification()] = self.makeChargeArray()
                    modifications[ion.getModification()][ion.getCharge() - self._minCharge][1] = ion.getIntensity()
                    intensitiesPerCharge[ion.getCharge() - self._minCharge][1] += ion.getIntensity()
                nonZero = np.where(intensitiesPerCharge[:,1] != 0)
                dataLength = len(intensitiesPerCharge[nonZero])
                #averageOfModifications = dict()
                modifications2 = dict()
                for mod,arr in modifications.items():
                    newArr = np.zeros((dataLength,2))
                    for i in range(dataLength):
                        newArr[i] = [intensitiesPerCharge[nonZero][i,0],
                                     arr[nonZero][i,1]/intensitiesPerCharge[nonZero][i,1]]
                    #averageOfModifications[mod] = np.average(newArr[:,1])
                    modifications2[mod] = newArr
                modificationsInSpectra.append(modifications2)
                #avOfModInSpectra.append(averageOfModifications)
            listOfModificationsInSpectra.append(modificationsInSpectra)
        return listOfModificationsInSpectra

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