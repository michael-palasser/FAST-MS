'''
Created on 2 Oct 2020

@author: michael
'''

import numpy as np

class IntactAnalyser(object):
    '''

    '''
    def __init__(self,ionLists):
        self.ionLists = ionLists
        self.minCharge = 250
        self.maxCharge = 0

    def calculateAvChargeAndError(self):
        '''value changed if reduced intensities are used'''
        averageCharges = list()
        averageErrors = list()
        for ionList in self.ionLists:
            chargeSum = 0
            sumInt = 0
            errorSum = 0
            notCounted = 0
            for ion in ionList:
                sumInt += ion.getIntensity()
                if abs(ion.calculateError()) < 30:
                    errorSum += ion.calculateError()
                else:
                    notCounted += 1
                chargeSum += ion.getCharge() *ion.getIntensity()
                charge = ion.getCharge()
                if charge < self.minCharge:
                    self.minCharge = charge
                if charge > self.maxCharge:
                    self.maxCharge = charge
            averageCharges.append(chargeSum/sumInt)
            averageErrors.append(errorSum/(len(ionList)-notCounted))
        return averageCharges, averageErrors

    def calculateAverageModification(self):
        averageModifications = list()
        for ionList in self.ionLists:
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
        return averageModifications

    def makeChargeArray(self):
        arr = np.zeros((self.maxCharge - self.minCharge + 1, 2))
        for i in range(self.maxCharge - self.minCharge + 1):
            arr[i][0] = self.minCharge + i
        return arr

    def calculateModifications(self):
        modificationsInSpectra = list()
        #avOfModInSpectra = list()
        for ionList in self.ionLists:
            modifications = dict()
            intensitiesPerCharge = self.makeChargeArray()
            for ion in ionList:
                if ion.getModification() not in modifications:
                    modifications[ion.getModification()] = self.makeChargeArray()
                modifications[ion.getModification()][ion.getCharge()-self.minCharge][1] = ion.getIntensity()
                intensitiesPerCharge[ion.getCharge()-self.minCharge][1] += ion.getIntensity()
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
        return modificationsInSpectra

    def getIonList(self):
        returnedLists = list()
        for ionList in self.ionLists:
            returnedLists.append(sorted(ionList,key=lambda obj:obj.getMz()))
        return returnedLists