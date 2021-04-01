'''
Created on 10 Aug 2020

@author: michael
'''
import numpy as np
from math import isnan

class Analyser(object):
    '''
    classdocs
    '''
    def __init__(self, ions, sequence, precCharge, modification):
        self._ions = ions #sorted(_ions, key=lambda obj:(obj.type , obj.number))
        self._sequence = sequence
        self._precCharge = abs(precCharge)
        self._modification = modification
        #self._percentageDict = dict()


    def setIons(self, ions):
        self._ions = ions

    def calculateRelAbundanceOfSpecies(self):
        relAbundanceOfSpecies = dict()
        totalSum = 0
        """for type in fragmentList:
            relAbundanceOfSpecies[type] = 0"""
        for ion in self._ions:
            if (ion.getScore() < 5) or (ion.getQuality()<0.3) or (ion.getNumber() == 0):
                if ion.getType() not in relAbundanceOfSpecies.keys():
                    relAbundanceOfSpecies[ion.getType()] = ion.getRelAbundance()
                else:
                    relAbundanceOfSpecies[ion.getType()] += ion.getRelAbundance()
                totalSum += ion.getRelAbundance()
        for species in relAbundanceOfSpecies:
            relAbundanceOfSpecies[species] /= totalSum
        return relAbundanceOfSpecies

    def getModificationLoss(self):
        if self._modification == "":
            return None
        modifiedSum = 0
        totalSum = 0
        for ion in self._ions:
            if (ion.getNumber()==0): #(ion._charge == self._precCharge) and
                if self._modification in ion.getModification():
                    modifiedSum += ion.getRelAbundance()
                totalSum += ion.getRelAbundance()
        return 1 - modifiedSum / totalSum


    def calculatePercentages(self, interestingIons, *args):
        if self._modification == "":
            return None
        temp = dict()
        for ion in self._ions:
            if ion.getType() in interestingIons:
                if args:
                    if len([mod for mod in args[0] if mod in ion.getModification()])>0:
                        #print('not', ion.getName())
                        continue
                if ion.getType() not in temp.keys():
                    temp[ion.getType()] = np.zeros((len(self._sequence), 3))
                if self._modification in ion.getModification():
                    temp[ion.getType()][ion.getNumber() - 1] += \
                        np.array([ion.getRelAbundance(),
                                  ion.getRelAbundance() * int(self.getNrOfModifications(ion.getModification())), 0])
                    #print('\t', ion.getName(), ion.getRelAbundance()*int(self.getNrOfModifications(ion.getModification())), 'mod')
                else:
                    temp[ion.getType()][ion.getNumber() - 1] += \
                        np.array([ion.getRelAbundance(),0,0])
                    #print('\t', ion.getName(), ion.getRelAbundance())
        for key,vals in temp.items():
            print('sequ.\t',key+'_free\t', key+'+'+self._modification)
            [print(str(i+1), '\t',val[0]-val[1], '\t', val[1]) for i,val in enumerate(vals)]
        return self.calculateProportions(temp)#dict()


    def getNrOfModifications(self, modificationString):
        nrOfModif = 1
        if modificationString[modificationString.find(self._modification) - 1].isdigit():
            nrOfModif = modificationString[modificationString.find(self._modification) - 1]
            if modificationString[modificationString.find(self._modification) - 2].isdigit():
                nrOfModif += (10 * modificationString[modificationString.find(self._modification) - 2])
        return nrOfModif

    def calculateProportions(self, tempDict):
        proportions = dict()
        for key,arr in tempDict.items():
            for row in arr:
                if row[0]!=0:
                    row[2] = row[1]/row[0]
                else:
                    row[2] = None
            proportions[key] = arr[:, 2]
        return proportions

    def getAvCharges(self, interestingIons, reduced):
        temp = dict()
        #redTemp = dict()
        chargeDict = dict()
        for ion in self._ions:
            if ion.getType() in interestingIons:
                if ion.getType() not in temp.keys():
                    temp[ion.getType()] = np.zeros((len(self._sequence), 3))
                    #chargeDict[ion.type] = len(self._sequence)*[[]]
                    chargeDict[ion.getType()] = [[] for i in range(len(self._sequence))]
                    #redTemp[ion.type] = np.zeros((len(self._sequence), 3))
                charge = ion.getCharge()
                chargeDict[ion.getType()][ion.getNumber() - 1].append(charge)
                if reduced:
                    temp[ion.getType()][ion.getNumber() - 1] += \
                                        np.array([ion.getRelAbundance(),ion.getRelAbundance() * charge, 0])
                else:
                    temp[ion.getType()][ion.getNumber() - 1] += np.array([ion.getIntensity(), ion.getIntensity() * charge, 0])
        avCharges = self.calculateProportions(temp)
        minMaxChargeDict = dict()
        for key,vals in chargeDict.items():
            minMaxCharges = []
            for charges in vals:
                if len(charges)>1:
                    minMaxCharges.append((min(charges),max(charges)))
                else:
                    minMaxCharges.append((np.nan, np.nan))
            minMaxChargeDict[key] = np.array(minMaxCharges)
            print(key,minMaxCharges)
        #reducedAvCharges = self.calculateProportions(redTemp)
        for key,vals in minMaxChargeDict.items():
            print(key)
            [print(i, val[0], val[1]) for i,val in enumerate(vals)]
        return avCharges, minMaxChargeDict

    def toTable(self, forwardVals, backwardVals):
        table = []
        for i, bb in enumerate(self._sequence[:-1]):
            table.append([bb, i+1])
        for vals in forwardVals:
            [table[i].append(val) for i, val in enumerate(vals[:-1])]
        for vals in backwardVals:
            [table[i].append(val) for i, val in enumerate(reversed(vals[:-1]))]
        for i, bb in enumerate(self._sequence[1:]):
            table[i]+=[len(self._sequence)-i-1,bb]
        return table

    '''def addColumn(self, table, vals):
        for i, val in enumerate(vals):
            if isnan(val):
                table[i].append('')
            else:
                table[i].append(val)
        return table'''

    #ToDo: Other __spectrum, ausslassen wenn -
    """def createPlot(self,nr_mod):
        forwLadderX = list()
        forwLadderY = list()
        backLadderX = list()
        backLadderY = list()
        sequLength = len(self._sequence)
        sortedPercentages = sorted(self._percentageDict.keys())
        for species in sortedPercentages:
            index = 0
            while index < sequLength:
                if species in ['a','b','c','d'] \
                        and self._percentageDict[species][index]!= '-':
                    forwLadderX.append(index+1)
                    forwLadderY.append(self._percentageDict[species][index])
                elif species in ['w','x','y','z'] \
                        and self._percentageDict[species][len(self._sequence) - index - 1] != '-':
                    backLadderX.append(index+1)
                    backLadderY.append(self._percentageDict[species][len(self._sequence) - index - 1])
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
        plt.show()"""

