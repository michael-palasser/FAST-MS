from unittest import TestCase
import numpy as np

from src.entities.Ions import SimpleIntactIon
from src.services.analyser_services.IntactAnalyser import IntactAnalyser
#from tests.intact.test_IntactFinder import initFinders, initTestSequences

class TestIntactAnalyser(TestCase):
    def setUp(self):
        self.maxCharge =15
        """try:
            self.finderRNA, self.configRNA, self.finderProt, self.configProt = initFinders()
        except:
            initTestSequences()
            self.finderRNA, self.configRNA, self.finderProt, self.configProt = initFinders()
        with open('2511_RIO_test.txt') as f:
            self.finderRNA.readData(f)
        self.finderRNA.calibrateAll()
        self.analyser = IntactAnalyser(self.finderRNA.findIons(self.configRNA.get('k'), self.configRNA.get('d'), True))"""

    def test_calculate_av_charge_and_error(self):
        ions, errors = self.getRandomIons(20)
        weigthedCharges = 0
        weightedChargesAb = 0
        sumInt = 0
        sumAb = 0
        for ion in ions:
            intensity = ion.getIntensity()
            z = ion.getCharge()
            sumInt += intensity
            sumAb +=intensity/z
            weigthedCharges += z*intensity
            weightedChargesAb += intensity
        analyser = IntactAnalyser([[ions]])
        averageCharges, averageErrors, stddevOfErrors = analyser.calculateAvChargeAndError()
        self.assertAlmostEqual(weigthedCharges/sumInt, averageCharges[0][0][0])
        self.assertAlmostEqual(weightedChargesAb/sumAb, averageCharges[0][0][1])
        self.assertAlmostEqual(np.average(errors), averageErrors[0][0])
        self.assertAlmostEqual(np.std(errors), stddevOfErrors[0][0])

    def getRandomIons(self, nr):
        errors = np.empty(nr)
        ions = []
        for i in range(nr):
            mz = (i + 1) * 100
            # ppm errors between -10 and +10 ppm
            ppm = np.random.random_sample() * 20 - 10
            errors[i]= ppm
            charge = np.random.randint(1, self.maxCharge)
            intensity = np.random.randint(10 ** 6, 10 ** 8)
            nrMod = np.random.randint(1, 5)
            if not i%4:
                mod = '+x'
            elif not i%2:
                mod = '+y'
            else:
                mod = '-'
                nrMod=0
            ions.append(SimpleIntactIon('', mod, mz + ppm * mz / 10 ** 6, mz, charge, intensity, nrMod, 0))
        return ions, errors

    def test_calculate_average_modification(self):
        ions, _ = self.getRandomIons(20)
        weigthedMod = {z:0 for z in range(1,self.maxCharge)}
        sumInt = {z:0 for z in range(1,self.maxCharge)}
        totalModified, total = 0,0
        totalModifiedAb, totalAb = 0,0
        for ion in ions:
            intensity = ion.getIntensity()
            z=ion.getCharge()
            weigthedMod[z] += ion.getNrOfModifications()*intensity
            sumInt[z] += intensity
            totalModified += ion.getNrOfModifications()* intensity
            total += intensity
            totalModifiedAb += ion.getNrOfModifications()* intensity/z
            totalAb += intensity/z
        analyser = IntactAnalyser([[ions]])
        averageModificationsPerZList, averageModificationsList = analyser.calculateAverageModification(False)
        averageModificationsPerZ = averageModificationsPerZList[0][0]
        for z in averageModificationsPerZ.keys():
            self.assertAlmostEqual(weigthedMod[z]/sumInt[z], averageModificationsPerZ[z])
        self.assertAlmostEqual(totalModified/total, averageModificationsList[0][0])
        _, averageModificationsList = analyser.calculateAverageModification(True)
        self.assertAlmostEqual(totalModifiedAb/totalAb, averageModificationsList[0][0])


    """def test_make_charge_array(self):
        self.fail()"""

    def test_calculate_modifications(self):
        mods = {'-':0,'+x':1,'+y':2}
        ions = []
        for z in range(1,self.maxCharge):
            if z == 4:
                continue
            intensity = np.random.randint(10 ** 6, 10 ** 8)
            for mod in mods.keys():
                nrMod = np.random.randint(1, 5)
                if mod == '-':
                    nrMod=0
                ions.append(SimpleIntactIon('', mod, 1, 1, z, intensity, nrMod, 0))
        modifInts = np.zeros((self.maxCharge,3))
        modifIntsTotal, modifAbsTotal = np.zeros(3), np.zeros(3)
        for ion in ions:
            index = mods[ion.getModification()]
            intensity, z = ion.getIntensity(), ion.getCharge()
            modifInts[z-1,index] += intensity
            modifIntsTotal[index] += intensity
            modifAbsTotal[index] += intensity/z
        modifRelInts = np.zeros((self.maxCharge,3))
        totalInt, totalAb = np.sum(modifIntsTotal), np.sum(modifAbsTotal)
        for i in range(self.maxCharge):
            for j,val in enumerate(modifInts[i]):
                modifRelInts[i,j] = val/np.sum(modifInts[i])
        analyser = IntactAnalyser([[ions]])
        analyser.calculateAvChargeAndError()
        listOfCalcModifsPerZ, listOfcalcModifs = analyser.calculateModifications()
        for mod,arr in listOfCalcModifsPerZ[0][0].items():
            for row in arr:
                self.assertAlmostEqual(modifRelInts[int(row[0]-1),mods[mod]],row[1])
        for mod,val in listOfcalcModifs[0][0].items():
            self.assertAlmostEqual(modifIntsTotal[mods[mod]]/totalInt,val)
        for mod,val in analyser.calculateModifications(True)[1][0][0].items():
            self.assertAlmostEqual(modifAbsTotal[mods[mod]]/totalAb,val)

    """def test_get_sorted_ion_list(self):
        self.fail()"""
