'''
Created on 3 Jul 2020

@author: michael
'''
from abc import ABC
import numpy as np
from src.services.FormulaFunctions import eMass, protMass


class Ion(ABC):
    '''
    Abstract superclass for ions
    '''
    def getName(self):
        pass

    def getCharge(self):
        return self._charge
    def setCharge(self, charge):
        self._charge = charge

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

    def getScore(self):
        return self._score
    def setScore(self, score):
        self._score = score


    def getNeutral(self, mz, mode):
        return (mz - mode *protMass) * self._charge - self._radicals*(protMass+eMass)

    def getMolecularMass(self, mode):
        return self.getNeutral(self.getMonoisotopic(),mode)

    def getAverageMass(self, mode):
        avMass = np.sum(self._isotopePattern['m/z']*self._isotopePattern['calcInt'])/np.sum(self._isotopePattern['calcInt'])
        if np.isnan(self.getNeutral(avMass,mode)):
            print(self._isotopePattern, avMass, self._isotopePattern['calcInt'])
        return self.getNeutral(avMass,mode)

    def getNoise(self):
        return self._noise
    def setNoise(self,noise):
        self._noise = noise
    def getComment(self):
        return self._comment
    def setComment(self, comment):
        self._comment = comment
    def addComment(self, comment):
        self._comment += comment + ','


    def setIsoIntQual(self, isotopePattern, intensity, quality):
        self._isotopePattern = isotopePattern
        self._intensity = int(round(intensity))
        if quality is None:
            quality = 1.
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
        if self._noise != 0:
            """signal = 0
            for val in self._isotopePattern['calcInt']:
                if val> self._noise:
                    signal += val-self._noise
            return signal / self._noise"""
            return self._intensity / (self._noise)#*len(self._isotopePattern))
        else:
            print(self.getName(), self._intensity, self._noise)
            return np.nan

    def getRelAbundance(self):
        return self._intensity / self._charge

    def getValues(self):
        '''
        Getter of ion values for IonTableWidget
        '''
        if self._quality is None:
            print("reset quality", self.getName())
            self._quality = 1
            
        return [round(self.getMonoisotopic(),5), self._charge, int(round(self._intensity)), self.getName(), round(self._error, 2),
                round(self.getSignalToNoise(),1), round(self._quality, 2)]#"""

    def getId(self):
        return self.getName() +', '+str(self._charge)

    def getHash(self):
        return (self.getName(),self._charge)

    def getMoreValues(self):
        '''
        Getter of ion values
        '''
        try:
            return self.getValues()+[round(self.getScore(), 1), self._comment]
        except TypeError:
            return self.getValues()+[20.0, self._comment]


    def toStorage(self):
        '''
        To save an ion in database
        :return: list of values
        '''
        return [self._type+self._modification, self._number, self._formula, self._monoisotopicRaw, self._charge,
                int(round(self._noise)), self._quality, self._comment]

    def peaksToStorage(self):
        '''
        To save peaks in database
        :return: 2d list of peak values
        '''
        peaks = []
        for i, peak in enumerate(self._isotopePattern):
            peaks.append([peak['m/z'], round(peak['I']), round(peak['calcInt']), float(peak['error']), int(peak['used'])])
        return peaks


    def setIsotopePatternPart(self, col, vals):
        '''
        Sets only 1 column of the isotope pattern
        :param col: index of column
        :param vals: values
        '''
        self._isotopePattern[col] = vals


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
        :param (int) radicals: no. of radicals
        '''
        self._type = type
        self._number = number
        self._modification = modification
        self._formula = formula
        self._sequence = sequence
        self._radicals = radicals
        self._isotopePattern = None


    def getType(self):
        return self._type
    def getNumber(self):
        return self._number
    def getModification(self):
        return self._modification

    def getModificationList(self):
        modifications = []
        for str1 in self._modification.split('+'):
            for mod in ('+'+str1).split('-'):
                if mod[0]=='+':
                    newMod = mod
                else:
                    newMod = '-'+mod
                if len(newMod)>1:
                    modifications.append(newMod)
        return modifications

    def getFormula(self):
        return self._formula
    def setFormula(self, formula):
        self._formula = formula

    def getSequence(self):
        return self._sequence
    def setSequence(self, sequence):
        self._sequence = sequence

    def getIsotopePattern(self):
        return self._isotopePattern
    def setIsotopePattern(self, isotopePattern):
        self._isotopePattern = isotopePattern
    """def setIsotopePatternPart(self, col, vals):
        '''
        Sets only 1 column of the isotope pattern
        :param col: index of column
        :param vals: values
        '''
        self._isotopePattern[col] = vals"""

    def getRadicals(self):
        return self._radicals

    def getName(self, html=False):
        if self._number == 0:
            return self._type + self._modification
        elif html:
            if self._modification=="":
                return self._type + "<sub>"+str(self._number)+"</sub>"
            else:
                return "["+self._type + "<sub>"+str(self._number)+"</sub>" + self._modification+"]"
        return self._type + format(self._number, "02d") + self._modification  # + "-" + self.loss

    def setType(self, type):
        self._type = type

    def toString(self):
        return self.getName() + "\t\t" + self._formula.toString()

    def getNumberOfHighestIsotopes(self):
        '''
        Defines number of peaks to be searched for in first step of findIons function in SpectrumHandler
        :return: (int) number of peaks
        '''
        abundances = self._isotopePattern['calcInt'] / self._isotopePattern[0]['calcInt']
        if len(abundances) < 3:
            return 1
        elif abundances[2] > 0.6:
            return 3
        elif abundances[1] > 0.3:
            return 2
        return 1

    def getMonoisotopicMass(self):
        if self._isotopePattern is None:
            self._isotopePattern = self.getFormula().calculateMonoIsotopic()
            return self._isotopePattern
        elif isinstance(self._isotopePattern, float):
            return self._isotopePattern
        return self._isotopePattern['m/z'][0]

class FragmentIon(Fragment, Ion):
    '''
    charged fragment
    '''
    def __init__(self, fragment, monoisotopic, charge, isotopePattern, noise, quality=None, calculate=False,
                 comment='', score=None):
        '''
        Constructor
        :param (Fragment) fragment
        :param (int) charge: abs of ion _charge
        :param (ndarray) isotopePattern: structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param (float) noise: noise level in the m/z area of the ion, calculated by calculateNoise function in SpectrumHandler
        :param (float) quality: quality error of the ion (optional)
        :param (bool) calculate: intensity, error and score are calculated if true (for loading old search) (optional)
        :param (str) comment: comment of ion (optional)
        '''
        super().__init__(fragment._type, fragment._number, fragment._modification,
                         fragment._formula, fragment._sequence, fragment._radicals, )
        self._monoisotopicRaw = monoisotopic
        self._charge = charge
        self._isotopePattern = isotopePattern
        self._quality = quality
        self._score = score
        if calculate:
            self._intensity= np.sum(self._isotopePattern['calcInt'])
            self._error = np.average(self._isotopePattern['error'][np.where(self._isotopePattern['I'] != 0 &
                                                                            self._isotopePattern['used'])])
        else:
            self._intensity = 0
            self._error = 0
        self._noise = noise
        self._comment = comment

    def getTheoMz(self):
        return self._monoisotopicRaw



class IntactNeutral(object):
    '''
    Class which represents a neutral intact species
    '''
    def __init__(self, sequName, modification, nrOfModifications, formula, radicals):
        '''
        :param (str) sequName: name of the sequence
        :param (str) modification: modification/ligand/loss/adduct
        :param (int) nrOfModifications: no. of modifications on ion
        :param (MolecularFormula) formula: molecular formula of the species
        :param (int) radicals: no. of radicals on species
        '''
        self._name = sequName
        self._modification = modification
        self._nrOfModifications = nrOfModifications
        self._formula = formula
        self._radicals = radicals
        self._isotopePattern = None
        self._monoisotopicRaw = None

    def getUnmodifiedName(self):
        return self._name
    def getModification(self):
        return self._modification
    def getName(self):
        return self._name + self._modification
    def getNrOfModifications(self):
        return self._nrOfModifications
    def getFormula(self):
        return self._formula
    def getIsotopePattern(self):
        return self._isotopePattern
    def getRadicals(self):
        return self._radicals
    def setIsotopePattern(self, isotopePattern):
        self._isotopePattern = isotopePattern
    def getMonoisotopicMass(self):
        if self._monoisotopicRaw is None:
            self._monoisotopicRaw = self._formula.calculateMonoIsotopic()
        return self._monoisotopicRaw

    def getNumberOfHighestIsotopes(self):
        '''
        Defines number of peaks to be searched for in first step of findIons function in SpectrumHandler
        :return: (int) number of peaks
        '''
        abundances = self._isotopePattern['calcInt'] / self._isotopePattern[0]['calcInt']
        if len(abundances) < 3:
            return 1
        elif abundances[2] > 0.6:
            return 3
        elif abundances[1] > 0.3:
            return 2
        return 1

class IntactIon(IntactNeutral, Ion):
    '''
    Ion for intact ion search
    '''
    def __init__(self, neutral, monoisotopic, charge, isotopePattern, noise, quality=None, calculate=False, comment='',
                 score=None):
        '''

        :param (IntactNeutral) neutral: neutral version of ion
        :param (float) monoisotopic: theoretical monoisotopic m/z
        :param (int) charge: abs of ion _charge
        :param (ndarray) isotopePattern: structured numpy-array: [m/z, intensity, m/z_theo, calcInt, error (ppm), used (for modelling)]
        :param (float) noise: noise level in the m/z area of the ion, calculated by calculateNoise function in SpectrumHandler
        :param (float) quality: quality error of the ion (optional)
        :param (bool) calculate: intensity, error and score are calculated if true (for loading old search) (optional)
        :param (str) comment: comment of ion (optional)
        '''
        super(IntactIon, self).__init__(neutral.getUnmodifiedName(), neutral.getModification(),
                                        neutral.getNrOfModifications(), neutral.getFormula(), neutral.getRadicals())
        self._monoisotopicRaw = monoisotopic
        self._charge = charge
        self._isotopePattern = isotopePattern
        self._quality = quality
        if calculate:
            self._intensity= np.sum(self._isotopePattern['calcInt'])
            self._error = np.average(self._isotopePattern['error'][np.where(self._isotopePattern['I'] != 0 &
                                                                            self._isotopePattern['used'])])
            self._score = score
        else:
            self._intensity = 0
            self._error = 0
            self._score = 0
        self._noise = noise
        self._comment = comment


class SimpleIntactIon(IntactNeutral, Ion):
    '''
    Simplified ion for assignment in intact ion list
    '''
    def __init__(self, sequName, modification, mz,theoMz, charge, intensity, nrOfModifications, radicals):
        '''
        :param (str) name: name of the ion
        :param (str) modification: modification/ligand/loss
        :param (float) mz: monoisotopic m/z
        :param (float) theoMz: theoretical (calculated) m/z
        :param (int) charge: charge
        :param (float) intensity: intensity
        :param (int) nrOfModifications: no. of modifications on ion
        :param (int) radicals: no. of radicals on ion
        '''
        super(SimpleIntactIon, self).__init__(sequName, modification, nrOfModifications, '', radicals)
        self._mz = mz
        self._theoMz = theoMz
        self._charge = charge
        self._intensity = intensity
        #self._isotopePattern = isotopePattern
        #self._comment = ''


    def getMonoisotopic(self):
        return self._mz
    def getTheoMz(self):
        return self._theoMz

    def getRelAbundance(self):
        return self._intensity/self._charge

    def getError(self):
        return (self._mz - self._theoMz) / self._theoMz * 10 ** 6

    def toList(self):
        return [self._mz, self._charge, self._intensity, self.getRelAbundance(), self.getName(), round(self.getError(), 2)]


class SimpleIon(SimpleIntactIon):
    '''
    Simplified ion for assignment in intact ion list
    '''
    def __init__(self, neutral, mz, theoMz, z, intensity, snr, qual):
        '''
        :param (Fragment) neutral: neutral fragment
        :param (float) mz: monoisotopic m/z
        :param (float) theoMz: theoretical (calculated) m/z
        :param (int) charge: charge
        :param (float) intensity: intensity
        '''
        name = neutral.getType()
        if neutral.getNumber() != 0:
            name +=format(neutral.getNumber(), "02d")
        super(SimpleIon, self).__init__(name, neutral.getModification(), mz, theoMz, z, intensity,
                                        0, neutral.getRadicals())
        self._snr = snr
        self._quality = qual
        self._monoPeak = None
        self.getNumber = neutral.getNumber

    def getType(self):
        return self.getUnmodifiedName()[0]

    def getSignalToNoise(self):
        return self._snr

    def getMonoPeak(self):
        return self._monoPeak

    def setMonoPeak(self, monoPeak):
        self._monoPeak = monoPeak

