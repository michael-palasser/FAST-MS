'''
Created on 3 Jul 2020

@author: michael
'''
import math
import os

import numpy as np
from src.ConfigurationHandler import ConfigHandler
from src import path

noiseLimit = ConfigHandler(os.path.join(path, "src","FragmentHunter","Repository","settings.json")).get('noiseLimit')

class Fragment(object):
    '''
    uncharged fragment
    '''

    def __init__(self, type, number, modification, formula, sequence):
        '''
        Constructor
        :param type: typically a, b, c, d, w, x, y or z (String)
        :param number: number in sequence (int)
        :param modification: +modification, +ligands and -loss (String)
        :param formula: Type MolecularFormula
        :param sequence: list of sequence of fragment
        '''
        self.type = type
        self.number = number
        self.modification = modification
        self.formula = formula
        self.sequence = sequence
        self.isotopePattern = None

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
        abundances = self.isotopePattern['int'] / self.isotopePattern[0]['int']
        if len(abundances) < 3:
            return 1
        elif abundances[2] > 0.6:
            return 3
        elif abundances[1] > 0.3:
            return 2
        return 1


class Ion(Fragment):
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
                         fragment.formula, fragment.sequence)
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
        return np.min(self.isotopePattern['m/z_theo']) * (
                    1 + self.error * 10 ** (-6))  # np.min(self.isotopePattern['m/z'])

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
