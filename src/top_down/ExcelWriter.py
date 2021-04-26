'''
Created on 13 Aug 2020

@author: michael
'''
import xlsxwriter
from numpy import isnan
from datetime import datetime


class BasicExcelWriter(object):
    '''
    Used by OccupancyRecalculator to write xlsx output file
    '''
    def __init__(self, file):
        '''
        :param (str) file: path of the output file
        '''
        self.workbook = xlsxwriter.Workbook(file)
        self.worksheet1 = self.workbook.add_worksheet('analysis')
        self.percentFormat = self.workbook.add_format({'num_format': '0.0%'})


    def writeAbundancesOfSpecies(self, row, relAbundanceOfSpecies):
        '''
        Writes percentages of each fragment type in worksheet1
        :param (int) row: Current row in current sheet
        :param (dict[str,float]) relAbundanceOfSpecies:
        :return: (int) last row
        '''
        self.worksheet1.write(row, 0, "fragmentation:")
        keys = sorted(list(relAbundanceOfSpecies.keys()))
        for species in keys:
            if relAbundanceOfSpecies[species] > 0:
                self.worksheet1.write(row, 1, species)
                self.worksheet1.write(row, 2, relAbundanceOfSpecies[species], self.percentFormat)
                row += 1
        return row + 2


    def writePercentage(self,row,col, val):
        '''
        Writes a percentage in a cell
        :param (int) row: row of cell
        :param (int) col: column of cell
        :param (float) val: percentage value
        '''
        if (val != None) and (not isnan(val)):
            self.worksheet1.write(row, col, val, self.percentFormat)


    def writeOccupancies(self, row, sequence, percentageDict, *args):
        '''#ToDo: DRY
        Writes occupancies in worksheet1
        :param (int) row: row to start writing in sheet
        :param (list[str]) sequence: list of building blocks
        :param (dict[str,ndarray(dtype=float)]) percentageDict: dict {fragment-type : occupancies},
            occupancies are ordered by number of corresponding building blocks
        :param (tuple[list[str],list[str]]) args: list of forward fragment types, list of backward fragment types
        :return: (int) last row
        '''
        self.worksheet1.write(row, 0, "Occupancies: /%")
        row+=1
        self.worksheet1.write(row, 0, "base'")
        self.worksheet1.write_column(row+1,0, sequence)
        self.worksheet1.write(row, 1, "#5'/N-term.")
        self.worksheet1.write_column(row+1,1, list(range(1,len(sequence)+1)))
        col=2
        if args and args[1]:
            forwFrags = args[0]
            backFrags = args[1]
        else:
            forwFrags = ['a', 'b', 'c', 'd']
            backFrags = ['w', 'x', 'y', 'z']
        for key in sorted(list(percentageDict.keys())):
            currentRow = row
            self.worksheet1.write(currentRow, col, key)
            currentRow += 1
            for i in range(len(sequence)):
                if key in backFrags:
                    val = percentageDict[key][len(sequence)-i-2]
                elif key in forwFrags:
                    val = percentageDict[key][i]
                else:
                    raise Exception("Unknown Direction of Fragment:",key)
                if val != None:
                    self.writePercentage(currentRow, col, val)
                currentRow += 1
            col+=1
        self.worksheet1.write(row, col, "#3'/C-term.")
        self.worksheet1.write_column(row+1,col, reversed(list(range(1,len(sequence)))))
        self.addChart(row,percentageDict, sequence,backFrags)
        return row+len(sequence)


    def addChart(self, row,percentageDict,sequence, backwardFrags):
        '''

        :param (int) row: row to place chart
        :param (dict[str,ndarray(dtype=float)]) percentageDict: dict {fragment-type : occupancies},
            occupancies are ordered by number of corresponding building blocks
        :param (list[str]) sequence: list of building blocks
        :param (list[str]) backwardFrags: list of backward fragment types
        :return:
        '''
        chart = self.workbook.add_chart({'type':'line'})
        lastRow = row + len(sequence)
        col = 2
        '''if args and args[0]:
            backwardFrags = args[0]
        else:
            backwardFrags = ['w', 'x', 'y', 'z']'''
        for key in sorted(list(percentageDict.keys())):
            if key in backwardFrags:
                chart.add_series({
                    'name': ['analysis', row, col],
                    'categories': ['analysis', row+1, 1, lastRow, 1],
                    'values': ['analysis', row+1, col, lastRow, col],
                    'y2_axis': 1,
                    'marker': {'type': 'automatic', 'size': 4},
                    'line': {'width': 2.5}
                })
            else:
                chart.add_series({
                    'name': ['analysis', row, col],
                    'categories': ['analysis', row+1, 1, lastRow, 1],
                    'values': ['analysis', row+1, col, lastRow, col],
                    'marker': {'type': 'automatic', 'size': 4},
                    'line': {'width': 2.5},
                })
            col+=1
        chart.set_size({'width': len(sequence) * 20 + 100, 'height': 400})
        chart.set_title({'name': 'Occupancies'})
        chart.set_x_axis({'name': 'cleavage site',
                           'name_font': {'size': 13},
                           'position_axis': 'on_tick',
                           'num_font': {'size': 10}, })
        chart.set_y_axis({'name': '5\'-O /%',
                           'name_font': {'size': 13},
                           'min': 0, 'max': 1,
                           'num_font': {'size': 10},
                           'num_format': '0%',
                          })
        chart.set_y2_axis({'name': '3\'-O /%',
                            'name_font': {'size': 13},
                            'min': 0, 'max': 1,
                            'num_font': {'size': 10},
                            'num_format': '0%',
                            'reverse': True, })
        chart.set_legend({'font': {'size': 12}})
        # Set an Excel chart style. Colors with white outline and shadow.
        chart.set_style(10)
        # Insert the chart into the worksheet (with an offset).
        self.worksheet1.insert_chart(row, len(percentageDict)+4, chart, {'x_offset': 25, 'y_offset': 10})


    def closeWorkbook(self):
        self.workbook.close()




class ExcelWriter(BasicExcelWriter):
    '''
    Class to write results of top-down MS analysis to xlsx file
    '''
    def __init__(self, file, configurations):
        '''
        :param (str) file: path of the output file
        :param (dict[str:Any]) configurations: configurations
        '''
        super().__init__(file)
        self.configs = configurations
        self.worksheet2 = self.workbook.add_worksheet('ions')
        self.worksheet3 = self.workbook.add_worksheet('peaks')
        self.worksheet4 = self.workbook.add_worksheet('deleted ions')
        self.worksheet5 = self.workbook.add_worksheet('ions before remodelling')
        self.worksheet6 = self.workbook.add_worksheet('molecular formulas')
        self.worksheet7 = self.workbook.add_worksheet('info')
        self.format2digit = self.workbook.add_format({'num_format': '0.00'})
        self.format5digit = self.workbook.add_format({'num_format': '0.00000'})

    def toExcel(self, analyser, intensityModeller, properties, fragmentLibrary, settings, spectrumHandler, infoString):
        '''
        Write results of top-down MS analysis to xlsx file
        :param (Analyser) analyser: analyser
        :param (IntensityModeller) intensityModeller: intensityModeller
        :param (PropertyStorage) properties: properties
        :param (list[FragmentIon]) fragmentLibrary: fragmentLibrary
        :param (dict[str:Any]) settings: settings
        :param (SpectrumHandler) spectrumHandler: spectrumHandler
        :param (str) infoString: infoString
        '''
        try:
            #percentages = list()
            self.writeAnalysis({"spectral file:": settings['spectralData'], 'max. m/z:':spectrumHandler.getUpperBound()},
                               analyser.getModificationLoss(),
                               analyser.calculateRelAbundanceOfSpecies(),
                               properties.getSequenceList(),
                               analyser.calculateOccupancies(self.configs['interestingIons'], properties.getUnimportantModifs()),
                               properties.getFragmentsByDir(1), properties.getFragmentsByDir(-1))
            #self.analyser.createPlot(__maxMod)
            observedIons = self.sortByName(intensityModeller.getObservedIons().values())
            deletedIons = self.sortByName(intensityModeller.getDeletedIons().values())
            precursorRegion = intensityModeller.getPrecRegion(settings['sequName'], abs(settings['charge']))
            self.writeIons(self.worksheet2, observedIons,precursorRegion)
            self.writePeaks(self.worksheet3, 0, 0, observedIons)
            row = self.writeIons(self.worksheet4, deletedIons,precursorRegion)
            self.writePeaks(self.worksheet4, row + 3, 0, deletedIons)
            self.writeIons(self.worksheet5, self.sortByName(intensityModeller.getRemodelledIons()), precursorRegion)
            self.writeSumFormulas(fragmentLibrary, spectrumHandler.getSearchedChargeStates())
            self.writeInfos(infoString)
        finally:
            self.closeWorkbook()

    @staticmethod
    def sortByName(ionList):
        # return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
        return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))



    def writeGeneralParameters(self, row, generalParam):
        '''
        Writes time, name of input file and max. m/z to worksheet1
        :param (int) row: row to start writing
        :param (dict[str,Any]) generalParam: input file name, max. m/z in spectrum containing non-noise peaks
            (see SpectrumHandler)
        :return: (int) last row
        '''
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.worksheet1.write_row(row, 0,("Time:",date))
        row=1
        print(generalParam)
        for key,val in generalParam.items():
            self.worksheet1.write_row(row, 0, (key,val))
            row +=1
        return row+2


    def writeAnalysis(self, generalParam, modLoss, relAbundanceOfSpecies,sequence, percentages, forwFrags, backFrags):
        '''
        Writes summary of analysis to worksheet1
        :param (dict[str,Any]) generalParam: input file name, max. m/z in spectrum containing non-noise peaks
            (see SpectrumHandler)
        :param (float) modLoss: proportion of modification loss of precursor
        :param (dict[str,float]) relAbundanceOfSpecies: relative fragment type abundances {type:abundance}
        :param (list[str]) sequence: list of building blocks
        :param (dict[str,ndarray(dtype=float)]) percentages: dict {fragment-type : occupancies},
            occupancies are ordered by number of corresponding building blocks
        :param (list[str]) forwFrags: list of forward fragment types
        :param (list[str]) backFrags: list of backward fragment types
        '''
        row = self.writeGeneralParameters(0, generalParam)
        row+=1
        self.worksheet1.write(row,0,("analysis:"))
        row+=1
        if modLoss != None:
            self.worksheet1.write(row,0,'modification_loss:')
            self.worksheet1.write(row,1,modLoss,self.percentFormat)
            row +=1
        row +=1
        row = self.writeAbundancesOfSpecies(row,relAbundanceOfSpecies)
        if modLoss != None:
            self.writeOccupancies(row, sequence, percentages, forwFrags, backFrags)


    def writeIon(self,worksheet, row,ion):
        '''
        Writes an ion into the corresponding worksheet
        :param (Worksheet) worksheet: corresponding worksheet
        :param (int) row: row where ion should be written
        :param (FragmentIon) ion: corresponding ion
        :return: (int) next row
        '''
        worksheet.write(row, 0, ion.getMonoisotopic(), self.format5digit)
        worksheet.write(row, 1, ion.getCharge())
        worksheet.write(row, 2, round(ion.getIntensity()))
        worksheet.write(row, 3, ion.getName())
        worksheet.write(row, 4, round(ion.getError(),3), self.format2digit)
        worksheet.write(row, 5, round(ion.getSignalToNoise(),3), self.format2digit)
        worksheet.write(row, 6, round(ion.getQuality(),3), self.format2digit)
        worksheet.write(row, 7, ion.getFormula().toString())
        worksheet.write(row, 8, round(ion.getScore(),3), self.format2digit)
        worksheet.write(row, 9, ion.getComment())
        return row+1


    def writeIons(self,worksheet, ionList,precursorArea):
        '''
        Writes a list of ions into the corresponding worksheet
        :param (Worksheet) worksheet: corresponding worksheet
        :param (list[FragmentIon]) ionList: list of ions
        :param (tuple[float,float]) precursorArea:
            lowest m/z, m/z of precursor +70/precCharge (to include cationic adducts)
        :return: (int) next row
        '''
        worksheet.write_row(0,0,('m/z','z','intensity','fragment','error /ppm', 'S/N','quality',
                                                        'formula','score', 'comment'))
        row= 1
        for ion in ionList:
            row = self.writeIon(worksheet,row,ion)
        lengthIonList = str(len(ionList))
        highlighted = self.workbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.conditional_format('A2:A'+lengthIonList, {'type': 'cell',
                                               'criteria': 'between',
                                               'minimum': precursorArea[0],
                                               'maximum': precursorArea[1],
                                               'format': highlighted})
        worksheet.conditional_format('G2:G'+lengthIonList, {'type': 'cell',
                                               'criteria': 'greater than',
                                               'value': self.configs['shapeMarked'],
                                               'format': highlighted})
        worksheet.conditional_format('I2:I'+lengthIonList, {'type': 'cell',
                                               'criteria': 'greater than',
                                               'value': self.configs['scoreMarked'],
                                               'format': highlighted})
        return row+1


    def writePeaks(self, worksheet, row,col, ionList):
        '''
        Writes a list of peaks to the corresponding worksheet
        :param (Worksheet) worksheet: corresponding worksheet
        :param (int) row: row of starting cell
        :param (int) col: column of starting cell
        :param (list[FragmentIon]) ionList: list of ions
        :return: (int) next row
        '''
        worksheet.write_row(row,col,('m/z','z','intensity','fragment','error','used'))
        row += 1
        for ion in ionList:
            if ion.getType() in self.configs['interestingIons']:
                for peak in ion.getIsotopePattern():
                    worksheet.write(row,col,peak['m/z'],self.format5digit)
                    worksheet.write(row,col+1,ion.getCharge())
                    worksheet.write(row,col+2,int(round(peak['calcInt'])))
                    worksheet.write(row,col+3,ion.getName())
                    worksheet.write(row,col+4,peak['error'],self.format2digit)
                    worksheet.write(row,col+5,peak['used'])
                    row+=1
        return row


    def writeSumFormulas(self, listOfFragments, chargeStates):
        '''
        Writes the molecular formulas of all calculated fragments and the possible charge states to worksheet6
        :param (list[Fragment]) listOfFragments: list of fragments
        :param (dict[str,list[int]]) chargeStates: dictionary {fragment name : list of searched charge states}
        '''
        self.worksheet6.write_row(0,0,('name','formula','searched charge st.'))
        row =1
        for fragment in listOfFragments:
            if fragment.getType() in self.configs['interestingIons']:
                self.worksheet6.write(row,0,fragment.getName())
                self.worksheet6.write(row, 1, fragment.getFormula().toString())
                #self.worksheet6.write(row, 2, self.listToString(chargeStates[fragment.getName()]))
                self.worksheet6.write(row, 2, ', '.join([str(z) for z in chargeStates[fragment.getName()]]))
                row+=1

    """@staticmethod
    def listToString(items):
        '''
        Creates a string from a list
        :param (list[Any]) items: 
        :return: 
        '''
        itemString = ""
        for item in items:
            if itemString == "":
                itemString += str(item)
            else:
                itemString += ", " + str(item)
        return itemString"""


    def writeInfos(self, info):
        '''
        Writes information about the search (e.g. all user inputs) to worksheet7
        :param (str) info:  information
        '''
        #self.worksheet7.write(0, 0, "Configurations:")
        for i, line in enumerate(info.split('\n')):
            col = 0
            if line.startswith('\t'):
                col =1
            self.worksheet7.write(i, col, line)