import numpy as np

from src.Exceptions import InvalidInputException
from src.MolecularFormula import MolecularFormula
from src.FormulaFunctions import stringToFormula
from src.Services import MoleculeService, FragmentationService, ModificationService, PeriodicTableService
from src.entities.GeneralEntities import Sequence
from src.entities.Ions import Fragment, FragmentIon
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.entities.SearchSettings import processTemplateName
from src.simpleFunctions import eMass, protMass


class IsotopePatternLogics(object):
    '''
    Class that represents the service layer of the Isotope Pattern Tool
    '''
    def __init__(self):
        self._moleculeService = MoleculeService()
        self._fragService = FragmentationService()
        self._modService = ModificationService()
        self._elements = PeriodicTableService().getAllPatternNames()
        self._molecules = self._moleculeService.getAllPatternNames()
        self._intensityModeller = IntensityModeller(ConfigurationHandlerFactory.getTD_ConfigHandler().getAll())
        self._peakDtype = np.dtype([('m/z', np.float64), ('relAb', np.int32), ('calcInt', np.float64), ('used', np.bool_)])
        #self._peakDtype = np.dtype([('m/z', float), ('relAb', float), ('calcInt', float), ('used', np.bool_)])

        self._formula = None
        self._isotopePattern = None
        self._ion = None
        self._neutralMass = None
        self._avMass = None

    def getMolecules(self):
        '''
        :return: (list[str]) all stored molecule names
        '''
        return ['mol. formula']+self._molecules

    def getFragmentationNames(self):
        '''
        :return: (list[str]) all stored fragmentation pattern names
        '''
        return self._fragService.getAllPatternNames()

    def getModifPatternNames(self):
        '''
        :return: (list[str]) all stored modification pattern names
        '''
        return self._modService.getAllPatternNames()

    def getFragItems(self, fragmentationName):
        '''
        :param (str) fragmentationName: name of the corresponding fragmentation pattern
        :return: (tuple[list[str], list[str])) names of fragment templates, names of precursor templates
        '''
        return [fragTemplate.getName() for fragTemplate in
                self._fragService.getPatternWithObjects(fragmentationName).getItems()],\
               [precTemplate.getName() for precTemplate in
                self._fragService.getPatternWithObjects(fragmentationName).getItems2()][1:]


    def getModifItems(self, modifPatternName):
        '''
        :param (str) modifPatternName: name of the modification pattern
        :return: (list[str]) names of modifications
        '''
        return [modTemplate.getName() for modTemplate in
                self._modService.getPatternWithObjects(modifPatternName).getItems()]

    def getIon(self):
        return self._ion

    def getNeutralMass(self):
        '''
        :return: (float) mass of the neutral molecule
        '''
        return self._neutralMass

    def getAvMass(self):
        '''
        :return: (float) average mass
        '''
        return self._avMass

    def calculate(self, mode, inputString, charge, electrons, intensity, fragmentationName=None, fragTemplName=None,
                  modifPatternName=None, modifName=None, nrMod=None, accelerate=None):
        '''
        Calculates the isotope pattern of the ion
        Parameters fragmentationName, fragTemplName, modifPatternName, modifName, nrMod are only optional if mode is
        'mol. formula'
        :param (str) mode: molecule ('mol. formula' or e.g. 'RNA', 'Protein')
        :param (str) inputString: formula
        :param (int) charge: charge
        :param (int) electrons: nr. of electrons
        :param (int | float) intensity: intensity of the ion
        :param (str) fragmentationName: name of fragmentation pattern (optional)
        :param (str) fragTemplName: name of fragment template (optional)
        :param (str) modifPatternName: name of modification pattern (optional)
        :param (str) modifName: name of modification (optional)
        :param (int) nrMod: nr. of modifications (optional)
        :return: (tuple[FragmentIon, float]) calculated ion, mass of neutral molecule
        '''
        if inputString[0].islower():
            raise InvalidInputException(inputString, ", Unvalid format, first character must not be lower case")
        if mode == self.getMolecules()[0]:
            fragment = Fragment('-',0,'',MolecularFormula(self.checkFormula(inputString)),[],electrons)
        else:
            fragment = self.getFragment(mode, inputString, fragmentationName, fragTemplName, modifPatternName,
                                        modifName, nrMod)
        formula = fragment.getFormula()
        if formula != self._formula:
            self._formula = formula
            #self._fragment = fragment
            tempFormula=self._formula.addFormula({'H':charge})
            if tempFormula.getFormulaDict()['H']<0:
                raise InvalidInputException('Nr of H = '+str(tempFormula.getFormulaDict()['H']), 'not enough Hs for deprotonation')
            #if tempFormula.calcIsotopePatternSlowly(1)['m/z'][0]>6000:
            if accelerate is None:
                self._isotopePattern = tempFormula.calculateIsotopePattern()
            else:
                self._isotopePattern = tempFormula.calculateIsotopePatternFFT(accelerate)
            '''else:
                self._isotopePattern = tempFormula.calcIsotopePatternSlowly()'''
        #isotopePattern = copy.deepcopy(self._isotopePattern)
        self._neutralMass = self._isotopePattern['m/z'][0]
        self._avMass = np.sum(self._isotopePattern['calcInt']*self._isotopePattern['m/z']) / \
                       np.sum(self._isotopePattern['calcInt'])
        if charge != 0:
            self._neutralMass -= (protMass+eMass)*charge
        self._isotopePattern['m/z'] = self.getMz(self._isotopePattern['m/z'],charge,electrons)
        self._isotopePattern['calcInt'] *= intensity
        peaks = []
        for row in self._isotopePattern:
            peaks.append((row['m/z'],0,row['calcInt'],1))
        peaks = np.array(peaks, dtype=self._peakDtype)
        self._ion = FragmentIon(fragment, np.min(peaks['m/z']), charge, peaks,0)
        self._ion.setQuality(0)
        return self._ion, self._neutralMass, self._avMass

    @staticmethod
    def getMz(mass, z, electrons):
        '''
        Calculates m/z
        :param (float) mass: neutral mass
        :param (int) z: charge
        :param (int) electrons: number of electrons
        :return: (float) m/z
        '''
        if z != 0:
            return abs((mass+electrons*(protMass+eMass)-z*eMass) / z)
        else:
            return abs(mass+electrons*(protMass+eMass))

    def checkFormula(self,formulaString):
        '''
        Checks the format of the formula (user input)
        :param (str) formulaString: molecular formula string
        :return: (dict[str,int]) formula as dict {element:quantity}
        :raises InvalidInputException: if format of formulaString is incorrect
        '''
        formula = stringToFormula(formulaString,{},1)
        if formula == {}:
            raise InvalidInputException(formulaString, ", Unvalid format")
        for key in formula.keys():
            if key not in self._elements:
                print("Element: " + key + " unknown")
                raise InvalidInputException(formulaString, ", Element: " + key + " unknown")
        return formula


    def getFragment(self, moleculeName, sequString, fragmentationName, fragTemplName, modifPatternName, modifName, nrMod):
        '''
        Generates the fragment to the corresponding inputs
        :param (str) molecule: name of the molecule
        :param (str) sequString: name of the sequence
        :param (str) fragmentationName: name of the fragmentation pattern
        :param (str) fragTemplName: name of the fragment template
        :param (str) modifPatternName: name of the modification pattern
        :param (str) modifName: name of the modification
        :param (int) nrMod: nr. of modifications
        :return: (Fragment) fragment
        '''
        '''if sequString[0].islower():
            raise InvalidInputException(sequString, ", Unvalid format, first character in Sequence must not be lower case")'''
        molecule = self._moleculeService.get(moleculeName)
        sequenceList = Sequence("",sequString,molecule.getName(),0).getSequenceList()
        #formula = MolecularFormula(molecule.getFormula())
        buildingBlocks = molecule.getBBDict()
        formula = MolecularFormula({})
        for link in sequenceList:
            if link not in buildingBlocks:
                raise InvalidInputException(sequString, 'Building Block "'+link+ '" unknown for '+moleculeName )
            formula = formula.addFormula(buildingBlocks[link].getFormula())
        fragmentation = self._fragService.getPatternWithObjects(fragmentationName)
        if fragTemplName in ([precTempl.getName() for precTempl in fragmentation.getItems2()]):
            formula = formula.addFormula(molecule.getFormula())
            fragTempl = [precTempl for precTempl in fragmentation.getItems2() if precTempl.getName()==fragTemplName][0]
            number = 0
        else:
            fragTempl = [fragTempl for fragTempl in fragmentation.getItems() if fragTempl.getName()==fragTemplName][0]
            number = len(sequenceList)
        species, rest = processTemplateName(fragTempl.getName())
        formula = formula.addFormula(fragTempl.getFormula())
        if modifPatternName != '-' and nrMod != 0:
            modPattern = self._modService.getPatternWithObjects(modifPatternName)
            modif = [modif for modif in modPattern.getItems() if modif.getName()==modifName][0]
            formula = formula.addFormula({key:val*nrMod for key,val in modif.getFormula().items()})
            if nrMod != 1:
                rest =modifName[0]+str(nrMod)+modifName[1:]+rest
            else:
                rest =modifName+rest
        return Fragment(species, number, rest, formula, sequenceList, fragTempl.getRadicals())

    def model(self, peaks):
        '''
        Calculates the intensity of the ion
        :param (ndarray(dtype=[float,int,float,bool])) peaks: peaks (unfitted)
        :return: (FragmentIon) ion with modelled intensity and isotope pattern
        '''
        peakArr = np.array(peaks, dtype=self._peakDtype)
        if np.all(peakArr['relAb']==0):
            raise InvalidInputException('All Intensities = 0', '')
        isotopePattern, intensity, quality =  self._intensityModeller.modelSimply(peakArr)
        self._ion.setIsoIntQual(isotopePattern, intensity, quality)
        return self._ion


    def getIsotopePattern(self, ion):
        '''
        Returns the peaks which are activated #ToDo
        :param (FragmentIon) ion: ion
        :return: (ndarray(dtype=[float,int,float,bool])) activated peaks
        '''
        isotopePattern = ion.getIsotopePattern()
        return isotopePattern[np.where(isotopePattern['used'])]
