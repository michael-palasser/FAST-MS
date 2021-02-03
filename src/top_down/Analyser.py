'''
Created on 10 Aug 2020

@author: michael
'''
import numpy as np
import pylab as plt

class Analyser(object):
    '''
    classdocs
    '''
    def __init__(self, listOfIons, sequence, precCharge, modification):
        self.listOfIons = sorted(listOfIons, key=lambda obj:(obj.type , obj.number))
        self.sequence = sequence
        self.precCharge = abs(precCharge)
        self.modification = modification
        self.percentageDict = dict()


    def calculateRelAbundanceOfSpecies(self):
        relAbundanceOfSpecies = dict()
        totalSum = 0
        """for type in fragmentList:
            relAbundanceOfSpecies[type] = 0"""
        for ion in self.listOfIons:
            if (ion.score < 5) or (ion.quality<0.3) or (ion.number == 0):
                if ion.type not in relAbundanceOfSpecies.keys():
                    relAbundanceOfSpecies[ion.type] = ion.getRelAbundance()
                else:
                    relAbundanceOfSpecies[ion.type] += ion.getRelAbundance()
                totalSum += ion.getRelAbundance()
        for species in relAbundanceOfSpecies:
            relAbundanceOfSpecies[species] /= totalSum
        return relAbundanceOfSpecies

    def getModificationLoss(self):
        if self.modification == "":
            return None
        modifiedSum = 0
        totalSum = 0
        for ion in self.listOfIons:
            if (ion.number==0): #(ion.charge == self.precCharge) and
                if self.modification in ion.modification:
                    modifiedSum += ion.getRelAbundance()
                totalSum += ion.getRelAbundance()
        return 1 - modifiedSum / totalSum


    def calculatePercentages(self, interestingIons):
        if self.modification == "":
            return None
        temp = dict()
        for ion in self.listOfIons:
            if ion.type[0] in interestingIons:
                if ion.type[0] not in temp:
                    temp[ion.type[0]] = np.zeros((len(self.sequence), 3))
                if self.modification in ion.modification:
                    temp[ion.type[0]][ion.number - 1] += \
                        np.array([ion.getRelAbundance(),
                                  ion.getRelAbundance()*int(self.getNrOfModifications(ion.modification)),0])
                else:
                    temp[ion.type[0]][ion.number - 1] += \
                        np.array([ion.getRelAbundance(),0,0])
        #returnedDict = dict()
        for key,arr in temp.items():
            for row in arr:
                if row[0]!=0:
                    row[2] = row[1]/row[0]
                else:
                    row[2] = None
            self.percentageDict[key] = arr[:,2]
        return self.percentageDict


    def getNrOfModifications(self, modificationString):
        nrOfModif = 1
        if modificationString[modificationString.find(self.modification)-1].isdigit():
            nrOfModif = modificationString[modificationString.find(self.modification)-1]
            if modificationString[modificationString.find(self.modification) - 2].isdigit():
                nrOfModif += (10 * modificationString[modificationString.find(self.modification) - 2])
        return nrOfModif

    #ToDo: Other __spectrum, ausslassen wenn -
    def createPlot(self,nr_mod):
        forwLadderX = list()
        forwLadderY = list()
        backLadderX = list()
        backLadderY = list()
        sequLength = len(self.sequence)
        sortedPercentages = sorted(self.percentageDict.keys())
        for species in sortedPercentages:
            index = 0
            while index < sequLength:
                if species in ['a','b','c','d'] \
                        and self.percentageDict[species][index]!='-':
                    forwLadderX.append(index+1)
                    forwLadderY.append(self.percentageDict[species][index])
                elif species in ['w','x','y','z'] \
                        and self.percentageDict[species][len(self.sequence)-index-1] != '-':
                    backLadderX.append(index+1)
                    backLadderY.append(self.percentageDict[species][len(self.sequence)-index-1])
                index += 1
        fig, ax1 = plt.subplots()
        ax1.plot(forwLadderX, forwLadderY, color='tab:blue', marker='v', label='c-fragments')
        ax1.grid()
        ax2 = ax1.twinx()
        plt.gca().invert_yaxis()
        ax2.plot(np.array(backLadderX) - 1, backLadderY, color='tab:green', marker='^', label='y-fragments')
        ax1.legend(loc=2)
        ax1.set_ylim([-0.05, nr_mod + 0.05])
        ax2.legend(loc=4)
        ax2.set_ylim([nr_mod + 0.05, -0.05])
        plt.rcParams['figure.figsize'] = 15, 4
        #locs, labels = plt.xticks()
        plt.xticks(np.arange(1, sequLength + 1, step=1))
        plt.show()

