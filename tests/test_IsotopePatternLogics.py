from copy import deepcopy
from unittest import TestCase
import numpy as np

from src.Exceptions import InvalidInputException
from src.services.IsotopePatternLogics import IsotopePatternLogics
from src.MolecularFormula import MolecularFormula
from src.entities.SearchSettings import SearchSettings, processTemplateName
from src.services.library_services.LibraryBuilder import FragmentLibraryBuilder
from src.services.assign_services.SpectrumHandler import getMz
from tests.test_MolecularFormula import RNA_formulaDummy, RNA_pattern
from tests.top_down.test_LibraryBuilder import initTestSequences
#from tests.test_MolecularFormula


class TestIsotopePatternLogics(TestCase):
    def setUp(self):
        try:
            self.initLibrary()
        except:
            initTestSequences()
            self.initLibrary()

    def initLibrary(self):
        self.logics = IsotopePatternLogics()
        self.searchSettingsRNA = SearchSettings('dummyRNA', 'RNA_CAD', 'CMCT')
        self.fragmentsRNA = self.getLibrary(self.searchSettingsRNA, 2)
        self.searchSettingsProt = SearchSettings('dummyProt', 'Protein_ECD', '-')
        self.fragmentsProt = self.getLibrary(self.searchSettingsProt, 0)

    def getLibrary(self, searchSettings, nrMod):
        builder = FragmentLibraryBuilder(searchSettings, nrMod)
        builder.createFragmentLibrary()
        builder.addNewIsotopePattern()
        return {frag.getName():frag for frag in builder.getFragmentLibrary()}

    '''def test_get_molecules(self):
        self.fail()

    def test_get_fragmentation_names(self):
        self.fail()

    def test_get_modif_pattern_names(self):
        self.fail()

    def test_get_frag_items(self):
        self.fail()

    def test_get_modif_items(self):
        self.fail()

    def test_get_ion(self):
        self.fail()

    def test_get_neutral_mass(self):
        self.fail()'''

    def test_calculate(self):
        RNA_ion,RNA_neutralMass, RNA_averageMass = self.getIon('RNA',0)
        formulaIon, formulaNeutralMass, formulaAverageMass = self.logics.calculate('mol. formula',RNA_formulaDummy.toString()+'(C14H25N3O)2',
                                                               -2, 0,1000)
        self.assertEqual(RNA_ion.getFormula().toString(), formulaIon.getFormula().toString())
        self.assertAlmostEqual(RNA_neutralMass,formulaNeutralMass)
        self.assertAlmostEqual(RNA_averageMass,formulaAverageMass)
        self.testIsotopePattern(formulaIon.getIsotopePattern(), RNA_ion.getIsotopePattern())

        pepIon,pepNeutralMass, pepAverageMass = self.getIon('Protein',1)
        formulaIon, formulaNeutralMass, formulaAverageMass = self.logics.calculate('mol. formula','C16H24N6O5', 2, 1,1000)
        self.assertEqual(pepIon.getFormula().toString(), formulaIon.getFormula().toString())
        self.assertAlmostEqual(pepNeutralMass,formulaNeutralMass)
        self.assertAlmostEqual(pepAverageMass,formulaAverageMass)
        self.testIsotopePattern(formulaIon.getIsotopePattern(), pepIon.getIsotopePattern())

        formulaIon, formulaNeutralMass, formulaAverageMass = self.logics.calculate('mol. formula',RNA_formulaDummy.toString(),-2, 0,1000)
        #print([(getMz(RNA_pattern[i]['m/z'],2,0),RNA_pattern[i]['calcInt']*1000) for i in range(len(RNA_pattern))])
        theoIsotopePattern= np.array(self.getIonPattern(RNA_pattern,2,-1,0),dtype=RNA_pattern.dtype)
        #print(theoIsotopePattern)
        #print(formulaIon.getIsotopePattern())
        self.testIsotopePattern(theoIsotopePattern, formulaIon.getIsotopePattern(), 10e-4)
        with self.assertRaises(InvalidInputException):
            self.logics.calculate('mol. formula', 'c(C14H25N3O)2',2, 0, 1000)
        with self.assertRaises(InvalidInputException):
            self.getIon('bad',0)

    def getIonPattern(self, neutralPattern, z, sprayMode, radicals):
        protonIsotopePattern = MolecularFormula({'H': z}).calcIsotopePatternPart(2)['calcInt']
        theoreticalPeaks = deepcopy(neutralPattern)
        theoreticalPeaks['m/z'] = getMz(theoreticalPeaks['m/z'], z * sprayMode, radicals)
        theoreticalPeaks['calcInt'][0] *= protonIsotopePattern[0] ** sprayMode
        if sprayMode == 1:
            regressionVals = neutralPattern['calcInt']
        else:
            regressionVals = theoreticalPeaks['calcInt']
        for i in range(1,len(theoreticalPeaks)):
            theoreticalPeaks['calcInt'][i] += protonIsotopePattern[1]*regressionVals[i-1]*sprayMode
        return theoreticalPeaks

    def getIon(self,mode, radicals):
        bad = ''
        charge = -2
        if mode == 'RNA':
            searchSettings = self.searchSettingsRNA
            modifPattern = 'CMCT'
            modif = '+CMCT'
            nrMod = 2
        elif mode == 'Protein':
            searchSettings = self.searchSettingsProt
            modifPattern = '-'
            modif = '-'
            nrMod = 0
            charge = 2
        else:
            mode='RNA'
            searchSettings = self.searchSettingsProt
            modifPattern = '-'
            modif = '-'
            nrMod = 0
            bad = 'g'
        properties = self.getProperties(searchSettings)
        return self.logics.calculate(mode,bad+properties['sequString'], charge, radicals,1000, properties['fragmentationName'],
                                     'Prec', modifPattern, modif, nrMod)

    def testIsotopePattern(self,calcIsotopePattern1=None, calcIsotopePattern2=None, delta=5*10**(-6)):
        if calcIsotopePattern1 is not None:
            #calcIsotopePattern1 = np.array(calcIsotopePattern1, dtype=[('m/z', np.float64), ('calcInt', np.float64)])
            #calcIsotopePattern1['calcInt'] *= (calcIsotopePattern2['calcInt'][0] / calcIsotopePattern1['calcInt'][0])
            #if len(calcIsotopePattern1) > (len(theoIsotopePattern) + 1):
            #    raise Exception('Length of calculated isotope pattern to short')
            self.assertEqual(len(calcIsotopePattern1),len(calcIsotopePattern2))
            sum1 = np.sum(calcIsotopePattern1['calcInt'])
            sum2 = np.sum(calcIsotopePattern2['calcInt'])
            #factor = calcIsotopePattern2[0]['calcInt'] / theoIsotopePattern[0]['calcInt'],
            for i in range(len(calcIsotopePattern1)):
                #self.assertAlmostEqual(getMz(theoIsotopePattern[i]['m/z'], charge, radicals), calcIsotopePattern2[i]['m/z'], delta=5 * 10 ** (-6))
                #self.assertAlmostEqual(theoIsotopePattern[i]['calcInt']*factor, calcIsotopePattern2[i]['calcInt'],
                #                       delta=5 * 10 ** (-6))
                self.assertAlmostEqual(calcIsotopePattern1[i]['m/z'], calcIsotopePattern2[i]['m/z'],
                                       delta=delta)
                self.assertAlmostEqual(calcIsotopePattern1[i]['calcInt']/sum1, calcIsotopePattern2[i]['calcInt']/sum2,
                                       delta=delta)

    def test_check_formula(self):
        with self.assertRaises(InvalidInputException):
            self.logics.checkFormula('CxH5')
        with self.assertRaises(InvalidInputException):
            self.logics.checkFormula('')
        molFormulaDummy = MolecularFormula('C5H4N3O')
        dict0 = {'C': 5, 'H': 4, 'N': 3, 'O': 1}
        self.assertEqual(dict0, molFormulaDummy.getFormulaDict())

    def test_get_fragment(self):
        self.test_get_fragment2('RNA')
        self.test_get_fragment2('Protein')
        with self.assertRaises(InvalidInputException):
            self.logics.getFragment('RNA', 'GCHx', 'RNA_CAD', 'c', '-', '-', 0)



    def test_get_fragment2(self, mode=None):
        if mode is None:
            return
        elif mode == 'RNA':
            precName = 'dummyRNA'
            fragLib = self.fragmentsRNA
            searchSettings = self.searchSettingsRNA
        else:
            precName = 'dummyProt'
            fragLib = self.fragmentsProt
            searchSettings = self.searchSettingsProt
        newFragDict = {}
        for name, frag in fragLib.items():
            if precName in name:
                _, rest = processTemplateName(name)
                newFragDict['Prec' + rest] = frag
            newFragDict[name] = frag
        properties = self.getProperties(searchSettings)
        for fragTemp in searchSettings.getFragmentation().getItems() + searchSettings.getFragmentation().getItems2():
            if not fragTemp.isEnabled():
                continue
            fragTempName = fragTemp.getName()
            if fragTempName[0] in ['a', 'b', 'c', 'd']:
                sequ = properties['sequString'][:-1]
            elif fragTempName[0] in ['w', 'x', 'y', 'z']:
                sequ = properties['sequString'][1:]
            else:
                sequ = properties['sequString']
            fragment = self.logics.getFragment(mode, sequ, properties['fragmentationName'], fragTempName, '-', '-', 0)
            name = fragment.getName()
            if (name not in newFragDict.keys()) and ('-G' in name or '-A' in name or '-C' in name):
                continue
            self.assertIn(name, newFragDict.keys())
            self.assertEqual(fragment.getFormula().getFormulaDict(), newFragDict[name].getFormula().getFormulaDict())
            for modTemp in searchSettings.getModification().getItems():
                if not modTemp.isEnabled():
                    continue
                for nrMod in range(1, 3):
                    fragment = self.logics.getFragment(mode, sequ, properties['fragmentationName'], fragTempName,
                                                       properties['modifPatternName'], modTemp.getName(), nrMod)
                    name = fragment.getName()
                    if nrMod == 1:
                        pos = name.find('CMCT')
                        name = name[:pos] + str(nrMod) + name[pos:]
                    self.assertIn(name, newFragDict.keys())
                    self.assertEqual(fragment.getFormula().getFormulaDict(),
                                     newFragDict[name].getFormula().getFormulaDict(), fragment.getName() + ', ' + name)

    def getProperties(self, searchSettings):
        print('hey',searchSettings.getModificationName())
        return {'sequString': ''.join(searchSettings.getSequenceList()),
                'fragmentationName': searchSettings.getFragmentation().getName(),
                'modifPatternName': searchSettings.getModification().getName()}

    '''def test_model(self):
        self.fail()

    def test_get_isotope_pattern(self):
        self.fail()'''
