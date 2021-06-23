from unittest import TestCase
import numpy as np

from src.Exceptions import InvalidInputException
from src.IsotopePatternLogics import IsotopePatternLogics
from src.MolecularFormula import MolecularFormula
from src.Services import SequenceService
from src.entities.SearchSettings import SearchSettings
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from tests.top_down.test_LibraryBuilder import initTestSequences


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
        RNA_formulaDummy = MolecularFormula('C38H48N15O26P3')  # GCAU
        peptideFormulaDummy = MolecularFormula('C36H56N12O14S')  # GCASDQHPV
        uniFormulaDummy = MolecularFormula('C5H5N5ONa')
        RNA_pattern = [(1223.2107777180972, 0.58545685), (1224.2134684, 0.28360589), (1225.21578726, 0.09861313),
                       (1226.21815597, 0.02558403), (1227.22044876, 0.00558521)]
        peptide_pattern = [(912.37596571, 0.59104661), (913.37869526, 0.26946771), (914.37874787, 0.1035717),
                           (915.37979107, 0.02834297), (916.38113847, 0.00624432)]
        uni_pattern = [(174.03917908, 0.92733003), (175.04099458, 0.06836688), (176.04296025, 0.00412072)]
        self.testIsotopePattern(RNA_pattern, RNA_formulaDummy.calculateIsotopePattern())
        self.testIsotopePattern(peptide_pattern, peptideFormulaDummy.calculateIsotopePattern())
        print(uniFormulaDummy.calculateIsotopePattern())
        self.testIsotopePattern(uni_pattern, uniFormulaDummy.calculateIsotopePattern())
        self.fail()


    def testIsotopePattern(self, theoIsotopePattern=None, calcIsotopePattern=None):
        if theoIsotopePattern != None:
            theoIsotopePattern = np.array(theoIsotopePattern, dtype=[('m/z', np.float64), ('calcInt', np.float64)])
            theoIsotopePattern['calcInt'] *= (calcIsotopePattern['calcInt'][0] / theoIsotopePattern['calcInt'][0])
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
