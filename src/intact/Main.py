'''
Created on 17 Jul 2020

@author: michael
'''

import os
import subprocess
import traceback
from datetime import datetime


from src.intact.LibraryBuilder import IntactLibraryBuilder
from src.intact.Finder import Finder
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.intact.Analyser import IntactAnalyser
from src.intact.ExcelWriter import IntactExcelWriter
from src import path
#from src.views.ParameterDialogs import IntactStartDialog


def run():
    #dialog = IntactStartDialog()
    configHandler = ConfigurationHandlerFactory.getIntactHandler()
    spectralFile = os.path.join(path, 'Spectral_data','intact', configHandler.get('spectralData'))

    """theoretical values"""
    print("\n********** calculating theoretical values **********")
    libraryBuilder = IntactLibraryBuilder(configHandler.get('sequName'), configHandler.get('modification'))
    finder = Finder(libraryBuilder.createLibrary(),configHandler)

    """calibrate spectra"""
    print("\n********** calibrating spectralFile **********")
    with open(spectralFile) as f:
        finder.readData(f)
    finder.calibrate()

    """find spectrum"""
    print("\n********** finding spectrum **********")
    analyser = IntactAnalyser(finder.findIons(configHandler.get('k'), configHandler.get('d'), 1))

    """output"""
    print("\n********** output **********")
    output = configHandler.get('output')
    if output == '':
        output = spectralFile[0:-4] + '_out' + '.xlsx'
    else:
        output = os.path.join(path, 'Spectral_data','intact', output + '.xlsx')
    parameters = {'pattern:':spectralFile,'date:':datetime.now().strftime("%d/%m/%Y %H:%M")}
    parameters.update(configHandler.getAll())
    excelWriter = IntactExcelWriter(output)
    avCharges, avErrors = analyser.calculateAvChargeAndError()
    try:
        excelWriter.writeAnalysis(parameters, analyser.getIonList(),
                                  avCharges,avErrors,
                                  analyser.calculateAverageModification(),
                                  analyser.calculateModifications())
        print("saved in:", output)
    except:
        traceback.print_exc()
    finally:
        excelWriter.closeWorkbook()

    try:
        subprocess.call(['openAgain',output])
    except:
        pass
    return 0


if __name__ == '__main__':
    #app = QApplication(sys.argv)
    #dialog = IntactStartDialog()
    #dialog.exec_()
    run()
    #sys.exit(app.exec_())