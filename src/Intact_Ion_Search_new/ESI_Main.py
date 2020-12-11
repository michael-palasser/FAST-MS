'''
Created on 17 Jul 2020

@author: michael
'''

import os
import traceback
from datetime import datetime
from src.FragmentHunter.Main import findSequence
from src.LibraryBuilder import ESI_LibraryBuilder
from src.Intact_Ion_Search.Finder import Finder
from src.ParameterHandler import ParameterHandler
#from src.ConfigurationHandler import ConfigHandler
from src.Intact_Ion_Search.ESI_Analyser import Analyser
from src.Intact_Ion_Search.ESI_ExcelWriter import ExcelWriter
from src import path

def getMode():
    while True:
        modeInput = input('Positive or negative mode? Enter "+" or "-":')
        if modeInput == '-':
            return -1
        elif modeInput == '+':
            return 1
        else:
            print('Enter "+" or "-":')


#if __name__ == '__main__':
def main():
    """inputs"""
    print("********** Inputs **********\n")
    parameterHandler = ParameterHandler()
    with open(path + 'Parameters/parameters_intact.txt','r') as f:
        parameterHandler.readParameters(f)
    with open(path + 'Parameters/sequences.txt','r') as sequenceFile:
        while True:
            sequenceName = input('Enter sequence name: ')
            #sequenceName = 'rre2b'
            molecule, sequence = findSequence(sequenceFile, sequenceName)
            if sequence != None:
                break
            else:
                print('not found')

    modification = input('Modification: ')
    #modification = 'CMCT'
    mode = getMode()
    while True:
        spectralFile = input('Spectral data: ')
        #spectralFile = '0207&0607'
        if (spectralFile[-4:] != '.txt') and (spectralFile[-4:] != '.csv'):
            spectralFile += '.txt'
        spectralFile = path + 'Spectral_data/ESI/' + spectralFile
        if os.path.isfile(spectralFile):
            break
        else:
            print(spectralFile,"not found")


    """theoretical values"""
    print("\n********** calculating theoretical values **********")
    libraryBuilder = ESI_LibraryBuilder(sequenceName, sequence, molecule, modification)
    moleculeFile = path + 'Parameters/' + molecule + '.txt'
    if not os.path.isfile(moleculeFile):
        raise Exception('molecule in sequences.txt unknown')


    with open(moleculeFile, mode="r") as f:
        libraryBuilder.readMoleculeFile(f)
    with open(path +'Parameters/intact_modifications.txt', mode="r") as f:
        finder = Finder(sequenceName, libraryBuilder.createLibrary(f), mode, parameterHandler)

    """calibrate spectra"""
    print("\n********** calibrating spectralFile **********")
    with open(spectralFile) as f:
        finder.readData(f)
    finder.calibrate(finder.findIons(parameterHandler.getNumber('errorLimitCalib'), 0),
                     parameterHandler.getNumber('errorLimitCalib'))

    """find ions"""
    print("\n********** finding spectrum **********")
    #ToDo: variable error
    analyser = Analyser(finder.findIons(parameterHandler.getNumber('errorLimit'),1))

    """output"""
    print("\n********** output **********")
    output = input('name of output file: ')
    if output == '':
        output = spectralFile[0:-4] + '_out' + '.xlsx'
    else:
        output = path + 'Spectral_data/ESI/' + output + '.xlsx'
    parameters = {'data:':spectralFile,'date:':datetime.now().strftime("%d/%m/%Y %H:%M")}
    parameters.update(parameterHandler.parameters)
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
    return 0
