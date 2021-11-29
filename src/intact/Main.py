'''
Created on 17 Jul 2020

@author: michael
'''

import os
import subprocess
import traceback
from datetime import datetime

from src.services.DataServices import SequenceService
from src.services.library_services.IntactLibraryBuilder import IntactLibraryBuilder
from src.services.assign_services.Finders import IntactFinder
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.analyser_services.IntactAnalyser import IntactAnalyser
from src.services.export_services.IntactExcelWriter import IntactExcelWriter
from src import path
#from src.gui.ParameterDialogs import IntactStartDialog


def run():
    '''
    Analyses one or more spectra of intact ions:
    1.  Input: txt file, format: m/z, z, relative abundance #ToDo
    2.  Library with theoretical ion masses is created
    3.  Search for ions in uncalibrated spectrum. These are used for internal calibration (automated)
    4.  Search for ions in calibrated spectrum
    5.  Analysis: charge states, modifications/ligands, ...
    6.  Output in xlsx file
    '''
    #dialog = IntactStartDialog()
    settings = ConfigurationHandlerFactory.getIntactHandler().getAll()
    #files = [os.path.join(path, 'Spectral_data','intact', file) for file in settings['spectralData']]
    #print(files)
    #spectralFile = os.path.join(path, 'Spectral_data','intact', settings['spectralData'])

    """theoretical values"""
    print("\n********** calculating theoretical values **********")
    libraryBuilder = IntactLibraryBuilder(SequenceService().get(settings['sequName']), settings['modifications'])
    configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
    for key in ('errorLimitCalib','maxStd', 'k', 'd'):
        settings[key] = configs[key]
    finder = IntactFinder(libraryBuilder.createLibrary(), settings)

    """calibrate spectra"""
    print("\n********** calibrating spectralFile **********")
    #with open(spectralFile) as f:
    #    finder.readData(f)
    finder.readData(settings['spectralData'])
    listOfCalibrationVals = None
    if settings['calibration']:
        listOfCalibrationVals = finder.calibrateAll()

    """find ions"""
    print("\n********** finding ions **********")
    analyser = IntactAnalyser(finder.findIons(settings['k'], settings['d'], True), configs['useAb'])

    """output"""
    print("\n********** output **********")
    output = settings['output']
    if output == '':
        output =  datetime.now().strftime("%d.%m.%Y") + '.xlsx'
    else:
        output = os.path.join(path, 'Spectral_data','intact', output + '.xlsx')
    listOfParameters = []
    for file in settings['spectralData']:
        parameters = {'date:':datetime.now().strftime("%d/%m/%Y %H:%M"), 'data:':file}
        parameters.update(settings)
        del parameters['spectralData']
        listOfParameters.append(parameters)
    excelWriter = IntactExcelWriter(output)
    #abundanceInput = False
    #if settings['inputMode'] != 'intensities':
    #    abundanceInput = True
    avCharges, avErrors, stddevs = analyser.calculateAvChargeAndError()
    try:
        excelWriter.writeIntactAnalysis(listOfParameters, analyser.getSortedIonList(),
                                        avCharges, avErrors, stddevs, listOfCalibrationVals,
                                        analyser.calculateAverageModification(),
                                        analyser.calculateModifications())
        print("saved in:", output)
    except:
        traceback.print_exc()
    finally:
        excelWriter.closeWorkbook()

    try:
        subprocess.call(['open',output])
    except:
        pass
    return 0


if __name__ == '__main__':
    #app = QApplication(sys.argv)
    #dialog = IntactStartDialog()
    #dialog.exec_()
    run()
    #sys.exit(app.exec_())'''