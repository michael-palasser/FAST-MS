import numpy as np

from src.entities.Ions import Fragment, Ion


class InternalFragment(Fragment):

    def __init__(self, type, number, modification, formula, sequence, radicals, type2, number2):
        '''
        :param (str) type: typically a, b, c, d
        :param (int) number: forward length of fragment-sequence (of original sequence)
        :param (str) modification: +modification, +ligands and -loss
        :param (MolecularFormula) formula: MolecularFormula
        :param (list [str]) sequence: list of building blocks
        :param (int) radicals: no. of radicals
        :param (str) type2: typically w, x, y or z
        :param (int) number2: backward length of fragment-sequence (of original sequence)
        '''
        super().__init__(type, number, modification, formula, sequence, radicals)
        self._type2 = type2
        self._number2 = number2

    def getName(self, html=False):
        if html:
            modification = self._modification
            if self._modification !="" and html:
                modification = self._modification + "]"
            return self._type + "<sub>" + self._type2 + "<sub>[" + str(self._number2+1)+ ":" + str(self._number)+ "]" + modification
        return self._type + self._type2 + "[" + str(self._number2+1)+ ":" + str(self._number)+ "]" + self._modification
        #return self._type + self._type2 + "[" + format(self._number2+1, "02d")+ "-" + format(self._number, "02d")+ "]" + self._modification
            #return self._type2 + "<sub>"+str(self._number2)+"<sub>"+ super().getName(html)
        #return self._type2 + format(self._number2, "02d") + self._modification  # + "-" + self.loss

    def getEdges(self):
        return [self._sequence[0] + str(self._number2+1) +":" + self._sequence[-1] + str(self._number), self._number2+1, self._number]

    def getNumber2(self):
        return self._number2

    def getAllAttributes(self):
        return self._type, self._number, self._modification, self._formula, self._sequence, self._radicals, \
            self._type2, self._number2,


class InternalFragmentIon(InternalFragment, Ion):
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
                         fragment._formula, fragment._sequence, fragment._radicals, fragment._type2, fragment._number2)
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

    def toStorage(self):
        '''
        To save an ion in database
        :return: list of values
        '''
        return [self.getName()+self._modification, -1, self._formula, self._monoisotopicRaw, self._charge,
                int(round(self._noise)), self._quality, self._comment]

class SimpleInternalIon(InternalFragment, Ion):
    def __init__(self, neutral, mz, theoMz, charge, intensity, error, snr, qual):
        '''
        :param (InternalFragment) neutral: neutral fragment
        :param (float) mz: assigned monoisotopic m/z
        :param (float) theoMz: theoretical (calculated) m/z
        :param (int) charge: charge
        :param (float) intensity: intensity
        :param (float) error: ppm error
        :param (float) snr: S/N (SNAP)
        :param (float) qual: Quality Factor (SNAP)
        '''
        super(SimpleInternalIon, self).__init__(*neutral.getAllAttributes())
        self._mz = mz
        self._theoMz = theoMz
        self._charge = charge
        self._intensity = intensity
        self._error = error
        self._snr = snr
        self._quality = qual

    def getValues(self):
        return [self._mz,self._charge, self._intensity, self.getName()]

    def getMonoisotopic(self):
        return self._mz
    def getTheoMz(self):
        return self._theoMz
    def getSignalToNoise(self):
        return self._snr



"""class InternalIon(FragmentIon):
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
        super().__init__(fragment, monoisotopic, charge, isotopePattern, noise, quality, calculate, comment, score)"""