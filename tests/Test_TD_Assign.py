import os
from copy import deepcopy

from unittest import TestCase

from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.resources import path
from src.top_down.TD_Assign import TD_Assigner
from tests.test_services.test_LibraryBuilder import initTestSequences


class Test_TD_Assign(TestCase):

    def test_search(self):
        initTestSequences()
        configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        settings = {'sequName': 'CR_1_2', 'charge': -4, 'fragmentation': 'RNA CAD', 'modifications': +134,
                    'nrMod': 1, 'spectralData': os.path.join(path, 'tests', 'test_files',
                                            'CR_1_2_annealed_noMg_ESI_500mMDEPC_125min_Sk75_CAD12p5_134_SNAP.txt'),
                    'errorlimit': 50}
        assigner = TD_Assigner(settings,configs)
        found =assigner.search()
        [print(ion.getName(),ion.getCharge()) for ion in found]

        print('\n new')
        settings['errorlimit'] = 10
        settings['spectralData'] = os.path.join(path, 'tests', 'test_files','CR_1_2_annealed_noMg_ESI_500mMDEPC_125min_Sk75_CAD12p5_134_SNAP_cal.txt')
        assigner = TD_Assigner(settings,configs)
        found2 =assigner.search()
        [print(ion.getName(),ion.getCharge()) for ion in found2]
        print(len(found), len(found2))


    def getCalibratedSpectrum(self,finder, settings,found):
        data = deepcopy(finder.readFile(settings['spectralData'])[0])
        print('slkdfj',data.dtype)

        calibrationValues, errors, quality, usedIons = finder.findCalibrationFunction(found, 50, 0.8)
        print(data[5])
        data['m/z'] = finder.calibrate(data['m/z'], calibrationValues)
        print(data[5])
        with open(os.path.join(path, 'tests', 'test_files',
                'CR_1_2_annealed_noMg_ESI_500mMDEPC_125min_Sk75_CAD12p5_134_SNAP_cal.txt')) as f:
            f.write('m/z\tz\I\n')
            for row in data:
                for item in row:
                    f.write(item+'\t')
            f.write('\n')

        return data
