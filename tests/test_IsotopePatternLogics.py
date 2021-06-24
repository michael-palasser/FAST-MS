from unittest import TestCase
import numpy as np

from src.Exceptions import InvalidInputException
from src.IsotopePatternLogics import IsotopePatternLogics
from src.MolecularFormula import MolecularFormula
from src.Services import SequenceService
from src.entities.SearchSettings import SearchSettings
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from tests.top_down.test_LibraryBuilder import initTestSequences
from tests.test_MolecularFormula import *


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
        RNA_ion,RNA_neutralMass = self.getIon('RNA',0)
        formulaIon, formulaNeutralMass = self.logics.calculate('mol. formula',RNA_formulaDummy.toString()+'(C14H25N3O)2',2, 0,1000)
        self.assertEqual(RNA_ion.getFormula().toString(), formulaIon.getFormula().toString())
        #theoIsotopePattern = self.fragmentsRNA['dummyRNA'].getIsotopePattern()
        self.assertAlmostEqual(RNA_neutralMass,formulaNeutralMass)
        self.testIsotopePattern(formulaIon.getIsotopePattern(), RNA_ion.getIsotopePattern())
        #self.testIsotopePattern(theoIsotopePattern, formulaIon.getIsotopePattern())
        #ToDo

    def getIon(self,mode, radicals):
        if mode == 'RNA':
            searchSettings = self.searchSettingsRNA
            modifPattern = 'CMCT'
            modif = '+CMCT'
            nrMod = 2
        else:
            searchSettings = self.searchSettingsProt
            modifPattern = '-'
            modif = '-'
            nrMod = 0
        properties = self.getProperties(searchSettings)
        return self.logics.calculate(mode, properties['sequString'], 2, radicals,1000, properties['fragmentationName'],
                                     'Prec', modifPattern, modif, nrMod)

    def testIsotopePattern(self, theoIsotopePattern=None, calcIsotopePattern=None):
        if theoIsotopePattern != None:
            #theoIsotopePattern = np.array(theoIsotopePattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])
            #theoIsotopePattern['calcInt'] *= (calcIsotopePattern['calcInt'][0] / theoIsotopePattern['calcInt'][0])
            if len(theoIsotopePattern) > (len(calcIsotopePattern) + 1):
                raise Exception('Length of calculated isotope pattern to short')
            for i in range(len(theoIsotopePattern)):
                self.assertAlmostEqual(theoIsotopePattern[i]['m/z'], calcIsotopePattern[i]['m/z'], delta=5 * 10 ** (-6))
                self.assertAlmostEqual(theoIsotopePattern[i]['calcInt'], calcIsotopePattern[i]['calcInt'],
                                       delta=5 * 10 ** (-6))
            self.assertAlmostEqual(1.0, float(np.sum(calcIsotopePattern['calcInt'])), delta=0.005)
            self.assertTrue(np.sum(calcIsotopePattern['calcInt']) < 1)

    def test_check_formula(self):
        with self.assertRaises(InvalidInputException):
            self.logics.checkFormula('CxH5')
        with self.assertRaises(InvalidInputException):
            self.logics.checkFormula('cH4')
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
                _, rest = FragmentLibraryBuilder.processTemplateName(name)
                newFragDict['Prec' + rest] = frag
            newFragDict[name] = frag
        properties = self.getProperties(searchSettings)
        for fragTemp in searchSettings.getFragmentation().getItems() + searchSettings.getFragmentation().getItems2():
            if not fragTemp.enabled():
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
                if not modTemp.enabled():
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
        return {'sequString': ''.join(searchSettings.getSequenceList()),
                'fragmentationName': searchSettings.getFragmentation().getName(),
                'modifPatternName': searchSettings.getModificationName()}

    '''def test_model(self):
        self.fail()

    def test_get_isotope_pattern(self):
        self.fail()'''
