import os
from unittest import TestCase

import numpy as np
from src.resources import path
from src.repositories.SpectralDataReader import SpectralDataReader




class Test_spectral_data_reader(TestCase):
    def test_open_txt_file(self):
        print('start')
        file1 = os.path.join(path, 'tests', 'test_files', '2511_RIO_test_0.txt')
        file2 = os.path.join(path, 'tests', 'test_files', '2511_neoRibo_3xRIO_CMCT_1.5mMPip_4mMIm_01_0.52.txt')
        file3 = os.path.join(path, 'tests', 'test_files', 'NNC0614_Antisense_MS010_22_0445_19V_SNAP.txt')
        file4 = os.path.join(path, 'tests', 'test_files', 'NNC0614_Antisense_MS010_22_0445_19V.txt')
        file5 = os.path.join(path, 'tests', 'test_files', 'MS010_22_0433_SP.txt')
        reader = SpectralDataReader()
        data1 =reader.openTxtFile(file1,np.dtype([('m/z', float), ('z', np.uint8), ('I', float)]))[0]
        vals_theo = (255.22924, 1, 17481426)
        for i, index in enumerate(('m/z', 'z', 'I')):
            self.assertAlmostEqual(vals_theo[i],data1[index])
        data2 = reader.openTxtFile(file2,np.dtype([('m/z', float), ('I', float)]))[0]
        vals_theo = (209.41425, 759733)
        for i, index in enumerate(('m/z', 'I')):
            self.assertAlmostEqual(vals_theo[i],data2[index])
        reader.openTxtFile(file3,np.dtype([('m/z', float), ('z', np.uint8), ('I', float), ('S/N', float),
                                                   ('qual', float)]))
        reader.openTxtFile(file4,np.dtype([('m/z', float), ('I', float), ('S/N', float)]))
        vals_theo = (145.0403, 194,14.2)
        data3 = reader.openTxtFile(file5,np.dtype([('m/z', float), ('I', float), ('S/N', float)]))
        for i, index in enumerate(('m/z', 'I','S/N')):
            self.assertAlmostEqual(vals_theo[i],data3[0][index])
        reader.openTxtFile(file5,np.dtype([('m/z', float), ('I', float)]))

    def test_open_csv_file(self):
        assert False
