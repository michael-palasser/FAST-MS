import subprocess

import numpy as np
import os
import re
from datetime import datetime

from src.top_down.Main import findSequence
from src.entities.Fragment import Fragment,Ion
from src.top_down.Analyser import Analyser
from src.top_down.TDExcelWriter import BasicExcelWriter
from src import path
from src.repositories.ConfigurationHandler import ConfigHandler

def run():
    """openAgain everything"""
    with open(path + 'Parameters/sequences.txt', 'r') as sequenceFile:
        sequenceName = input('Enter sequence name: ')
        molecule, sequence = findSequence(sequenceFile, sequenceName)
    if sequence != None:
        if molecule in ['P', 'peptide', 'protein']:
            molecule = 'protein'
    else:
        raise Exception('Sequence not found')
    precModification = input('Enter modification: ')

    """import ion-list"""
    spectralFile = path + 'Spectral_data/Occupancies_in.csv'
    with open(spectralFile, 'w') as f:
        pass
    subprocess.call(['open',spectralFile])
    input('Press any key to start')
    try:
        arr = np.loadtxt(spectralFile, delimiter=',', skiprows=1,
                         dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')])
    except ValueError:
        arr = np.loadtxt(spectralFile, delimiter='\t', skiprows=1,
                         dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')])
    ionList = list()
    speciesList = list()
    for ion in arr:
        species = re.findall(r"([a-z]+)", ion['name'])[0]
        if (species not in speciesList) and (species!=sequenceName):
            speciesList.append(species)
        number = int(re.findall(r"([0-9]+)", ion['name'])[0])
        if ion['name'].find('+') != -1:
            modification = ion['name'][ion['name'].find('+'):]
        else:
            modification = ""
        newIon = Ion(Fragment(species, number, modification, dict(), []), ion['z'], np.zeros(1), 0)
        newIon.intensity = ion['intensity']
        ionList.append(newIon)

    """Analysis and Output"""
    analyser = Analyser(ionList, sequence,precModification,
                        ConfigHandler(os.path.join(path,"src","top_down","data","configurations.json"))
                            .getAll())
    excelWriter = BasicExcelWriter(os.path.join(path, "Spectral_data","Occupancies_out.xlsx"))
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    excelWriter.worksheet1.write(0,0,date)
    row = excelWriter.writeAbundancesOfSpecies(2, analyser.calculateRelAbundanceOfSpecies())
    excelWriter.writeOccupancies(row,sequence,analyser.calculatePercentages(speciesList))
    excelWriter.closeWorkbook()
    try:
        subprocess.call(['open', os.path.join(path, "Spectral_data","Occupancies_out.xlsx")])
    except:
        pass

if __name__ == '__main__':
    run()