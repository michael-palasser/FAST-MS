'''
Created on 5 Oct 2020

@author: michael
'''
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

from src.services.export_services.ExcelWriter import ExcelWriter


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
        :param (list[SimpleIntactIon]) listOfIons: list of Ion objects
        '''
        worksheet.write(self._row, 0, 'observed ions:')
        row = self._row + 1
        headers = ('m/z', 'z', 'int', 'int/z','name', 'error')
        worksheet.write_row(row, 0, headers)
        for ion in listOfIons:
            row += 1
            worksheet.write_row(row, 0, ion.toList())
        if row>self._lastRow:
            self._lastRow = row
        self._col = len(headers)+1

    def writeGeneralAnalysis(self, worksheet, averageCharge, avError, stdDevOfErrors, calibrationVals):
        '''
        Writes av. charge and the values of the calibration (av. error, std. dev. of the errors, and the parameters of
        the calibration function) of one spectrum to xlsx file
        :param (tuple[float,float]) averageCharge: average charge in a spectrum
        :param (float) avError:  average ppm error in a spectrum
        :param (float) stdDevOfErrors:  std. dev. of the ppm errors in a spectrum
        :param (tuple[float]) calibrationVals: the parameters (a,b,c) of the calibration function: y=ax^2+bx+c
        '''
        worksheet.write(self._row, self._col+1, 'av.charge:')
        worksheet.write(self._row+1, self._col, 'using int')
        worksheet.write(self._row + 1, self._col+1, averageCharge[0], self._format2digit)
        worksheet.write(self._row+2, self._col, 'using int/z')
        worksheet.write(self._row + 2, self._col+1, averageCharge[1], self._format2digit)
        worksheet.write(self._row + 4, self._col, 'calibration:')
        worksheet.write(self._row + 5, self._col, 'av.error:')
        worksheet.write(self._row + 5, self._col+1, avError, self._format2digit)
        worksheet.write(self._row + 6, self._col, 'std.dev.:')
        worksheet.write(self._row + 6, self._col+1, stdDevOfErrors, self._format2digit)
        row = self._row + 7
        if calibrationVals is not None:
            for i,key in enumerate(('a','b','c')):
                worksheet.write(row + i, self._col, key)
                worksheet.write(row + i, self._col+1, calibrationVals[i])
        self._col += 3

    def writeAverageMod(self, worksheet, avModifPerCharge, avModif):
        '''
        Writes av. modifications per charge of one spectrum to xlsx file
        :param worksheet: worksheet
        :param (dict[int,float]) avModifPerCharge: {charge: av. modification}
        :param (float) avModifPerCharge: {charge: av. modification}
        '''
        worksheet.write(self._row, self._col, 'av. number of modifications:')
        worksheet.write(self._row + 1, self._col, 'total')
        worksheet.write(self._row + 1, self._col + 1, avModif, self._format2digit)
        worksheet.write_row(self._row + 2, self._col, ['z', 'value'])
        row = self._row + 2
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

    def writeModifications(self, worksheet, modificationsPerZ, modifications):
        '''
        Writes the percentages of each modification for each charge state in one spectrum to xlsx file
        :param (dict[str,ndarray(dtype=[int,float])]) modificationsPerZ:
            {modification: 2D array of [(charge,percentage)]}
        '''
        self.percentFormat = self._workbook.add_format({'num_format': '0.0%'})
        worksheet.write(self._row, self._col, 'modifications:')
        worksheet.write(self._row + 1, self._col, 'av.values')
        worksheet.write_row(self._row + 2, self._col, ['mod', 'total av.', 'z-states av.'])
        avRow = self._row + 3             #for the averaged values
        avRow2 = self._row + 3
        currentCol = self._col + 4
        for mod, val in modifications.items():
            worksheet.write(avRow2, self._col, mod)
            worksheet.write(avRow2,  self._col + 1, val, self.percentFormat)
            avRow2+=1
        for mod,arr in modificationsPerZ.items():
            if mod == "":
                mod = "-"
            worksheet.write(self._row + 1, currentCol, mod)
            row = self._row + 2
            worksheet.write_row(row, currentCol, ['z', 'value'])
            for line in arr:
                row +=1
                worksheet.write(row, currentCol, int(line[0]))
                worksheet.write(row, currentCol + 1, line[1], self.percentFormat)
            worksheet.write(avRow, self._col + 2, '=AVERAGE(' + xl_rowcol_to_cell(self._row + 3, currentCol + 1)
                                   +':' + xl_rowcol_to_cell(row,currentCol+1) +')', self.percentFormat)
            avRow+=1
            currentCol+=3
            if row>self._lastRow:
                self._lastRow = row
        self._col = currentCol + 3


    def writeIntactAnalysis(self, listOfParameters, listsOfIons, avCharges, avErrors, stdDevsOfErrors, listOfCalibrationVals,
                            avModifPerCharges, modificationsInSpectra):
        '''
        Writes the analysis to xlsx file
        :param (list[dict[str,Any]]) parameters: lists of {name: value}
        :param (list[list[list[SimpleIntactIon]]]) listsOfIons: observed ions for each spectrum
        :param (list[list[tuple[float,float]]]) avCharges: average charges in each spectrum
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
                calibrationVals = None
                if listOfCalibrationVals is not None:
                    calibrationVals = listOfCalibrationVals[i][j]
                self.writeGeneralAnalysis(worksheet, avCharges[i][j], avErrors[i][j], stdDevsOfErrors[i][j],
                                          calibrationVals)
                self.writeAverageMod(worksheet, avModifPerCharges[0][i][j], avModifPerCharges[1][i][j])
                self.writeModifications(worksheet, modificationsInSpectra[0][i][j], modificationsInSpectra[1][i][j])
                if self._lastRow -self._row < 9:
                    self._row += 11
                else:
                    self._row = self._lastRow + 2


    def closeWorkbook(self):
        self._workbook.close()


class FullIntactExcelWriter(ExcelWriter, IntactExcelWriter):
    '''
    Responsible for output of full intact ion search to xlsx file
    '''
    def __init__(self, file, configurations, options):
        '''

        :param (str) file: path of xlsx output file
        :param (dict[str:Any]) configurations: configurations
        :param (dict[str:str]) options: export options
        '''
        super(FullIntactExcelWriter, self).__init__(file, configurations, options)
        self._col, self._lastRow = 0, 0
        self._intact = True

    def toExcel(self, analyser, intensityModeller, neutralLibrary, settings, spectrumHandler, infoString):
        '''
        Write results of top-down MS analysis to xlsx file
        :param (Analyser) analyser: analyser
        :param (IntensityModeller) intensityModeller: intensityModeller
        :param (list[Neutral]) neutralLibrary: library of neutral species
        :param (dict[str:Any]) settings: settings
        :param (SpectrumHandler) spectrumHandler: spectrumHandler
        :param (str) infoString: info string
        '''
        self._spraymode = 1
        if settings['sprayMode'] == 'negative':
            self._spraymode = -1
        try:
            self.writeInfos(infoString)
            self._row = self.writeGeneralParameters(0, {"spectral file:": settings['spectralData'], 'max. m/z:': spectrumHandler.getUpperBound()})
            self._row += 1
            self._worksheet1.write(self._row, 0, ("analysis:"))
            self._row += 1
            avCharges, avErrors, stddevs = analyser.calculateAvChargeAndError()
            avModifPerCharges, avModifications = analyser.calculateAverageModification()
            modificationsInSpectraPerZ, modificationsInSpectra = analyser.calculateModifications()
            self.writeGeneralAnalysis(self._worksheet1, avCharges[0][0], avErrors[0][0], stddevs[0][0], None)
            self.writeAverageMod(self._worksheet1, avModifPerCharges[0][0], avModifications[0][0])
            self.writeModifications(self._worksheet1, modificationsInSpectraPerZ[0][0], modificationsInSpectra[0][0])
            precursorRegion = (0,0)
            observedIons = self.sortByName(intensityModeller.getObservedIons().values())
            deletedIons = self.sortByName(intensityModeller.getDeletedIons().values())
            self.writeIons(self._worksheet2, observedIons, precursorRegion)
            self.writePeaks(self._worksheet3, 0, 0, observedIons)
            row = self.writeIons(self._worksheet4, deletedIons, precursorRegion)
            self.writePeaks(self._worksheet4, row + 3, 0, deletedIons)
            self.writeIons(self._worksheet5, self.sortByName(intensityModeller.getRemodelledIons()), precursorRegion)
            self.writeSumFormulas(neutralLibrary, spectrumHandler.getSearchedChargeStates())
        finally:
            self.closeWorkbook()

