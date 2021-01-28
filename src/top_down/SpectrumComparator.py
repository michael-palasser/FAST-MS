'''
Created on 15 Oct 2020

@author: michael
'''
import subprocess

import numpy as np
import xlsxwriter
from datetime import datetime
from src import path

def removeEmptyElements(rawList):
    newList = rawList
    while '' in newList:
        newList.remove('')
    return newList


def getHash(name, z):   #ToDo: DRY
    return name+'_'+format(z,"02d")

def deHash(hash):
    name = hash[:hash.find('_')]
    z = int(hash[hash.find('_')+1:])
    return (name,z)

def run():
    spectralFiles = list()
    #spectralFiles = ['0107.txt','0707.txt','0807.txt','0907.txt']
    while True:
        fileName = input('Enter file name: ')
        if fileName == '':
            break
        else:
            if fileName[:-4] != '.txt':
                fileName += '.txt'
            spectralFiles.append(fileName)

    spectra = list()
    ions = dict()
    for spectralFile in spectralFiles:
        spectrum = list()
        with open(path+'Spectral_data/Comparison/'+spectralFile) as f:
            for line in f:
                if line.startswith('m/z'):
                    continue
                items = tuple(removeEmptyElements(line.rstrip().split()))
                spectrum.append(items)
                ionHash = getHash(items[3],int(items[1]))
                if ionHash in ions:
                    ions[ionHash].append(spectralFile)
                else:
                    ions[ionHash] = [spectralFile]
        spectra.append(np.array(spectrum,
                                dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')]))

    outputName = input('Name of output file: ')
    if outputName == '':
        date = datetime.now().strftime("%d%m%Y")
        output = path + 'Spectral_data/Comparison/' + date + '_out' + '.xlsx'
    else:
        output = path + 'Spectral_data/Comparison/' + outputName + '.xlsx'

    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    worksheet.write_row(0,0,['analysis:',datetime.now().strftime("%d/%m/%Y")])
    worksheet.write_row(3,0,['fragment','z'])
    worksheet.write_row(3,3,spectralFiles)
    row = 4

    cell_format=workbook.add_format()
    cell_format.set_bg_color('green')
    red = workbook.add_format({'bold': True, 'font_color': 'red'})
    green = workbook.add_format({'bold': True, 'font_color': 'green'})
    for ionHash in sorted(list(ions.keys())):
        col = 3
        counter = 0
        for spectralFile in spectralFiles:
            if spectralFile in ions[ionHash]:
                counter += 1
                worksheet.write(row,col,1,cell_format)
            col+=1
        if 1 > (counter / (col -3)) > 0.66:
            worksheet.write_row(row, 0, deHash(ionHash), green)
        elif (counter / (col -3)) < 0.34:
            worksheet.write_row(row, 0, deHash(ionHash), red)
        else:
            worksheet.write_row(row, 0, deHash(ionHash))
        row+=1
    workbook.close()
    subprocess.call(['open', output])
    print("********** saved in:", output, "**********\n")

if __name__ == '__main__':
    run()