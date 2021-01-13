'''
Created on 17 Jul 2020

@author: michael
'''

import os
import subprocess
import traceback
from datetime import datetime
from src.FragmentHunter.Main import findSequence
from src.Repositories.IntactRepository import ESI_Repository
from src.LibraryBuilder import ESI_LibraryBuilder
from src.Intact_Ion_Search.Finder import Finder
from src.Repositories.ConfigurationHandler import ConfigHandler
from src.Intact_Ion_Search.ESI_Analyser import Analyser
from src.Intact_Ion_Search.ESI_ExcelWriter import ExcelWriter
from src import path

"""def getMode():
    while True:
        modeInput = input('Positive or negative mode? Enter "+" or "-":')
        if modeInput == '-':
            return -1
        elif modeInput == '+':
            return 1
        else:
            print('Enter "+" or "-":')"""

#if __name__ == '__main__':
def run():
    configHandler = ConfigHandler(os.path.join(path,"src","Intact_Ion_Search","configurations.json"))
    with open(os.path.join(path, 'Parameters','sequences.txt'),'r') as sequenceFile:
        while True:
            sequenceName = configHandler.get('sequName')
            #sequenceName = 'rre2b'
            molecule, sequence = findSequence(sequenceFile, sequenceName)
            if sequence != None:
                break
            else:
                print('not found')

    while True:
        spectralFile = configHandler.get('spectralData')
        #spectralFile = '0207&0607'
        if (spectralFile[-4:] != '.txt') and (spectralFile[-4:] != '.csv'):
            spectralFile += '.txt'
        spectralFile = os.path.join(path, 'Spectral_data','ESI', spectralFile)
        if os.path.isfile(spectralFile):
            break
        else:
            print(spectralFile,"not found")


    """theoretical values"""
    print("\n********** calculating theoretical values **********")
    libraryBuilder = ESI_LibraryBuilder(sequenceName, sequence, molecule, configHandler.get('modification'))
    moleculeFile = os.path.join(path, 'Parameters', molecule+'.txt')
    if not os.path.isfile(moleculeFile):
        raise Exception('molecule in sequences.txt unknown')


    with open(moleculeFile, mode="r") as f:
        libraryBuilder.readMoleculeFile(f)
    #with openAgain(os.path.join(path,'Parameters','intact_modifications.txt'), mode="r") as f:
    finder = Finder(libraryBuilder.createLibrary(ESI_Repository().getPatternWithObjects(
        configHandler.get('modification'))),configHandler)

    """calibrate spectra"""
    print("\n********** calibrating spectralFile **********")
    with open(spectralFile) as f:
        finder.readData(f)
    finder.calibrate()

    """find spectrum"""
    print("\n********** finding spectrum **********")
    analyser = Analyser(finder.findIons(configHandler.get('k'),configHandler.get('d'),1))

    """output"""
    print("\n********** output **********")
    output = configHandler.get('output')
    if output == '':
        output = spectralFile[0:-4] + '_out' + '.xlsx'
    else:
        output = os.path.join(path, 'Spectral_data','ESI', output + '.xlsx')
    parameters = {'pattern:':spectralFile,'date:':datetime.now().strftime("%d/%m/%Y %H:%M")}
    parameters.update(configHandler.getAll())
    excelWriter = ExcelWriter(output)
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
    run()