'''
Created on 1 Oct 2020

@author: michael
'''

import numpy as np
from scipy.optimize import curve_fit
from src.entities.Ions import IntactIon as Ion

protonMass = 1.00727647

class Finder(object):
    '''

    '''
    def __init__(self, theoValues, configHandler):
        self.theoValues = theoValues
        self.mode = 1
        if configHandler.get('sprayMode') == 'negative':
            self.mode *= -1
        self.configHandler = configHandler
        self.data = list()
        self.foundIons = list()

    def readData(self,file):
        spectrum = list()
        for line in file:
            line = line.rstrip()
            if line.startswith('m/z'):
                if len(spectrum) != 0:
                    self.data.append(np.array(spectrum, dtype=
                        [('m/z', np.float64),('z',np.uint8),('relAb',np.float64)]))
                    spectrum = list()
            else:
                try:
                    lineList = line.split()
                    spectrum.append((lineList[0], lineList[1][:-1], lineList[2]))
                except:
                    print("problem in spectral pattern file: \nline", line)
                    continue
        self.data.append(np.array(spectrum, dtype=[('m/z', np.float64), ('z', np.uint8), ('relAb', np.float64)]))


    def getMz(self, mass, z):
        return mass / z + protonMass * self.mode


    @staticmethod
    def calculateError(value, theoValue):
        return (value - theoValue) / theoValue * 10 ** 6

    def getErrorLimit(self,k, d, mz):
        return k / 1000 * mz + d


    def findIons(self, k, d, flag):
        ionLists = list()
        for spectrum in self.data:
            ions = list()
            for modif, val in self.theoValues.items():
                mass = val[0]
                z = 1
                while True:
                    if self.getMz(mass,z) < self.configHandler.get('minMz'):
                        break
                    elif self.getMz(mass,z) < self.configHandler.get('maxMz'):
                        errorLimit = self.getErrorLimit(k, d, self.getMz(mass, z))
                        mask = np.where((abs(self.calculateError(spectrum['m/z'], self.getMz(mass,z))) < errorLimit)
                                        & (spectrum['z'] == z))
                        if (len(mask[0]) == 1):
                            ions.append(Ion(self.configHandler.get('sequName'),modif,spectrum[mask]['m/z'][0],self.getMz(mass,z),
                                            spectrum[mask]['z'][0],spectrum[mask]['relAb'][0],val[1]))

                        elif (flag == 1):
                            if len(mask[0]) == 0:
                                mask = np.where(
                                    (abs(self.calculateError(spectrum['m/z'], self.getMz(mass+1.00266, z)))
                                        < errorLimit) & (spectrum['z'] == z))
                                if len(mask[0]) == 0:
                                    mask = np.where(
                                        (abs(self.calculateError(spectrum['m/z'], self.getMz(mass-1.00266, z)))
                                            < errorLimit) & (spectrum['z'] == z))

                                if (len(mask[0]) == 1):
                                    ions.append(
                                        Ion(self.configHandler.get('sequName'), modif, spectrum[mask]['m/z'][0], self.getMz(mass, z),
                                            spectrum[mask]['z'][0], spectrum[mask]['relAb'][0], val[1]))
                            if len(mask[0]) > 1:
                                #print("more than one ion within error range:",spectralFile[mask])
                                ionPicked = 0
                                if errorLimit > 6.5:
                                    newMask = np.where(abs(self.calculateError(spectrum['m/z'],
                                                                               self.getMz(mass,z))) < 6.5)
                                    if (len(newMask[0]) == 1):
                                        ionPicked = 1
                                        ions.append(Ion(self.configHandler.get('sequName'),modif,spectrum[newMask]['m/z'][0],
                                                        self.getMz(mass,z),spectrum[newMask]['z'][0],
                                                        spectrum[newMask]['relAb'][0],val[1]))
                                    elif len(newMask[0]) > 1:
                                        mask = newMask
                                if ionPicked == 0:
                                    sortedArr = np.sort(spectrum[mask], order='relAb')
                                    ions.append(
                                        Ion(self.configHandler.get('sequName'), modif, sortedArr[-1]['m/z'], self.getMz(mass, z),
                                            sortedArr[-1]['z'], sortedArr[-1]['relAb'], val[1]))
                    z+=1
            ionLists.append(ions)
        return ionLists


    @staticmethod
    def fun_parabola(x,a,b,c):
        return a * x**2 + b * x + c


    def calibrate(self):
        calibrationValues = list()
        count = 1
        errorLimit = self.configHandler.get('errorLimitCalib')
        for ionList in self.findIons(0, errorLimit, 0):
            limit = errorLimit
            solution = [0,1,0]
            while limit >=10 :
                y = list()
                x = list()
                errorList = list()
                for ion in ionList:
                    calibratedX = self.fun_parabola(ion.mz, solution[0], solution[1], solution[2])
                    if abs(self.calculateError(calibratedX, ion.theoMz)) < limit:
                        y.append(ion.theoMz)
                        x.append(ion.mz)
                        errorList.append(abs(self.calculateError(calibratedX, ion.theoMz)))
                solution, pcov = curve_fit(self.fun_parabola, np.array(x), np.array(y))
                limit -= 10
                if np.average(np.array(errorList)) < 2.5:
                    break
            count += 1
            calibrationValues.append(solution)
        newData = list()
        for spectrum,solution in zip(self.data,calibrationValues):
            spectrum['m/z'] = self.fun_parabola(spectrum['m/z'], solution[0],solution[1],solution[2])
            newData.append(spectrum)
        self.data = newData

