'''
Created on 21 Jul 2020

@author: michael
'''

import os
import subprocess
import traceback
import sys
import time
import re
from src.ConfigurationHandler import ConfigHandler
from src.FragmentHunter.Analyser import Analyser
from src.LibraryBuilder import FragmentLibraryBuilder
from src.FragmentHunter.SpectrumHandler import SpectrumHandler
from src.FragmentHunter.IntensityModeller import IntensityModeller
from src.FragmentHunter.TDExcelWriter import ExcelWriter
from src import path



def findSequence(file, name):
    '''
    finds sequence
    :param file: file with stored sequences
    :param name: sequence name
    :return: molecule, list of sequence, respectively None,None if sequence was not found
    '''
    for line in file:
        line = line.rstrip()
        lineList = line.split()
        if lineList[0] == name:
            return lineList[1],re.findall('[A-Z][^A-Z]*', lineList[2])
    return None,None


def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.charge))

#if __name__ == '__main__':
def run():
    settings = ConfigHandler(os.path.join(path,"src","FragmentHunter","settings.json")).getAll()
    configs = ConfigHandler(os.path.join(path,"src","FragmentHunter","configurations.json")).getAll()
    with open(os.path.join(path, 'Parameters','sequences.txt'),'r') as sequenceFile:
            molecule, sequence = findSequence(sequenceFile, settings['sequName'])
            if sequence != None:
                if molecule in ['P','peptide','protein']:
                    molecule = 'protein'
            else:
                raise Exception('Sequence not found')
    modificationType = settings['modification']
    maxMod = 1
    if settings['modification'] == '':
        maxMod = 0
    elif (settings['modification'][0].isdigit()) and not (settings['modification'][1].isdigit()):                     #bei DEPC fkt da inpmod[1] immer Zahl ist
            maxMod = int(settings['modification'][0])
            modificationType = settings['modification'][1:]
    spectralFile = settings['spectralData']
    if (spectralFile[-4:] != '.txt') and (spectralFile[-4:] != '.csv'):
        spectralFile += '.txt'
    spectralFile = os.path.join(path, 'Spectral_data','top-down', spectralFile)
    if not os.path.isfile(spectralFile):
        raise Exception(spectralFile,"not found")
    if settings['noiseLimit'] <= 0:
        raise Exception('noiseLimit must be > 0!')


    """create ion ladder"""
    moleculePath = os.path.join(path, 'Parameters', molecule)
    moleculeFile = moleculePath + '.txt'
    if (not os.path.isdir(moleculePath + '-fragmentation/' )) or (not os.path.isfile(moleculeFile)):
        raise Exception('molecule in sequences.txt unknown')
    fragmentFile = os.path.join(moleculePath + '-fragmentation', settings['dissociation'])
    if modificationType != "":
        fragmentFile += '_'+ modificationType + '.txt'
    else:
        fragmentFile += '.txt'


    libraryBuilder = FragmentLibraryBuilder(settings['sequName'], sequence, molecule, modificationType, maxMod)
    with open(fragmentFile, mode="r") as fragFile:
        libraryBuilder.readFragmentationFile(fragFile)
    with open(moleculeFile, mode="r") as f:
        libraryBuilder.readMoleculeFile(f)
    print("\n********** Creating fragment library **********")
    libraryBuilder.createFragmentLibrary()
    print()

    """read existing ion-list file or create new one"""
    fragmentLibraryFile = os.path.join(path, 'Fragment_lists', settings['dissociation'] + '_'+ settings['sequName'])
    if modificationType != "":
        fragmentLibraryFile +=  "_" + settings['modification'] + ".csv"
    else:
        fragmentLibraryFile += ".csv"
    libraryImported = False
    if os.path.isfile(fragmentLibraryFile):
        with open(fragmentLibraryFile, mode='r') as f:
            print("\n********** Importing list of isotope patterns from:", fragmentLibraryFile, "**********")
            try:
                libraryBuilder.addIsotopePatternFromFile(f)
                print("done")
                libraryImported = True
            except:
                traceback.print_exc()
                print("Problem with importing list of isotope patterns")
                creatingNew = input("Should a new List be created? Press \'y\', otherwise the program will be stopped")
                if creatingNew != 'y':
                    sys.exit()
    if libraryImported == False:
        start = time.time()
        print("\n********** Writing new list of isotope patterns to:",fragmentLibraryFile,"**********\n")
        libraryBuilder.addNewIsotopePattern()
        with open(fragmentLibraryFile, mode="w") as f:
            libraryBuilder.saveIsotopePattern(f)
        print("\ndone\nexecution time: ",round((time.time() - start)/60,2),"min\n")

    """Importing spectral data"""
    print("\n********** Importing spectral data from:", spectralFile, "**********")
    with open(spectralFile, mode='r') as f:
        spectrumHandler = SpectrumHandler(molecule, sequence, libraryBuilder.fragmentLibrary,
                                          libraryBuilder.getChargedModifications(), settings)
        if spectralFile[-4:] == '.csv':
            spectrumHandler.addSpectrumFromCsv(f)
        else:
            spectrumHandler.addSpectrum(f)


    """Finding fragments"""
    print("\n********** Search for spectrum **********")
    start = time.time()
    spectrumHandler.findPeaks()
    print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

    intensityModeller = IntensityModeller(configs)
    start = time.time()
    print("\n********** Calculating relative abundances **********")
    for ion in spectrumHandler.foundIons:
        intensityModeller.processIons(ion)
    for ion in spectrumHandler.ionsInNoise:
        print("hey",ion.getName())
        intensityModeller.processNoiseIons(ion)
    print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

    """Handle spectrum with same monoisotopic peak and charge"""
    print("\n********** Handling overlaps **********")
    for overlap in intensityModeller.findSameMonoisotopics():
        print('index\t m/z\t\t\tz\tI\t\t\tfragment\t\terror /ppm\tquality')
        for i in range(len(overlap)):
            print(i+1, end=':\t\t')
            print(overlap[i].toString())
        while True:
            try:
                indexKeptIon = int(input("Enter the index of the fragment you want to keep:"))
                if indexKeptIon <= len(overlap):
                    intensityModeller.correctedIons[intensityModeller.getHash(overlap[indexKeptIon - 1])].comment = "mono."
                    del overlap[indexKeptIon - 1]
                    for deletedIon in overlap:
                        intensityModeller.deleteIon(deletedIon)
                    break
                else:
                    print('Index not found')
            except:
                #print(intensityModeller.getHash(overlap[indexKeptIon - 1]))
                print('Enter Index')
        print("\n")


    """remodelling overlaps"""
    print("\n********** Re-modelling overlaps **********")
    intensityModeller.remodelIntensity()

    """analysis"""
    analyser = Analyser(list(intensityModeller.correctedIons.values()),sequence,modificationType, settings)

    """output"""
    output = settings.get('output')
    if output == '':
        output = spectralFile[0:-4] + '_out' + '.xlsx'
    else:
        output = os.path.join(path, 'Spectral_data','top-down', output + '.xlsx')
    excelWriter = ExcelWriter(output, configs)
    strMode = 'negative'
    if settings['sprayMode'] == 1:
        strMode = 'positive'
    try:
        generalParam = [("spectralFile:", spectralFile), ('date:', ""),
                        ('noiseLimit:', settings['noiseLimit']),
                        ('outlier_limit:', configs['outlierLimit']),
                        ('shape_limit:', configs['shapeDel']),
                        ('mode:',strMode)]
        #percentages = list()
        excelWriter.writeAnalysis(generalParam,
                                  analyser.getModificationLoss(),
                                  analyser.calculateRelAbundanceOfSpecies(),
                                  sequence,
                                  analyser.calculatePercentages(configs['interestingIons']))
        #analyser.createPlot(maxMod)
        precursorRegion = intensityModeller.getPrecRegion(settings['sequName'], settings['charge'])
        excelWriter.writeIons(excelWriter.worksheet2, intensityModeller.correctedIons.values(),
                              precursorRegion)
        excelWriter.writePeaks(excelWriter.worksheet3,0,0,intensityModeller.correctedIons.values())
        row = excelWriter.writeIons(excelWriter.worksheet4, sortIonsByName(intensityModeller.deletedIons),
                              precursorRegion)
        excelWriter.writePeaks(excelWriter.worksheet4,row+3,0,sortIonsByName(intensityModeller.deletedIons))
        excelWriter.writeIons(excelWriter.worksheet5, sortIonsByName(intensityModeller.remodelledIons),
                              precursorRegion)
        excelWriter.writeSumFormulas(libraryBuilder.fragmentLibrary, spectrumHandler.searchedChargeStates)
        print("********** saved in:", output, "**********\n")
    finally:
        excelWriter.closeWorkbook()
    try:
        subprocess.call(['open',output])
    except:
        pass
    return 0

if __name__ == '__main__':
    run()