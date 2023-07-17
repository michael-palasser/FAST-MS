import numpy as np
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory

from src.services.assign_services.AbstractSpectrumHandler import calculateError, getMz


ionDType = np.dtype([('m/z', float), ('charge', int), ('name', 'U32'), ('m/z_theo', float), ('error', float),
                     ('I', np.uint64), ('S/N_SNAP', float), ('quality', float), ('type', 'U1'), ('number', int),
                     ('mono_m/z', float), ('S/N_mono', float), ('mono_error', float)])
newIonDType = np.dtype([('name', 'U32'),('charge',int), ('m/z', float), ('type', 'U1'), ('number', int),                   #ID
                                                ('I', np.uint64),('S/N', float), ('quality', float),               #FAST MS
                                                ('I_SNAP', np.uint64),('S/N_SNAP', float), ('quality_SNAP', float),     #SNAP
                                                ('I_mono', np.uint64),('S/N_mono', float), ('error_mono', float),                         #SumPeak
                                                ('score',float)])
forwardTypes = ['a', 'b', 'c', 'd']
backwardTypes = ['w', 'x', 'y', 'z']




class MD_Analyser(object):
    """
    Class for analysis of ion and peak lists in MS/MS MD.
    """
    def __init__(self,sequLength):
        self._sequLength = sequLength
        self._scoreDict = None
    
    def getScoreDict(self):
        return self._scoreDict

    def analyseData(self, data, forward=True):
        """
        For analysis of SNAP and SumPeak lists. Deprecated
        """
        bestIons, secondIons = [], []
        if forward:
            types = forwardTypes
        else:
            types = backwardTypes
        for i in range(1, self._sequLength):
            current = data[np.where(np.isin(data['type'], types) & (data['number'] == i))]
            length = len(current)
            if length == 0:
                bestIons.append(np.empty(1, dtype=ionDType)[0])
                secondIons.append(np.empty(1, dtype=ionDType)[0])
            elif length == 1:
                bestIons.append(current[0])
                secondIons.append(np.empty(1, dtype=ionDType)[0])
            else:
                current = np.sort(current, order='S/N_SNAP')
                best = current[-1]
                bestIons.append(best)
                current = np.sort(current, order='S/N_mono')
                if (current[-1]['name'] != best['name']) or (current[-1]['charge'] != best['charge']):
                    secondIons.append(current[-1])
                else:
                    secondIons.append(current[-2])
        return bestIons, secondIons
    
    def takeBest(self, bestForward, bestBackward):
        """
        Takes the best ion for each cleavage site. Deprecated
        """
        best = []
        for i in range(self._sequLength-1):
            forwardSN = self.getHighestSN(bestForward[i])
            backwardSN = self.getHighestSN(bestBackward[self._sequLength-i-2])
            if forwardSN > backwardSN:
                best.append(bestForward[i])
                #sns.append(forwardSN)
            else:
                best.append(bestBackward[self._sequLength-i-1])
                #sns.append(backwardSN)
        #sns = np.array(sns)
        #evaluation = (np.min(sns), np.percentile(sns,25), np.median(sns))
        return best#,evaluation
    
    @staticmethod
    def getHighestSN(ionVals):
        """
        Takes the highest S/N value from SNAP or SumPeak data
        :param (ndArray, dtype=newIonDType) ionVals: values of the ions
        :return: (float) highest S/N value
        """
        sn = ionVals['S/N_mono']
        if sn < ionVals['S/N_SNAP']:
            sn = ionVals['S/N_SNAP']
        return sn

    @staticmethod
    def evaluate(bestSNs):
        """
        Calculates the statistics
        :param (list[float]) bestSNs: S/N values of the selected ions
        :return: (float, float, float) minimum, first quartile, median
        """
        values = []
        for vals in bestSNs:
            bestVal = max(vals)
            if bestVal == "":
                bestVal =0
            values.append(bestVal)
        values = np.array(values)
        return np.min(values), np.percentile(values,25), np.median(values)


    @staticmethod
    def ionsToArray(ionDict, ionSnapDict, ionPeakDict):
        """
        Makes an array of the relevant values of the found ions
        :param (dict[string, list[FragmenIon]]) ionDict: Found ions
        :param (dict[float] list[ndArray] ionSnapDict: Values of the assigned ions in the SNAP list
        :param (dict[float], list[ndArray]) ionPeakDict: Values of the assigned ions in the SumPeak list
        :return: (ndArray) combined ion values
        """
        ionList = []
        for ionHash in ionDict.keys():
            ion = ionDict[ionHash]
            peakVals = ionPeakDict[ionHash]
            #ToDo: What if not found
            snapI, snapSNR, snapQ = 0,0,0
            if ionHash in ionSnapDict.keys():
                snapIon = ionSnapDict[ionHash]
                snapI, snapSNR, snapQ = snapIon.getIntensity(), snapIon.getSNR(), snapIon.getQual()
            error = np.around(calculateError(peakVals['m/z'], ion.getTheoMz()),2)
            if peakVals['m/z'] ==0:
                error =0
            if ion.getModification() == '':
                ionList.append((ion.getName(), ion.getCharge(), ion.getMonoisotopic(), ion.getType()[0], ion.getNumber(),                                                 #ID
                            ion.getIntensity(), ion.getSignalToNoise(),  1-ion.getQuality(),                              #FAST MS
                            snapI, snapSNR, snapQ,                             #SNAP
                            peakVals["I"],peakVals["S/N"], error,     #SumPeak
                            0.))
        return np.array(ionList,dtype=newIonDType)


    def sortIons(self, ionDict, ionSnapDict, ionPeakDict, precursorRegion):
        """
        Makes an array of the relevant values of the found ions and calculates a score for all ions per cleavage site.
        The ions are sorted according to the score
        :param (dict[string, list[FragmenIon]]) ionDict: Found ions
        :param (dict[float] list[ndArray] ionSnapDict: Values of the assigned ions in the SNAP list
        :param (dict[float], list[ndArray]) ionPeakDict: Values of the assigned ions in the SumPeak list
        :param (float) precursorRegion: m/z of the precursor
        :return: (list[ndArray], ndArray) list of found ions per cleavage site, best ions according to score
        """
        arr = self.ionsToArray(ionDict, ionSnapDict, ionPeakDict)
        arrList = []
        self._scoreDict = ConfigurationHandlerFactory.getMDScoresHandler().getAll()
        for row in arr:
            if self.getHighestSN(row)<10:
                row['score'] += self._scoreDict['pen_S/N']
            if np.abs(row['error_mono'])>5:
                row['score'] += self._scoreDict['pen_error']
            if precursorRegion-5 < row['m/z'] < precursorRegion+5:
                row['score'] += self._scoreDict['pen_prec']
        for i_seq in range(1,self._sequLength):
            unsorted = arr[np.where((np.isin(arr['type'], forwardTypes) & (arr['number'] == i_seq)) |                   #forward
                                   (np.isin(arr['type'], backwardTypes) & (arr['number'] == self._sequLength-i_seq)))]  #backward
            for column, reward in self._scoreDict.items():
                if reward<0:
                    continue
                curSorted = np.sort(unsorted, order=column)[::-1]
                for i, row in enumerate(curSorted):
                    for j, row_unsorted in enumerate(unsorted):
                        if row_unsorted['name'] == row['name'] and (row_unsorted['charge'] == row['charge']):
                            unsorted[j]['score'] += (reward/2**i)
            arrList.append(np.sort(unsorted,order="score")[::-1])

        sortedArrList = []
        for i,values in enumerate(arrList):
            cleavageSite = []
            for row in values:
                ion = ionDict[(row['name'],row['charge'])]
                cleavageSite.append((i+1,row['m/z'], row['charge'], int(round(row['I'])), str(row['name']), ion.getError(), 
                                     row['S/N'], row['quality'], str(ion.getComment()), row['I_SNAP'], row['S/N_SNAP'], 
                                     row['quality_SNAP'], row['I_mono'], row['S/N_mono'], row['score']))
            if len(values)==0:
                cleavageSite.append((i+1,"", "", 0, "", "", 0, "", "", 0, 0, "", 0, 0, ""))
            sortedArrList.append(cleavageSite)
        best = [vals[0] for vals in sortedArrList]
        #print(best)
        return sortedArrList, best

        
