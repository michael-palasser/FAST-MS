'''
Created on 3 Jul 2020

@author: michael
'''
from math import exp
#from numpy import array, dtype

from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory

noiseLimit = ConfigurationHandlerFactory.getTD_SettingHandler().get('noiseLimit')

class Fragment(object):
    '''
    Uncharged fragment
    '''

    def __init__(self, type, number, modification, formula, sequence, radicals):
        '''
        :param (str) type: typically a, b, c, d, w, x, y or z
        :param (int) number: length of fragment-sequence
        :param (str) modification: +modification, +ligands and -loss
        :param (MolecularFormula) formula: MolecularFormula
        :param (list [str]) sequence: list of building blocks
        '''
        self._type = type
        self._number = number
        self._modification = modification
        self._formula = formula
        self._sequence = sequence
        self._isotopePattern = None
        self._radicals = radicals


    def getType(self):
        return self._type
    def getNumber(self):
        return self._number
    def getModification(self):
        return self._modification

    def getFormula(self):
        return self._formula
    def setFormula(self, formula):
        self._formula = formula

    def getSequence(self):
        return self._modification
    def setSequence(self, sequence):
        self._sequence = sequence

    def getIsotopePattern(self):
        return self._isotopePattern
    def setIsotopePattern(self, isotopePattern):
        self._isotopePattern = isotopePattern
    def setIsotopePatternPart(self, col, vals):
        '''
        Sets only 1 column of the isotope pattern
        :param col: index of column
        :param vals: values
        '''
        self._isotopePattern[col] = vals

    def getRadicals(self):
        return self._radicals

    def getName(self):
        if self._number == 0:
            return self._type + self._modification
        return self._type + format(self._number, "02d") + self._modification  # + "-" + self.loss

    def toString(self):
        return self.getName() + "\t\t" + self._formula.toString()

    def getNumberOfHighestIsotopes(self):
        '''
        Defines number of peaks to be searched for in first step of findPeaks function in SpectrumHandler
        :return: number of peaks
        '''
        abundances = self._isotopePattern['calcInt'] / self._isotopePattern[0]['calcInt']
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
        :param (int) charge: abs of ion _charge
        :param (ndarray) isotopePattern: structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param (float) noise: noise level in the m/z area of the ion, calculated by calculateNoise function in SpectrumHandler
        '''
        super().__init__(fragment._type, fragment._number, fragment._modification,
                         fragment._formula, fragment._sequence, fragment._radicals, )
        self._monoisotopicRaw = monoisotopic
        self._charge = charge
        self._isotopePattern = isotopePattern
        self._intensity = 0
        self._error = 0
        self._quality = 0
        self._score = 0
        self._noise = noise
        self._comment = ""

    def getCharge(self):
        return self._charge

    def getIntensity(self):
        return self._intensity
    def setIntensity(self, intensity):
        self._intensity = int(round(intensity))

    def getError(self):
        return self._error
    def setError(self, error):
        self._error = error

    def getQuality(self):
        return self._quality
    def setQuality(self, quality):
        self._quality = quality
        self.calcScore()

    def getScore(self):
        return self._score

    def calcScore(self):
        if self._quality > 1.5:
            print('warning:', round(self._quality, 2), self.getName())
            self._score = 10 ** 6
        else:
            self._score = exp(10 * self._quality) / 20 * self._quality * self._intensity / noiseLimit
        # return self.score

    def getNoise(self):
        return self._noise
    def getComment(self):
        return self._comment
    def addComment(self, comment):
        self._comment += comment + ','

    def setRemaining(self, intensity, error, quality, comment):
        '''
        Setter method for all values which are not already set by the constructor
        :param (float) intensity:
        :param (float) error:
        :param (float) quality:
        :param (str) comment:
        '''
        self._intensity = int(intensity)
        self._error = error
        self.setQuality(quality)
        self._comment = comment

    def setIsoIntQual(self, isotopePattern, intensity, quality):
        self._isotopePattern = isotopePattern
        self._intensity = int(round(intensity))
        self._quality = quality

    def toString(self):
        '''
        For printing purposes
        :return: (str)
        '''
        return str(round(self.getMonoisotopic(), 5)) + "\t\t" + str(self._charge) + "\t" + str(
            round(self._intensity)) + "\t" + '{:12}'.format(self.getName()) + "\t" + \
               str(round(self._error, 2)) + "\t\t" + str(round(self._quality, 2)) #+ "\t" + self._comment

    def getMonoisotopic(self):
        '''
        Calculates the (observed) monoisotopic m/z from the theoretical and the error of the ion
        :return: (float) monoisotopic m/z
        '''
        #return np.min(self.isotopePattern['m/z_theo']) * (1 + self.error * 10 ** (-6))  # np.min(self.isotopePattern['m/z'])
        return self._monoisotopicRaw * (1 + self._error * 10 ** (-6))

    def getSignalToNoise(self):
        return self._intensity / self._noise

    def getRelAbundance(self):
        return self._intensity / self._charge

    def getValues(self):
        '''
        Getter of ion values for IonTableWidget
        '''
        return [round(self.getMonoisotopic(),5), self._charge, int(round(self._intensity)), self.getName(), round(self._error, 2),
                round(self.getSignalToNoise(),1), round(self._quality, 2)]#"""

    def getId(self):
        return self.getName()+', '+str(self._charge)

    def getHash(self):
        return (self.getName(),self._charge)

    def getMoreValues(self):
        '''
        Getter of ion values
        '''
        return self.getValues()+[round(self.getScore(), 1), self._comment]

    '''def getPeaks(self):
        peaks = []
        for i, peak in enumerate(self.isotopePattern):
            peaks.append((peak['m/z'], self._charge, round(peak['calcInt']), peak['error'], peak['used']))
            #indizes.append(i)
        return peaks''' #pd.DataFrame(data=peaks, columns=['mz', 'z', 'int', 'name', 'error', 'used'])

    '''def getPeakValues(self):
        peaks = []
        for i, peak in enumerate(self._isotopePattern):
            peaks.append([round(peak['m/z'],5), round(peak['relAb']), round(peak['calcInt']), round(peak['error'],2),
                         peak['used']])
        print(self._isotopePattern, self._isotopePattern.dtype)
        return self._isotopePattern'''

    def toStorage(self):
        '''
        To save an ion in database
        :return: list of values
        '''
        return [self._type, self._number, self._modification, self._formula, self._sequence, self._radicals,
                self._monoisotopicRaw, self._charge, int(round(self._noise)), int(round(self._intensity)),
                float(self._error), self._quality, self._comment]
    '''def fromStorage(self):
        return [self.type, self.number, self.modification, self.formula, self.sequence, self.radicals,
               self._monoisotopicRaw, self._charge, self.noise, self.intensity,
                self.error, self.quality, self._comment]'''

    def peaksToStorage(self):
        '''
        To save peaks in database
        :return: 2d list of peak values
        '''
        peaks = []
        for i, peak in enumerate(self._isotopePattern):
            peaks.append([peak['m/z'], round(peak['relAb']), round(peak['calcInt']), float(peak['error']), int(peak['used'])])
        return peaks

class IntactIon(object):
    def __init__(self, name, modification, mz,theoMz, charge, intensity, nrOfModifications):
        '''
        :param (str) name: name of the ion
        :param (str) modification: modification/ligand/loss
        :param (float) mz: monoisotopic m/z
        :param (float) theoMz: theoretical (calculated) m/z
        :param (int) charge: charge
        :param (float) intensity: intensity or relative abundance
        :param (int) nrOfModifications: nr. of modifications on ion
        '''
        self._sequName = name
        self._modification = modification
        self._mz = mz
        self._theoMz = theoMz
        self._charge = charge
        self._intensity = intensity
        self._nrOfModifications = nrOfModifications

    def getModification(self):
        return self._modification
    def getName(self):
        return self._sequName + self._modification
    def getMz(self):
        return self._mz
    def getTheoMz(self):
        return self._theoMz
    def getCharge(self):
        return self._charge
    def getIntensity(self):
        return self._intensity
    def getNrOfModifications(self):
        return self._nrOfModifications

    def calculateError(self):
        return (self._mz - self._theoMz) / self._theoMz * 10 ** 6

    def toList(self):
        return [self._mz, self._charge, self._intensity, self.getName(), round(self.calculateError(), 2)]