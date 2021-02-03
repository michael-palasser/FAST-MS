'''
Created on 5 Oct 2020

@author: michael
'''
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


class IntactExcelWriter(object):
    '''

    '''
    def __init__(self, file):
        self.workbook = xlsxwriter.Workbook(file)
        self.worksheet1 = self.workbook.add_worksheet('analysis')
        self.row = 0
        self.format2digit = self.workbook.add_format({'num_format': '0.00'})
        self.lastRow = 0
        self.col = 0

    def writeParameters(self, parameters):
        self.worksheet1.write(self.row,0,'parameters:')
        self.row += 1
        for key,val in parameters.items():
            self.worksheet1.write_row(self.row,0,[key,val])
            #self.worksheet1.write(self.row,1,val)
            self.row += 1
        self.row += 2

    def writeIons(self, listOfIons):
        self.worksheet1.write(self.row,0,'observed __spectrum:')
        row = self.row+1
        self.worksheet1.write_row(row,0,['m/z','z','int','name','error'])
        for ion in listOfIons:
            row += 1
            self.worksheet1.write_row(row,0, ion.toList())
        if row>self.lastRow:
            self.lastRow = row
        self.col = 6

    def writeAvChargeAndError(self, averageCharge, avError):
        self.worksheet1.write(self.row,self.col,'av.charge:')
        self.worksheet1.write(self.row+1,self.col,averageCharge,self.format2digit)
        self.worksheet1.write(self.row+2,self.col,'av.error:')
        self.worksheet1.write(self.row+3,self.col,avError,self.format2digit)
        self.col += 2

    def writeAverageMod(self, avModifPerCharge):
        self.worksheet1.write(self.row,self.col,'av. number of modifications:')
        self.worksheet1.write_row(self.row+1,self.col,['z','value'])
        row = self.row+1
        firstCell = xl_rowcol_to_cell(row+1,self.col+1)
        for z,val in avModifPerCharge.items():
            row += 1
            self.worksheet1.write(row,self.col,int(z))
            self.worksheet1.write(row,self.col+1,val,self.format2digit)
        lastCell = xl_rowcol_to_cell(row,self.col+1)
        row+=1
        self.worksheet1.write(row, self.col,'av.')
        self.worksheet1.write(row,self.col+1, '=AVERAGE('+firstCell+':'+lastCell+')',self.format2digit)
        self.col += 3

    def writeModifications(self, modifications):
        self.percentFormat = self.workbook.add_format({'num_format': '0.0%'})
        self.worksheet1.write(self.row,self.col,'modifications:')
        self.worksheet1.write(self.row+1,self.col,'av.values')
        self.worksheet1.write_row(self.row+2,self.col,['mod','value'])
        avRow = self.row+3             #for the averaged values
        currentCol = self.col+3
        for mod,arr in modifications.items():
            if mod == "":
                mod = "-"
            self.worksheet1.write(self.row+1,currentCol,mod)
            row = self.row+2
            self.worksheet1.write_row(row,currentCol,['z','value'])
            for line in arr:
                row +=1
                self.worksheet1.write(row, currentCol, int(line[0]))
                self.worksheet1.write(row, currentCol+1, line[1],self.percentFormat)
            self.worksheet1.write(avRow,self.col,mod)
            self.worksheet1.write(avRow,self.col+1,'=AVERAGE('+xl_rowcol_to_cell(self.row+3,currentCol+1)
                                  +':'+xl_rowcol_to_cell(row,currentCol+1)+')',self.percentFormat)
            avRow+=1
            currentCol+=3
            if row>self.lastRow:
                self.lastRow = row
        self.col = currentCol+3


    def writeAnalysis(self, parameters, listsOfIons, avCharges,avErrors,avModifPerCharges, modificationsInSpectra):
        self.writeParameters(parameters)
        for i in range(len(avCharges)):
            self.worksheet1.write(self.row, 0, 'spectralFile '+str(i+1))
            self.row+=1
            self.writeIons(listsOfIons[i])
            self.writeAvChargeAndError(avCharges[i], avErrors[i])
            self.writeAverageMod(avModifPerCharges[i])
            self.writeModifications(modificationsInSpectra[i])
            self.row = self.lastRow + 2


    def closeWorkbook(self):
        self.workbook.close()
