'''
Created on 27 Jul 2020

@author: michael
'''
from math import exp
from re import findall
import logging
import numpy as np
from scipy.constants import R

from src.entities.Ions import FragmentIon
#from Other.simpleFunctions import eMass, protMass
from src.services.assign_services.AbstractSpectrumHandler import AbstractSpectrumHandler

logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename='logfile_SpectrumHandler.log',level=logging.INFO)


# ToDo: Test SearchParameters, Proteins!, Parameters
def getFragmentChargeRange(molecule, sprayMode, normalisationFactor, fragment, precModCharge, fragModCharge, precCharge,
                           tolerance):
    '''
    Calculates the most probable charge (z) for a given fragment and returns a range of this z +/- a tolerance
    The charge is calculated using the number of phosphates (RNA/DNA) or using the length of the sequence (proteins)
    :param (str) molecule: name of molecule
    :param (int) sprayMode: +1 for positive, -1 for negative
    :param (float) normalisationFactor:
    :param fragment: corresponding fragment
    :type fragment: Fragment
    :param (float) precModCharge: charge effect of precursor modification
    :param (float) fragModCharge: charge effect of fragment modification
    :param (int) precCharge: (absolute) charge of precursor
    :param (float) tolerance: the higher the larger the charge range
    :return: (generator, int) tuple of:
            range between lowest possible z and highest possible z,
            most probable z
    '''
    if molecule in ['RNA', 'DNA'] and sprayMode == -1:
        formula = fragment.getFormula().getFormulaDict()
        if ('P' not in formula.keys()) or (fragment.getFormula().getFormulaDict()['P'] == 0):
            return range(0, 0), 0
        probableZ = fragment.getFormula().getFormulaDict()['P'] * normalisationFactor
    elif molecule == 'Protein':
        probableZ = len(fragment.getSequence()) * normalisationFactor
    elif molecule in ['RNA', 'DNA'] and sprayMode == 1:
        probableZ = len(fragment.getSequence()) * normalisationFactor
    else:
        probableZ = len(fragment.getSequence()) * normalisationFactor
    probableZ -= fragment.getRadicals()
    lowZ, highZ = 1, precCharge
    zEffect = (fragModCharge - precModCharge) * sprayMode
    # print(1,fragment.getName(),probableZ)
    probableZ += zEffect
    # print(2,fragment.getName(),probableZ)
    if (probableZ - tolerance) > lowZ:
        lowZ = round(probableZ - tolerance)
    if (probableZ + tolerance) < highZ:
        highZ = round(probableZ + tolerance)
    # print(fragment.getName(),lowZ,round(probableZ,2),highZ)
    return range(lowZ, highZ + 1), probableZ


class SpectrumHandler(AbstractSpectrumHandler):
    '''
    Reads a top-down spectrum (peak list), calculates noise and finds peaks in the spectrum
    '''
    #ToDo:
    basicAA = {'H': 3, 'R': 10, 'K': 10,
               'D': 0.5, 'E': 0.5}
    acidicAA = {'D': 10, 'E': 10,
                'H': 0.9, 'R': 0.5, 'K': 0.5, }

    def __init__(self, properties, precursor, settings, configs, peaks=None):
        '''
        Constructor, also processes spectrum
        :param properties: propertyStorage of search
        :type properties: SearchSettings
        :param precursor: precursor Fragment
        :type precursor: Fragment
        :param (dict[str,Any]) settings: search settings
        :param (set[tuple[float]] | None) peaks: set of peak tuples (m/z, I)
        '''
        sprayMode = 1
        if settings['charge'] < 0:
            sprayMode = -1
        super(SpectrumHandler, self).__init__(settings, configs, sprayMode, FragmentIon, peaks)
        self._sequList = properties.getSequenceList()
        self._properties = properties
        '''
        self._settings = settings
        self._sprayMode = 1
        if self._settings['charge'] < 0:
            self._sprayMode = -1
        self._upperBound=0'''
        '''self._normalisationFactor = None'''
        self._moleculeName = self._properties.getMolecule().getName()
        self._precursor = precursor
        self._charge = self.calcPrecCharge(self._settings['charge'], self._precursor.getRadicals())
        self._normalisationFactor = self.getNormalisationFactor()
        self._precModCharge = self.getModCharge(self._precursor)

    def setPrecModCharge(self, precModCharge):
        self._precModCharge = precModCharge

    def calcPrecCharge(self, charge, radicals):
        return abs(charge) - radicals #must be changed if radicals turns to electrons

    def setNormalisationFactor(self, factor):
        self._normalisationFactor = factor

    def getCharge(self):
        return self._charge

    def getNormalisationFactor(self):
        '''
        Calculates factor to normalise charge to number of precursor charges
        :return: (float) normalisation factor
        '''
        if self._moleculeName in ['RNA', 'DNA'] and self._sprayMode == -1:
            return self._charge / self._precursor.getFormula().getFormulaDict()['P']
            #return self._charge / len(self._sequList)
        #elif self._moleculeName == 'Protein' and self._sprayMode == 1:
         #   return self._charge / self.getChargeScore(self._sequList)
        #elif self._moleculeName in ['RNA', 'DNA'] and self._sprayMode == 1:
        #    return self._charge / len(self._sequList)
        else:
            return self._charge  / len(self._sequList)#self.getChargeScore(self._sequList)

    def getChargeScore(self, fragment): #ToDo: For proteins, currently not use
        chargeDict = self._properties.getGPBsOfBBs(self._sprayMode)
        score = 0
        """if self._properties.getFragmentation()[fragment.type].getDirection() == 1 and self._sprayMode== 1:
            score ="""
        #if self._sprayMode == 1:
        for bb in fragment.sequenceList:
            score += exp(self._sprayMode*chargeDict[bb]/(R*298))
        return score

    def getModCharge(self, fragment):
        '''
        Calculates the charge altering effect by the modification of a fragment
        :param fragment: concerning fragment
        :type fragment: Fragment
        :return: (float) charge shift
        '''
        modCharge = 0
        for mod, charge in self._properties.getChargedModifications().items():
            if mod[1:] in fragment.getModification():
                nrMod = 1
                if len(findall(r"(\d+)"+mod, fragment.getModification())) > 0:
                    nrMod = int(findall(r"(\d+)"+mod, fragment.getModification())[0])
                modCharge += charge * nrMod# * self._sprayMode
        logging.debug('Charge of modification: '+ str(modCharge))
        return modCharge

    #ToDo: Test SearchParameters, Proteins!, Parameters
    def getChargeRange(self, fragment):
        '''
        Calculates the most probable charge (z) for a given fragment and returns a range of this z +/- a tolerance
        The charge is calculated using the number of phosphates (RNA/DNA) or using the length of the sequence (proteins)
        :param fragment: corresponding fragment
        :type fragment: Fragment
        :param (float) precModCharge: charge effect of precursor modification
        :return: (generator) range between lowest possible z and highest possible z
        '''
        if self._moleculeName in ['RNA','DNA'] and self._sprayMode == -1:
            #probableZ = (fragment.number-1) * self._normalisationFactor
            formula = fragment.getFormula().getFormulaDict()
            if ('P' not in formula.keys()) or (fragment.getFormula().getFormulaDict()['P'] == 0):
                return range(0,0)
            probableZ = fragment.getFormula().getFormulaDict()['P']* self._normalisationFactor
            #probableZ = fragment.formula.formulaDict['P'] * self._normalisationFactor
        elif self._moleculeName == 'Protein':
            #probableZ = self.getChargeScore(fragment) * self._normalisationFactor
            probableZ = len(fragment.getSequence()) * self._normalisationFactor
        elif self._moleculeName in ['RNA' ,'DNA'] and self._sprayMode == 1:
            probableZ = len(fragment.getSequence()) * self._normalisationFactor
        else:
            probableZ = len(fragment.getSequence()) * self._normalisationFactor
        probableZ -= fragment.getRadicals()
        tolerance = self._configs['zTolerance']
        lowZ, highZ = 1, self._charge
        if fragment.getNumber()==0:
            highZ = abs(self._settings['charge'])
        zEffect = (self.getModCharge(fragment)-self._precModCharge) * self._sprayMode
        #print(1,fragment.getName(),probableZ)
        probableZ += zEffect
        #print(2,fragment.getName(),probableZ)
        if (probableZ-tolerance)> lowZ:
            lowZ = round(probableZ-tolerance)
        if (probableZ+tolerance)< highZ:
            highZ = round(probableZ + tolerance)
        #print(fragment.getName(),lowZ,round(probableZ,2),highZ)
        logging.info(fragment.getName()+'\tmin z: '+str(lowZ)+'\tcalc. z: '+str(round(probableZ,2))+'\tmax z: '+str(highZ))
        return range(lowZ,highZ+1)


    def findIons(self, fragmentLibrary):
        '''
        Assigns peaks in spectrum to isotope peaks of corresponding ion
        1. Possible charges of species are calculated
        2. Search for n highest isotope peaks in spectrum: n either 1, 2 or 3 (see Fragment.getNumberOfHighestIsotopes)
        3. If found noise is calculated and the isotope peaks which could theoretically be above the noise are calculated:
            Programm searches for these peaks in spectrum
            If all isotope peaks are calculated to be below noise threshold, ion is added to deleted ion (comment = noise)
        :param (list) fragmentLibrary: list of Fragment-objects
        '''
        np.set_printoptions(suppress=True)
        #precModCharge = self.getModCharge(self._precursor)
        logging.debug('Normalisation factor: '+ str(self._normalisationFactor))
        self.getProtonIsotopePatterns()
        for fragment in fragmentLibrary:
            #neutralPatternFFT = formula.calculateIsotopePatternFFT(1, )
            logging.info(fragment.getName())
            self._searchedChargeStates[fragment.getName()] = []
            zRange = self.getChargeRange(fragment)
            self.findIon(fragment, zRange)


    def setSearchedChargeStates(self, searchedZStates):
        self._searchedChargeStates = searchedZStates