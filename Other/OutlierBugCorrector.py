import sys
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from src.resources import autoStart, path


def readCsv(file):
    try:
        arr = np.loadtxt(file, delimiter=',', skiprows=1,
                         dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32'),
                                ('error',np.float64), ('used', np.uint8)])
    except ValueError:
        arr = np.loadtxt(file, delimiter='\t', skiprows=1,
                         dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32'),
                                ('error',np.float64), ('used', np.uint8)])
    return arr


def run(mainWindow):
    """import ion-list"""
    spectralFile = path + 'Spectral_data/debug_incorrect.csv'
    with open(spectralFile, 'w') as f:
        f.write("m/z,z,int,name,error,used")
    autoStart(spectralFile)
    start = QtWidgets.QMessageBox.question(mainWindow, 'Correcting Intensities ',
        'Paste the ions (format: m/z, z, Int., fragment-name, error, used) in the csv-file and press "Ok"',
                                                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
    if start == QtWidgets.QMessageBox.Ok:
        arr = readCsv(spectralFile)
        incorrect = arr[np.where(arr['used']==0)]
        print(incorrect)
        corrected = {}
        #mz, z, corrInt, name = None, None, 0, None
        for row in incorrect:
            if (row['name'], row['z']) not in corrected.keys():
                corrInt = np.sum(arr[np.where((arr['z']==row['z']) & (arr['name']==row['name']))]['intensity'])
                corrected[(row['name'], row['z'])] = int(np.around(corrInt))
        #corrected.append((mz, z, corrInt, name))
        output = path + 'Spectral_data/debug_correct.txt'
        with open(output, 'w') as f:
            f.write("name\tz\tcorr_int\n")
            for key,val in corrected.items():
                print(key[0], key[1], val)
                f.write(key[0]+ '\t' + str(key[1]) + '\t' + str(val) + '\n')

        autoStart(output)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    while True:
        run(None)
        start = QtWidgets.QMessageBox.question(None, 'Correcting Intensities ',
                                               'Next Round?',
                                               QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if start == QtWidgets.QMessageBox.Cancel:
            break
    sys.exit(app.exec_())