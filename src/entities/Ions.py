'''
Created on 3 Jul 2020

@author: michael
'''
from math import exp

from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory

noiseLimit = ConfigurationHandlerFactory.getTD_SettingHandler().get('noiseLimit')

class Fragment(object):
    '''
    uncharged fragment
    '''

    def __init__(self, type, number, modification, formula, sequence, radicals):
        '''
        Constructor
        :param (str) type: typically a, b, c, d, w, x, y or z
        :param (int) number: length of fragment-sequence
        :param (str) modification: +modification, +ligands and -loss (String)
        :param (MolecularFormula) formula: MolecularFormula
        :param (list of str) sequence: list of building blocks
        '''
        self.type = type
        self.number = number
        self.modification = modification
        self.formula = formula
        self.sequence = sequence
        self.isotopePattern = None
        self.radicals = radicals


    def getType(self):
        return self.type
    def getNumber(self):
        return self.number
    def getModification(self):
        return self.modification
    def getFormula(self):
        return self.formula
    def getSequence(self):
        return self.modification
    def getIsotopePattern(self):
        return self.isotopePattern
    def getRadicals(self):
        return self.radicals


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

    def __init__(self, fragment, monoisotopic, charge, isotopePattern, noise):
        '''
        Constructor
        :param (Fragment) fragment
        :param (int) charge: abs of ion charge
        #ToDo: isotopePattern not compatible with Fragment isotope Pattern
        :param isotopePattern: structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param noise: noise level in the m/z area of the ion, calculated by calculateNoise function in SpectrumHandler
        '''
        super().__init__(fragment.type, fragment.number, fragment.modification,
                         fragment.formula, fragment.sequence, fragment.radicals,)
        self.monoisotopicRaw = monoisotopic
        self.charge = charge
        self.isotopePattern = isotopePattern
        self.intensity = 0
        self.error = 0
        self.quality = 0
        self.score = 0
        self.noise = noise
        self.comment = ""

    def getIntensity(self):
        return round(self.intensity)

    def setRemaining(self, intensity, error, quality, comment):
        self.intensity = intensity
        self.error = error
        self.quality = quality
        self.comment = comment
        self.getScore()

    def toString(self):
        return str(round(self.getMonoisotopic(), 5)) + "\t\t" + str(self.charge) + "\t" + str(
            round(self.intensity)) + "\t" + '{:12}'.format(self.getName()) + "\t" + \
               str(round(self.error, 2)) + "\t\t" + str(round(self.quality, 2)) #+ "\t" + self.comment

    def getMonoisotopic(self):
        #return np.min(self.isotopePattern['m/z_theo']) * (1 + self.error * 10 ** (-6))  # np.min(self.isotopePattern['m/z'])
        return self.monoisotopicRaw * (1 + self.error * 10 ** (-6))

    def getScore(self):
        if self.quality > 1.5:
            print('warning:', round(self.quality, 2), self.getName())
            self.score = 10 ** 6
        else:
            self.score = exp(10 * self.quality) / 20 * self.quality * self.intensity / noiseLimit
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
        return [round(self.getMonoisotopic(),5), self.charge, int(round(self.intensity)), self.getName(), round(self.error,2),
                round(self.getSignalToNoise(),1), round(self.quality,2)]#"""

    def getId(self):
        return self.getName()+', '+str(self.charge)

    def getMoreValues(self):
        return [round(self.getMonoisotopic(),5), self.charge, round(self.intensity), self.getName(), round(self.error,2),
                round(self.getSignalToNoise(),1), round(self.quality,2), round(self.getScore(),1),self.comment]

    def getPeaks(self):
        peaks = []
        for i, peak in enumerate(self.isotopePattern):
            peaks.append((peak['m/z'], self.charge, round(peak['calcInt']), peak['error'], peak['used']))
            #indizes.append(i)
        return peaks #pd.DataFrame(data=peaks, columns=['mz', 'z', 'int', 'name', 'error', 'used'])

    def getPeakValues(self):
        peaks = []
        for i, peak in enumerate(self.isotopePattern):
            peaks.append([round(peak['m/z'],5), round(peak['relAb']), round(peak['calcInt']), round(peak['error'],2),
                         peak['used']])
        return peaks

    def toStorage(self):
        return [self.type, self.number, self.modification, self.formula, self.sequence, self.radicals,
               self.monoisotopicRaw, self.charge, int(round(self.noise)), int(round(self.intensity)),
                float(self.error), self.quality, self.comment]
    '''def fromStorage(self):
        return [self.type, self.number, self.modification, self.formula, self.sequence, self.radicals,
               self.monoisotopicRaw, self.charge, self.noise, self.intensity,
                self.error, self.quality, self.comment]'''

    def peaksToStorage(self):
        peaks = []
        for i, peak in enumerate(self.isotopePattern):
            peaks.append([peak['m/z'], round(peak['relAb']), round(peak['calcInt']), float(peak['error']), int(peak['used'])])
        return peaks

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