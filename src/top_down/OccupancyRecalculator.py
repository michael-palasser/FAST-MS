import subprocess
import sys

import numpy as np
import os
from re import findall
from PyQt5 import QtWidgets

from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.DataServices import SequenceService
from src.entities.Ions import Fragment,FragmentIon
from src.gui.dialogs.StartDialogs import OccupancyRecalcStartDialog
from src.services.analyser_services.Analyser import Analyser
from src.services.export_services.ExcelWriter import BasicExcelWriter
from src.resources import path


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
    Calculates modification/ligand occupancies of a given ion list.
    Input: csv file
    Output: xlsx file
    :param (PyQt5.QtWidgets.QMainWindow | Any) mainWindow: Qt parent
    '''
    service = SequenceService()
    configs = ConfigurationHandlerFactory().getConfigHandler().getAll()
    dlg = OccupancyRecalcStartDialog(mainWindow, service.getAllSequenceNames())
    dlg.exec_()
    if dlg and dlg.getSequence() != None:
        sequenceName = dlg.getSequence()
        sequence = service.get(sequenceName).getSequenceList()
        modification = dlg.getModification()

        """import ion-list"""
        spectralFile = os.path.join(path, 'Spectral_data','Occupancies_in.csv')
        with open(spectralFile, 'w') as f:
            f.write("m/z,z,int,name")
        subprocess.call(['open',spectralFile])
        start = QtWidgets.QMessageBox.question(mainWindow, 'Calculating Occupancies ',
            'Paste the ions (format: m/z, z, Int., fragment-name) in the csv-file and press "Ok"',
                                                        QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if start == QtWidgets.QMessageBox.Ok:
            arr = readCsv(spectralFile)
            ionList = list()
            speciesList = list()
            for ion in arr:
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
            analyser = Analyser(ionList, sequence, 1, modification, configs['useAb'])
            excelWriter = BasicExcelWriter(os.path.join(path, "Spectral_data","Occupancies_out.xlsx"), modification)
            excelWriter.writeDate()
            row = excelWriter.writeAbundancesOfSpecies(2, analyser.calculateRelAbundanceOfSpecies()[0])
            excelWriter.addOccupOrCharges(0,row, sequence,
                                  analyser.calculateOccupancies(speciesList)[0],1) #ToDo
            excelWriter.closeWorkbook()
            try:
                subprocess.call(['open', os.path.join(path, "Spectral_data","Occupancies_out.xlsx")])
            except:
                pass
        else:
            return
    else:
        return


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    run(None)
    sys.exit(app.exec_())