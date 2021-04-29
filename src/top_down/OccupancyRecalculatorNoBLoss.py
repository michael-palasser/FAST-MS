import subprocess
import sys

import numpy as np
import os
from re import findall
from datetime import datetime
from PyQt5 import QtWidgets

from src.Services import SequenceService
from src.entities.Ions import Fragment,FragmentIon
from src.gui.StartDialogs import OccupancyRecalcStartDialog
from src.top_down.Analyser import Analyser
from src.top_down.ExcelWriter import BasicExcelWriter
from src import path


def readCsv(file):
    try:
        arr = np.loadtxt(file, delimiter=',', skiprows=1,
                         dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')])
    except ValueError:
        arr = np.loadtxt(file, delimiter='\t', skiprows=1,
                         dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')])
    return arr


def run(mainWindow):
    '''
    Calculates modification/ligand occupancies of a given ion list thereby neglecting base losses.
    Input: csv file
    Output: xlsx file
    :param (PyQt5.QtWidgets.QMainWindow | Any) mainWindow: Qt parent
    '''
    service = SequenceService()
    sequenceName = 'neoRibo'
    sequence = service.get(sequenceName).getSequenceList()
    modification = 'CMCT'
    '''dlg = OccupancyRecalcStartDialog(mainWindow, service.getAllSequenceNames())
    dlg.exec_()
    if dlg and dlg.sequence != None:
        sequenceName = dlg.sequence
        sequence = service.get(dlg.sequence).getSequenceList()
        modification = dlg.modification'''

    """import ion-list"""
    spectralFile = path + 'Spectral_data/Occupancies_in.csv'
    with open(spectralFile, 'w') as f:
        f.write("m/z,z,int,name")
    subprocess.call(['open',spectralFile])
    '''start = QtWidgets.QMessageBox.question(mainWindow, 'Calculating Occupancies ',
        'Paste the ions (format: m/z, z, Int., fragment-name) in the csv-file and press "Ok"',
                                                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
    if start == QtWidgets.QMessageBox.Ok:'''
    input('Press any key')
    arr = readCsv(spectralFile)
    ionList = list()
    speciesList = list()
    print('z\tm/z\tabundance\tassignment')
    for ion in arr:
        baseLoss = False
        for b in ['-G','-A','-C']:
            if b in ion['name']:
                #print('not', ion['name'])
                baseLoss = True
        if not baseLoss:
            print(ion['z'],'\t',ion['m/z'],'\t',ion['intensity']/ion['z'],'\t',ion['name'])
            species = findall(r"([a-z]+)", ion['name'])[0]
            if (species not in speciesList) and (species!=sequenceName):
                speciesList.append(species)
            number = int(findall(r"([0-9]+)", ion['name'])[0])
            if ion['name'].find('+') != -1:
                modif = ion['name'][ion['name'].find('+'):]
            else:
                modif = ""
            newIon = FragmentIon(Fragment(species, number, modif, dict(), [], 0), ion['m/z'], ion['z'], np.zeros(1), 0)
            newIon.setIntensity(ion['intensity'])
            ionList.append(newIon)

    """Analysis and Output"""
    analyser = Analyser(ionList, sequence, 1, modification)
    excelWriter = BasicExcelWriter(os.path.join(path, "Spectral_data","Occupancies_out.xlsx"))
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    excelWriter.worksheet1.write(0,0,date)
    row = excelWriter.writeAbundancesOfSpecies(2, analyser.calculateRelAbundanceOfSpecies())
    excelWriter.writeOccupancies(row, sequence, analyser.calculateOccupancies(speciesList))
    excelWriter.closeWorkbook()
    try:
        subprocess.call(['open', os.path.join(path, "Spectral_data","Occupancies_out.xlsx")])
    except:
        pass
    '''else:
        return'''


if __name__ == '__main__':
    #app = QtWidgets.QApplication(sys.argv)
    run(None)
    #sys.exit(app.exec_())