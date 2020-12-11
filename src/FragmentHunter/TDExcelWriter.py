'''
Created on 13 Aug 2020

@author: michael
'''
import xlsxwriter
import numpy as np
from datetime import datetime


class BasicExcelWriter(object):
    '''
    classdocs
    '''
    def __init__(self, file):
        self.workbook = xlsxwriter.Workbook(file)
        self.worksheet1 = self.workbook.add_worksheet('analysis')
        self.percentFormat = self.workbook.add_format({'num_format': '0.0%'})


    def writeAbundancesOfSpecies(self, row, relAbundanceOfSpecies):
        self.worksheet1.write(row, 0, "fragmentation:")
        keys = sorted(list(relAbundanceOfSpecies.keys()))
        for species in keys:
            if relAbundanceOfSpecies[species] > 0:
                self.worksheet1.write(row, 1, species)
                self.worksheet1.write(row, 2, relAbundanceOfSpecies[species], self.percentFormat)
                row += 1
        return row + 2


    def writePercentage(self,row,col, val):
        if (val != None) and (not np.isnan(val)):
            self.worksheet1.write(row, col, val, self.percentFormat)


    def writeOccupancies(self, row, sequence, percentageDict):
        self.worksheet1.write(row, 0, "Occupancies: /%")
        row+=1
        self.worksheet1.write(row, 0, "base'")
        self.worksheet1.write_column(row+1,0, sequence)
        self.worksheet1.write(row, 1, "#5'")
        self.worksheet1.write_column(row+1,1, list(range(1,len(sequence)+1)))
        col=2
        for key in sorted(list(percentageDict.keys())):
            currentRow = row
            self.worksheet1.write(currentRow, col, key)
            currentRow += 1
            for i in range(len(sequence)):
                if key[0] in ['w', 'x', 'y', 'z']:
                    val = percentageDict[key][len(sequence)-i-2]
                else:
                    val = percentageDict[key][i]
                if val != None:
                    self.writePercentage(currentRow, col, val)
                currentRow += 1
            col+=1
        self.worksheet1.write(row, col, "#3'")
        self.worksheet1.write_column(row+1,col, reversed(list(range(1,len(sequence)))))
        self.addChart(row,percentageDict, sequence)
        return row+len(sequence)


    def addChart(self, row,percentageDict,sequence):
        chart = self.workbook.add_chart({'type':'line'})
        lastRow = row + len(sequence)
        col = 2
        for key in sorted(list(percentageDict.keys())):
            if key[0] in ['w', 'x', 'y', 'z']:
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
        chart.set_x_axis({'name': 'Sequence',
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
    classdocs
    '''
    def __init__(self, file, configurations):
        super().__init__(file)
        self.configs = configurations
        self.worksheet2 = self.workbook.add_worksheet('ions')
        self.worksheet3 = self.workbook.add_worksheet('peaks')
        self.worksheet4 = self.workbook.add_worksheet('deleted ions')
        self.worksheet5 = self.workbook.add_worksheet('ions before remodelling')
        self.worksheet6 = self.workbook.add_worksheet('molecular formulas')
        self.format2digit = self.workbook.add_format({'num_format': '0.00'})
        self.format5digit = self.workbook.add_format({'num_format': '0.00000'})


    def writeGeneralParameters(self, row, generalParam):
        for line in generalParam:
            self.worksheet1.write(row,0, line[0])
            self.worksheet1.write(row,1, line[1])
            row +=1
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.worksheet1.write(1,1,date)
        return row+2


    def writeAnalysis(self, generalParam, modLoss, relAbundanceOfSpecies,sequence, percentages):
        row = self.writeGeneralParameters(0, generalParam)
        row+=1
        self.worksheet1.write(row,0,("analysis:"))
        row+=1
        if modLoss != None:
            self.worksheet1.write(row,0,'modification_loss:')
            self.worksheet1.write(row,1,modLoss,self.percentFormat)
            row +=1
        row = self.writeAbundancesOfSpecies(row,relAbundanceOfSpecies)
        if modLoss != None:
            self.writeOccupancies(row, sequence, percentages)


    def writeIon(self,worksheet, row,ion):
        worksheet.write(row, 0, ion.getMonoisotopic(), self.format5digit)
        worksheet.write(row, 1, ion.charge)
        worksheet.write(row, 2, round(ion.intensity))
        worksheet.write(row, 3, ion.getName())
        worksheet.write(row, 4, round(ion.error,3), self.format2digit)
        worksheet.write(row, 5, round(ion.getSignalToNoise(),3), self.format2digit)
        worksheet.write(row, 6, round(ion.quality,3), self.format2digit)
        worksheet.write(row, 7, ion.formula.toString())
        worksheet.write(row, 8, round(ion.score,3), self.format2digit)
        worksheet.write(row, 9, ion.comment)
        return row+1


    def writeIons(self,worksheet, ionList,precursorArea):
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
        worksheet.write_row(row,col,('m/z','z','intensity','fragment','error','used'))
        row += 1
        for ion in ionList:
            if ion.type in self.configs['interestingIons']:
                for peak in ion.isotopePattern:
                    worksheet.write(row,col,peak['m/z'],self.format5digit)
                    worksheet.write(row,col+1,ion.charge)
                    worksheet.write(row,col+2,int(round(peak['calcInt'])))
                    worksheet.write(row,col+3,ion.getName())
                    worksheet.write(row,col+4,peak['error'],self.format2digit)
                    worksheet.write(row,col+5,peak['used'])
                    row+=1
        return row


    def writeSumFormulas(self, listOfFragments, chargeStates):
        self.worksheet6.write_row(0,0,('name','formula','searched charge st.'))
        row =1
        for fragment in listOfFragments:
            if fragment.type in self.configs['interestingIons']:
                self.worksheet6.write(row,0,fragment.getName())
                self.worksheet6.write(row, 1, fragment.formula.toString())
                self.worksheet6.write(row, 2, self.listToString(chargeStates[fragment.getName()]))
                row+=1

    @staticmethod
    def listToString(items):
        itemString = ""
        for item in items:
            if itemString == "":
                itemString += str(item)
            else:
                itemString += ", " + str(item)
        return itemString