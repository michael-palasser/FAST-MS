'''
Created on 5 Oct 2020

@author: michael
'''
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
        self._worksheet1 = self._workbook.add_worksheet('analysis')
        self._row = 0
        self._format2digit = self._workbook.add_format({'num_format': '0.00'})
        self._lastRow = 0
        self._col = 0

    def writeParameters(self, parameters):
        '''
        Writes all user defined parameters to xlsx file
        :param (dict[str,Any]) parameters: {(str) name: value}
        '''
        self._worksheet1.write(self._row, 0, 'parameters:')
        self._row += 1
        for key,val in parameters.items():
            self._worksheet1.write_row(self._row, 0, [key, val])
            #self.worksheet1.write(self.row,1,val)
            self._row += 1
        self._row += 2

    def writeIons(self, listOfIons):
        '''
        Writes list of observed ion of one spectrum to xlsx file
        :param (list[IntactIon]) listOfIons: list of Ion objects
        '''
        self._worksheet1.write(self._row, 0, 'observed __spectrum:')
        row = self._row + 1
        self._worksheet1.write_row(row, 0, ['m/z', 'z', 'int', 'name', 'error'])
        for ion in listOfIons:
            row += 1
            self._worksheet1.write_row(row, 0, ion.toList())
        if row>self._lastRow:
            self._lastRow = row
        self._col = 6

    def writeAvChargeAndError(self, averageCharge, avError):
        '''
        Writes av. charge and av. error of one spectrum to xlsx file
        :param (float) averageCharge: average charge in a spectrum
        :param (float) avError:  average ppm error in a spectrum
        '''
        self._worksheet1.write(self._row, self._col, 'av.charge:')
        self._worksheet1.write(self._row + 1, self._col, averageCharge, self._format2digit)
        self._worksheet1.write(self._row + 2, self._col, 'av.error:')
        self._worksheet1.write(self._row + 3, self._col, avError, self._format2digit)
        self._col += 2

    def writeAverageMod(self, avModifPerCharge):
        '''
        Writes av. modifications per charge of one spectrum to xlsx file
        :param (dict[int,float]) avModifPerCharge: {charge: av. modification}
        '''
        self._worksheet1.write(self._row, self._col, 'av. number of modifications:')
        self._worksheet1.write_row(self._row + 1, self._col, ['z', 'value'])
        row = self._row + 1
        firstCell = xl_rowcol_to_cell(row + 1, self._col + 1)
        for z,val in avModifPerCharge.items():
            row += 1
            self._worksheet1.write(row, self._col, int(z))
            self._worksheet1.write(row, self._col + 1, val, self._format2digit)
        lastCell = xl_rowcol_to_cell(row, self._col + 1)
        row+=1
        self._worksheet1.write(row, self._col, 'av.')
        self._worksheet1.write(row, self._col + 1, '=AVERAGE(' + firstCell + ':' + lastCell + ')', self._format2digit)
        self._col += 3

    def writeModifications(self, modifications):
        '''
        Writes the percentages of each modification for each charge state in one spectrum to xlsx file
        :param (dict[str,ndarray(dtype=[int,float])]) modifications:
            {modification: 2D array of [(charge,percentage)]}
        '''
        self.percentFormat = self._workbook.add_format({'num_format': '0.0%'})
        self._worksheet1.write(self._row, self._col, 'modifications:')
        self._worksheet1.write(self._row + 1, self._col, 'av.values')
        self._worksheet1.write_row(self._row + 2, self._col, ['mod', 'value'])
        avRow = self._row + 3             #for the averaged values
        currentCol = self._col + 3
        for mod,arr in modifications.items():
            if mod == "":
                mod = "-"
            self._worksheet1.write(self._row + 1, currentCol, mod)
            row = self._row + 2
            self._worksheet1.write_row(row, currentCol, ['z', 'value'])
            for line in arr:
                row +=1
                self._worksheet1.write(row, currentCol, int(line[0]))
                self._worksheet1.write(row, currentCol + 1, line[1], self.percentFormat)
            self._worksheet1.write(avRow, self._col, mod)
            self._worksheet1.write(avRow, self._col + 1, '=AVERAGE(' + xl_rowcol_to_cell(self._row + 3, currentCol + 1)
                                   +':' + xl_rowcol_to_cell(row,currentCol+1) +')', self.percentFormat)
            avRow+=1
            currentCol+=3
            if row>self._lastRow:
                self._lastRow = row
        self._col = currentCol + 3


    def writeAnalysis(self, parameters, listsOfIons, avCharges,avErrors,avModifPerCharges, modificationsInSpectra):
        '''
        Writes the analysis to xlsx file
        :param (dict[str,Any]) parameters: {name: value}
        :param (list[list[IntactIon]]) listsOfIons: observed ions for each spectrum
        :param (list[float]) avCharges: average charges in each spectrum
        :param (list[float]) avErrors: average ppm error in each spectrum
        :param (list[dict[int,float]]) avModifPerCharges: av. modifications {charge: av. modification} in each spectrum
        :param (list[dict[str,ndarray(dtype=[int,float])]]) modificationsInSpectra:
            {modification: 2D array of [(charge,percentage)])} for each spectrum
        '''
        self.writeParameters(parameters)
        for i in range(len(avCharges)):
            self._worksheet1.write(self._row, 0, 'spectralFile ' + str(i + 1))
            self._row+=1
            self.writeIons(listsOfIons[i])
            self.writeAvChargeAndError(avCharges[i], avErrors[i])
            self.writeAverageMod(avModifPerCharges[i])
            self.writeModifications(modificationsInSpectra[i])
            self._row = self._lastRow + 2


    def closeWorkbook(self):
        self._workbook.close()
