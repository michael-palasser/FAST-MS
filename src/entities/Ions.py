'''
Created on 3 Jul 2020

@author: michael
'''
import math
import os

import numpy as np
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src import path
import pandas as pd

noiseLimit = ConfigurationHandlerFactory.getTD_SettingHandler().get('noiseLimit')

class Fragment(object):
    '''
    uncharged fragment
    '''

    def __init__(self, type, number, modification, formula, sequence, radicals):
        '''
        Constructor
        :param type: typically a, b, c, d, w, x, y or z (String)
        :param number: number in sequenceList (int)
        :param modification: +modification, +ligands and -loss (String)
        :param formula: Type MolecularFormula
        :param sequence: list of sequenceList of fragment
        '''
        self.type = type
        self.number = number
        self.modification = modification
        self.formula = formula
        self.sequence = sequence
        self.isotopePattern = None
        self.radicals = radicals

    def getName(self):
        if self.number == 0:
            return self.type + self.modification
        return self.type + format(self.number, "02d") + self.modification  # + "-" + self.loss

    def toString(self):
        return self.getName() + "\t\t" + self.formula.toString()

    def getNumberOfHighestIsotopes(self):
        '''
        Defines number of peaks to be searched for in first step of findPeaks function in SpectrumHandler
        :return: number of peaks
        '''
        abundances = self.isotopePattern['calcInt'] / self.isotopePattern[0]['calcInt']
        if len(abundances) < 3:
            return 1
        elif abundances[2] > 0.6:
            return 3
        elif abundances[1] > 0.3:
            return 2
        return 1


class FragmentIon(Fragment):
    '''
    charged fragment
    '''

    def __init__(self, fragment, charge, isotopePattern, noise):
        '''
        Constructor
        :param fragment: Type Fragment
        :param charge: int
        #ToDo: isotopePattern not compatible with Fragment isotope Pattern
        :param isotopePattern: structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param noise: noise level in the m/z area of the ion, calculated by calculateNoise function in SpectrumHandler
        '''
        super().__init__(fragment.type, fragment.number, fragment.modification,
                         fragment.formula, fragment.sequence, fragment.radicals,)
        self.charge = charge
        self.isotopePattern = isotopePattern
        self.intensity = 0
        self.error = 0
        self.quality = 0
        self.score = 0
        self.noise = noise
        self.comment = ""


    def toString(self):
        return str(round(self.getMonoisotopic(), 5)) + "\t\t" + str(self.charge) + "\t" + str(
            round(self.intensity)) + "\t" + '{:12}'.format(self.getName()) + "\t" + \
               str(round(self.error, 2)) + "\t\t" + str(round(self.quality, 2)) #+ "\t" + self.comment

    def getMonoisotopic(self):
        #return 500.
        return np.min(self.isotopePattern['m/z_theo']) * (1 + self.error * 10 ** (-6))  # np.min(self.isotopePattern['m/z'])

    def getScore(self):
        if self.quality > 1.5:
            print('warning:', round(self.quality, 2), self.getName())
            self.score = 10 ** 6
        else:
            self.score = math.exp(10 * self.quality) / 20 * self.quality * self.intensity / noiseLimit
        return self.score

    def getSignalToNoise(self):
        return self.intensity/self.noise

    def getRelAbundance(self):
        return self.intensity / self.charge

    def getValues(self):
        """formatInt = '{:12d}'
        if self.intensity >= 10 ** 13:
            lg10 = str(int(math.log10(self.intensity) + 1))
            formatInt = '{:' + lg10 + 'd}'
        return ['{:4.5f}'.format(round(self.getMonoisotopic(),5)),
                '{:2d}'.format(self.charge),
                formatInt.format(round(self.intensity)),
                self.getName(),
                '{:3.2f}'.format(round(self.error,2)),
                '{:6.1f}'.format(round(self.getSignalToNoise(),1)),
                '{:3.2f}'.format(round(self.quality,2))]"""
        """return [round(self.getMonoisotopic(),5), self.charge, round(self.intensity), self.getName(), round(self.error,2),
                round(self.getSignalToNoise(),1), round(self.quality,2)]#"""
        return [500, self.charge, round(self.intensity), self.getName(), round(self.error,2),
                round(self.getSignalToNoise(),1), round(self.quality,2)]

    """def getValueDict(self):
        return {'mz':500,'z':self.charge,'int':round(self.intensity),'name':self.getName(),'error':round(self.error, 2),
                'snr':round(self.getSignalToNoise(), 1),'qual':round(self.quality, 2),'com':self.comment}"""
    def getMoreValues(self):
        """return [round(self.getMonoisotopic(),5), self.charge, round(self.intensity), self.getName(), round(self.error,2),
                round(self.getSignalToNoise(),1), round(self.quality,2), round(self.getScore()),self.comment]#"""
        return [500, self.charge, round(self.intensity), self.getName(), round(self.error,2),
                round(self.getSignalToNoise(),1), round(self.quality,2), 2,self.comment]

    def getPeaks(self):
        peaks, indizes = [], []
        for i, peak in enumerate(self.isotopePattern):
            peaks.append((peak['m/z'], self.charge, round(peak['calcInt']), self.getName(), peak['error'],
                                peak['used']))
            indizes.append(i)
        return pd.DataFrame(data=peaks, columns=['mz', 'z', 'int', 'name', 'used'],
                            index=pd.MultiIndex.from_tuples(indizes))



class IntactIon(object):
    def __init__(self, name, modification, mz,theoMz, charge, intensity, nrOfModifications):
        '''

        '''
        self.name = name
        self.modification = modification
        self.mz = mz
        self.theoMz = theoMz
        self.charge = charge
        self.intensity = intensity
        self.nrOfModifications = nrOfModifications

    def calculateError(self):
        return (self.mz - self.theoMz) / self.theoMz * 10 ** 6

    def getName(self):
        return self.name + self.modification

    def toList(self):
        return [self.mz, self.charge, self.intensity, self.getName(), round(self.calculateError(), 2)]