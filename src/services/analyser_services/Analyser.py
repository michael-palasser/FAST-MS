'''
Created on 10 Aug 2020

@author: michael
'''
from copy import deepcopy

import numpy as np

class Analyser(object):
    '''
    Class for analysing the ion list
    '''
    def __init__(self, ions, sequence, precCharge, modification):
        '''
        :param (list of FragmentIon) ions: observed ion (from intensityModeller)
        :param (list of str) sequence: list of building blocks in sequence of precursor
        :param (int) precCharge: charge of precursor
        :param (str) modification: modification of precursor
        '''
        self._ions = ions #sorted(_ions, key=lambda obj:(obj.type , obj.number))
        self._sequence = sequence
        self._precCharge = abs(precCharge)
        self._modification = modification
        #self._percentageDict = dict()

    def setIons(self, ions):
        self._ions = ions

    def calculateRelAbundanceOfSpecies(self):
        '''
        Calculates relative abundances of all fragment types including the precursor ion
        :return: (dict[str,float], dict[str,ndArray[float]]) relative fragment type abundances {type:abundance}, and
            relative fragment type abundances per cleavage site
        '''
        relAbundanceOfSpecies = dict()
        precInt = 0
        totalSum = 0
        precName= 'prec'
        """for type in fragmentList:
            relAbundanceOfSpecies[type] = 0"""
        for ion in self._ions:
            #if (ion.getScore() < 5) or (ion.getQuality()<0.3) or (ion.getNumber() == 0):
            relAb = ion.getRelAbundance()
            if ion.getNumber() == 0:
                precInt+=relAb
                precName = ion.getType()
            else:
                relAb /= 2
                if ion.getType() not in relAbundanceOfSpecies.keys():
                    relAbundanceOfSpecies[ion.getType()] = np.zeros(len(self._sequence))
                relAbundanceOfSpecies[ion.getType()][ion.getNumber()-1] += relAb
            totalSum += relAb
        totalDict = {precName:precInt/totalSum}
        totalDict.update({type: np.sum(val/totalSum) for type, val in relAbundanceOfSpecies.items()})
        return totalDict, relAbundanceOfSpecies

    def getModificationLoss(self):
        '''
        Calculates the proportion of modification loss of the precursor
        :return: (float) modification loss proportion
        '''
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


    def calculateOccupancies(self, interestingIons, modification=None, unImportantMods=None):
        '''
        Calculates the modified proportion for each fragment
        :param (list of str) interestingIons: fragment types which should be analysed
        :param (str) modification: name of the modification (optional)
        :param (list of str) unImportantMods: list of modifications which should not be used for the calculation (optional)
        :return: (dict[str,ndarray[float]], dict[str,ndarray[float,float]])
            dictionary {fragment type: proportions [fragment number x proportion]} of modified proportions for every
                (interesting) fragment type
            dictionary {fragment type: absolute values (2D array wiht columns: unmod. intensity per cleavage sit,
                mod. intensity per cl.site)} for every (interesting) fragment type
        '''
        if modification == "":
            return None
        elif modification is None:
            modification=self._modification
        absValues = dict()
        for ion in self._ions:
            if ion.getType() in interestingIons:
                if unImportantMods is not None:
                    if len([mod for mod in unImportantMods if mod in ion.getModification()])>0:
                        #print('not', ion.getName())
                        continue
                if ion.getType() not in absValues.keys():
                    absValues[ion.getType()] = np.zeros((len(self._sequence), 3))
                #if self._modification in ion.getModification():
                '''if ('+' in modification[1:]) or ('-' in modification[1:]):
                    modifications = ion.getModificationList()
                else:'''
                modifications = ion.getModification()
                print(ion.getName(),modifications, modification, modification in modifications)
                if modification in modifications:
                    absValues[ion.getType()][ion.getNumber() - 1] += \
                        np.array([ion.getRelAbundance(),
                                  ion.getRelAbundance() * self.getNrOfModifications(ion.getModification(), modification), 0])
                    #print('\t', ion.getName(), ion.getRelAbundance()*int(self.getNrOfModifications(ion.getModification())), 'mod')
                else:
                    absValues[ion.getType()][ion.getNumber() - 1] += \
                        np.array([ion.getRelAbundance(),0,0])
                    #print('\t', ion.getName(), ion.getRelAbundance())
        for key,vals in absValues.items():
            print('sequ.\t',key+'_free\t', key+'+'+modification)
            [print(str(i+1), '\t',val[0]-val[1], '\t', val[1]) for i,val in enumerate(vals)]
        return self.calculateProportions(absValues),absValues#dict()


    @staticmethod
    def getNrOfModifications(modificationString, modification):
        '''
        Determines how often an ion is modified
        :param (str) modificationString: (raw) modification string of an ion
        :return: (int) number of modifications of ion
        '''
        modification = modification[1:]
        nrOfModif = 1
        if modificationString[modificationString.find(modification) - 1].isdigit():
            nrOfModif = modificationString[modificationString.find(modification) - 1]
            if modificationString[modificationString.find(modification) - 2].isdigit():
                nrOfModif += (10 * modificationString[modificationString.find(modification) - 2])
        print(modificationString, nrOfModif)
        return int(nrOfModif)

    def calculateProportions(self, tempDict):
        '''
        Calculates the proportion of the interesting value (col 2)
        :param (dict[str,ndarray(dtype=[float,float,float])]) tempDict: dict {fragment type: array} with array columns:
            summed values, interesting values, 0
        :return: (dict[str,ndarray(dtype=[float,float,float])]) dict {fragment type: array} with array columns:
            summed values, interesting values, interesting proportion
        '''
        proportions = dict()
        for key,arr in tempDict.items():
            for row in arr:
                if row[0]!=0:
                    row[2] = row[1]/row[0]
                else:
                    row[2] = None
            proportions[key] = arr[:, 2]
        print('calculateProportions',proportions)
        return proportions

    def analyseCharges(self, interestingIons, reduced):
        '''
        Calculates the average charges and the charge ranges for each (interesting) fragment
        :param (list of str) interestingIons: fragment types which should be analysed
        :param (bool) reduced: if True abundances are divided by charge
        :return: (tuple[Dict[str:ndarray[float]], Dict[str:ndarray[float, float]]])
            dictionary with average charges {fragment type: charge array[fragment number x av.charge]}
            dictionary with min/max charges {fragment type: charge array[fragment number x (min.charge, max charge)]}
        '''
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
        '''
        For output of calculateOccupancies and analyseCharges to table
        :param (list of ndarray(dtype = float)) forwardVals: list (length = N_forw) of arrays with values of
            forward (e.g. a,b,c,..) fragment types
        :param (list of ndarray(dtype = float)) backwardVals: list (length = N_back) of arrays with values of
            backward (e.g. x,y,z,..) fragment types
        :return: (list of list[str,int,N_forw x float, N_back x float, int, str]) 2D list,
            4 + N_forw + N_back columns (building block (forw), number (forw), N_forw x val_frag_forw ,
                N_back x val_frag_back,  number (back), building block (back))
        '''
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


    def getSequenceCoverage(self, forwTypes):
        '''
        Determines the sequence coverage for each fragment type, for each direction (N-/5'-terminus etc.) and the
        global sequence coverage
        :param (list[str]) forwTypes: list of all forward (N-terminal, 5'-, ...) fragment types
        :return: (dict[str,ndArray[bool]], dict[str,float], ndArray[bool])
            coverages: dictionary (fragm. type:array) whereby each row index of the array represents the cleavage site -1
                and the boolean values states if a fragment was found at the corresponding site.
            calcCoverages: dictionary (fragm. type:value) whereby the values represent the proportion of coverage
            overall: 2D array (1.column = forward direction, 2.column = forward direction, 3.column = global) whereby
                each row index of the array represents the cleavage site -1 and the boolean values states if a fragment
                was found at the corresponding site.
        '''
        sequLength=len(self._sequence)
        coverages = {}
        calcCoverages = dict()
        overall = np.zeros((sequLength,3))
        arr = np.zeros(sequLength)
        for ion in self._ions:
            if ion.getNumber()==0:
                continue
            type = ion.getType()
            if type not in coverages.keys():
                coverages[type]= deepcopy(arr)
            row = ion.getNumber()-1
            if type not in forwTypes:
                row = sequLength-ion.getNumber()
            coverages[type][row] = 1
        #overall = np.zeros(sequLength)
        redSequLength = sequLength-1
        for type,val in coverages.items():
            calcCoverages[type] = np.sum(val)/(redSequLength)
        overall[:,0] = np.any([val.astype(bool) for type,val in coverages.items() if type in forwTypes], axis=0)
        calcCoverages['forward'] = np.sum(overall[:,0])/redSequLength
        overall[:,1] = np.any([val.astype(bool) for type,val in coverages.items() if type not in forwTypes], axis=0)
        calcCoverages['backward'] = np.sum(overall[:,1])/redSequLength
        overall[:,2] = np.any((overall[:,0],overall[:,1]), axis=0)
        calcCoverages['total'] = np.sum(overall[:,2])/sequLength
        for type in coverages.keys():
            if type in forwTypes:
                coverages[type][-1] = np.nan
            else:
                coverages[type][0] = np.nan
        overall[-1,0] = np.nan
        overall[0,1] = np.nan
        coveragesForw, coveragesBack = {},{}
        for key,val in coverages.items():
            if key in forwTypes:
                coveragesForw[key] = val
            else:
                coveragesBack[key] = val
        return (coveragesForw,coveragesBack), calcCoverages, overall

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

