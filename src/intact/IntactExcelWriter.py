'''
Created on 5 Oct 2020

@author: michael
'''
import os

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


class IntactExcelWriter(object):
    '''
    Responsible for output of intact ion search to xlsx file
    '''
    def __init__(self, file):
        '''
        :param (str) file: path of xlsx output file
        '''
        self._workbook = xlsxwriter.Workbook(file)
        #self._worksheet1 = self._workbook.add_worksheet('analysis')
        self._row = 0
        self._format2digit = self._workbook.add_format({'num_format': '0.00'})
        self._lastRow = 0
        self._col = 0

    def writeParameters(self, worksheet, parameters):
        '''
        Writes all user defined parameters to xlsx file
        :param (dict[str,Any]) parameters: {(str) name: value}
        '''
        worksheet.write(self._row, 0, 'parameters:')
        self._row += 1
        for key,val in parameters.items():
            worksheet.write_row(self._row, 0, [key, val])
            #worksheet.write(self.row,1,val)
            self._row += 1
        self._row += 2

    def writeIons(self, worksheet, listOfIons):
        '''
        Writes list of observed ion of one spectrum to xlsx file
        :param (list[IntactIon]) listOfIons: list of Ion objects
        '''
        worksheet.write(self._row, 0, 'observed ions:')
        row = self._row + 1
        worksheet.write_row(row, 0, ['m/z', 'z', 'int', 'name', 'error'])
        for ion in listOfIons:
            row += 1
            worksheet.write_row(row, 0, ion.toList())
        if row>self._lastRow:
            self._lastRow = row
        self._col = 6

    def writeGeneralAnalysis(self, worksheet, averageCharge, avError, stdDevOfErrors, calibrationVals):
        '''
        Writes av. charge and the values of the calibration (av. error, std. dev. of the errors, and the parameters of
        the calibration function) of one spectrum to xlsx file
        :param (float) averageCharge: average charge in a spectrum
        :param (float) avError:  average ppm error in a spectrum
        :param (float) stdDevOfErrors:  std. dev. of the ppm errors in a spectrum
        :param (tuple[float]) calibrationVals: the parameters (a,b,c) of the calibration function: y=ax^2+bx+c
        '''
        worksheet.write(self._row, self._col, 'av.charge:')
        worksheet.write(self._row + 1, self._col, averageCharge, self._format2digit)
        worksheet.write(self._row + 3, self._col, 'calibration:')
        worksheet.write(self._row + 4, self._col, 'av.error:')
        worksheet.write(self._row + 4, self._col+1, avError, self._format2digit)
        worksheet.write(self._row + 5, self._col, 'std.dev.:')
        worksheet.write(self._row + 5, self._col+1, stdDevOfErrors, self._format2digit)
        row = self._row + 6
        for i,key in enumerate(('a','b','c')):
            worksheet.write(row + i, self._col, key)
            worksheet.write(row + i, self._col+1, calibrationVals[i])
        self._col += 2

    def writeAverageMod(self, worksheet, avModifPerCharge):
        '''
        Writes av. modifications per charge of one spectrum to xlsx file
        :param (dict[int,float]) avModifPerCharge: {charge: av. modification}
        '''
        worksheet.write(self._row, self._col, 'av. number of modifications:')
        worksheet.write_row(self._row + 1, self._col, ['z', 'value'])
        row = self._row + 1
        firstCell = xl_rowcol_to_cell(row + 1, self._col + 1)
        for z,val in avModifPerCharge.items():
            row += 1
            worksheet.write(row, self._col, int(z))
            worksheet.write(row, self._col + 1, val, self._format2digit)
        lastCell = xl_rowcol_to_cell(row, self._col + 1)
        row+=1
        worksheet.write(row, self._col, 'av.')
        worksheet.write(row, self._col + 1, '=AVERAGE(' + firstCell + ':' + lastCell + ')', self._format2digit)
        self._col += 3

    def writeModifications(self, worksheet, modifications):
        '''
        Writes the percentages of each modification for each charge state in one spectrum to xlsx file
        :param (dict[str,ndarray(dtype=[int,float])]) modifications:
            {modification: 2D array of [(charge,percentage)]}
        '''
        self.percentFormat = self._workbook.add_format({'num_format': '0.0%'})
        worksheet.write(self._row, self._col, 'modifications:')
        worksheet.write(self._row + 1, self._col, 'av.values')
        worksheet.write_row(self._row + 2, self._col, ['mod', 'value'])
        avRow = self._row + 3             #for the averaged values
        currentCol = self._col + 3
        for mod,arr in modifications.items():
            if mod == "":
                mod = "-"
            worksheet.write(self._row + 1, currentCol, mod)
            row = self._row + 2
            worksheet.write_row(row, currentCol, ['z', 'value'])
            for line in arr:
                row +=1
                worksheet.write(row, currentCol, int(line[0]))
                worksheet.write(row, currentCol + 1, line[1], self.percentFormat)
            worksheet.write(avRow, self._col, mod)
            worksheet.write(avRow, self._col + 1, '=AVERAGE(' + xl_rowcol_to_cell(self._row + 3, currentCol + 1)
                                   +':' + xl_rowcol_to_cell(row,currentCol+1) +')', self.percentFormat)
            avRow+=1
            currentCol+=3
            if row>self._lastRow:
                self._lastRow = row
        self._col = currentCol + 3


    def writeAnalysis(self, listOfParameters, listsOfIons, avCharges,avErrors, stdDevsOfErrors, listOfCalibrationVals,
                      avModifPerCharges, modificationsInSpectra):
        '''
        Writes the analysis to xlsx file
        :param (list[dict[str,Any]]) parameters: lists of {name: value}
        :param (list[list[list[IntactIon]]]) listsOfIons: observed ions for each spectrum
        :param (list[list[float]]) avCharges: average charges in each spectrum
        :param (list[list[float]]) stdDevsOfErrors: list of std. dev. of the ppm errors in each spectrum
        :param (list[list[tuple[float]]]) listOfCalibrationVals: list of the parameters (a,b,c) of the calibration
            function (y=ax^2+bx+c) for each spectrum
        :param (list[list[dict[int,float]]]) avModifPerCharges: av. modifications {charge: av. modification} in each
            spectrum
        :param (list[list[dict[str,ndarray(dtype=[int,float])]]]) modificationsInSpectra:
            {modification: 2D array of [(charge,percentage)])} for each spectrum
        '''
        self._worksheets = [self._workbook.add_worksheet() for _ in range(len(listOfParameters))]
        '''for parameters in listOfParameters:
            name = os.path.split(parameters['data:'])[-1][:-4]
            self._workbook.add_worksheet(name)'''
        for i,worksheet in enumerate(self._worksheets):
            self._row = 0
            self._lastRow = 0
            self._col = 0
            self.writeParameters(worksheet, listOfParameters[i])
            for j in range(len(avCharges[i])):
                worksheet.write(self._row, 0, 'spectralFile ' + str(j + 1))
                self._row+=1
                self.writeIons(worksheet, listsOfIons[i][j])
                self.writeGeneralAnalysis(worksheet, avCharges[i][j], avErrors[i][j], stdDevsOfErrors[i][j],
                                          listOfCalibrationVals[i][j])
                self.writeAverageMod(worksheet, avModifPerCharges[i][j])
                self.writeModifications(worksheet, modificationsInSpectra[i][j])
                self._row = self._lastRow + 2
                print(j)


    def closeWorkbook(self):
        self._workbook.close()
