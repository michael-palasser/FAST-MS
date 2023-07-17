from datetime import datetime
import numpy as np
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from src.BACHEM_extension.services.MD_analyser import ionDType,forwardTypes,backwardTypes


class EvaluationWriter(object):
    """
    Class that writes MS/MS MD analysis of SNAP and SumPeak lists to Excel file. Rather depricated functionality
    """
    def __init__(self,sequLength, precursorMass):
        self._formats = {'ppm_threshold:': float, 'Length:': int, 'Precursor:': float}
        self._sequLength = sequLength
        self._precursorMass = precursorMass

    def makeOutput(self, filepath, settings, ionArray, overlaps, forwardAnalysis, backwardAnalysis, best, sequName):
        self._workbook = xlsxwriter.Workbook(filepath)
        self.writeParameters(settings)
        worksheet2 = self._workbook.add_worksheet("ions")
        
        headers = [header for header in ionDType.names if header != 'type']
        worksheet2.write_row(0, 0, headers)
        row = 1
        sortedIons = self.sortIons(ionArray)
        for i, ion in enumerate(sortedIons):
            #worksheet.write_row(headerRow + i + 1, 0, self._formatVals(ion, (-5, -4)))
            worksheet2.write_row(row + i, 0, self.formatVals(ion, ("type")))
        newHeaders = headers[:-4] + headers[-3:]
        worksheet2.write_row(0, len(headers) + 2, ['overlaps:'] + overlaps)
        currentRow, mzColumns = self.writeAnalysis(2, ["5'-3'"] + newHeaders,worksheet2, forwardAnalysis,
                                                   self._sequLength)
        self.writeAnalysis(currentRow + 2, ["3'-5'"] + newHeaders, worksheet2, (backwardAnalysis[0][::-1],
                                                                  backwardAnalysis[1][::-1]), self._sequLength, True)
        highlighted = self._workbook.add_format({'bold': True, 'font_color': 'red'})
        condition = {'type': 'cell', 'criteria': 'between', 'minimum': self._precursorMass - 5,
                     'maximum': self._precursorMass + 5, 'format': highlighted}
        for col in [0] + mzColumns:
            worksheet2.conditional_format(row, col, row + len(ionArray), col + 1, condition)
        
        worksheet3 = self._workbook.add_worksheet("best")
        worksheet3.write_row(0, 0, ["cleavage site"] + newHeaders)                                                                 
        self.writeIonTable(1, 0, worksheet3, best, self._sequLength)
        col = len(newHeaders)+3
        #evaluationDict = {key:val for key,val in zip(("Minimum", "1. Quartile", "Median"),evaluation)}

        worksheet3.write_row(0,col,("Evaluation:", sequName))
        curRow = 1
        snapSNs = "H2:H"+str(self._sequLength)
        peakSNs = "K2:K"+str(self._sequLength)
        if_statement = 'IF('+snapSNs+'>'+peakSNs+","+snapSNs+","+peakSNs+')'
        for i, name in enumerate(("Minimum", "1. Quartile", "Median")):
            worksheet3.write(curRow, col, name)
            worksheet3.write_formula('P'+str(i+2), '=QUARTILE('+if_statement+','+str(i)+')')
            curRow += 1
        self.plot(worksheet3)

        self._workbook.close()

    def writeParameters(self, settings):
        worksheet1 = self._workbook.add_worksheet("parameters")
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        worksheet1.write(0, 0, date)
        row = 1
        for key, val in settings.items():
            if type(val) is list:
                val = '['+",".join(val)+']'
            worksheet1.write_row(row, 0, [key, val])
            row += 1


    @staticmethod
    def sortIons(ions):
        forwardIons = ions[np.where(np.isin(ions['type'], forwardTypes))]
        forwardIons = np.sort(forwardIons, order='number')
        backwardIons = ions[np.where(np.isin(ions['type'], backwardTypes))]
        backwardIons = np.sort(backwardIons, order='number')[::-1]
        sortedIons = np.append(forwardIons,
                               ions[np.where(
                                   np.isin(ions['type'], backwardTypes + forwardTypes, invert=True))])
        return np.append(sortedIons, backwardIons)


    def writeAnalysis(self, row, headers, worksheet, analysis, length, reverse=False):
        col = len(headers) + 2
        mzColumns = [col + 1]
        worksheet.write(row, col, 'best SNAP:')
        currentRow = row + 1
        # headers2 = ["5'-3'"] + headers[:-2
        worksheet.write_row(currentRow, col, headers)
        self.writeIonTable(currentRow+1, col, worksheet, analysis[0], length, reverse)
        """for i, line in enumerate(analysis[0]):
            number = i + 1
            if reverse:
                number = length - number
            worksheet.write_row(currentRow + i + 1, col, [number] + line)"""
        col += len(headers) + 1
        mzColumns.append(col + 1)
        worksheet.write(row, col, 'best Sum Peak:')
        worksheet.write_row(currentRow, col, headers)
        self.writeIonTable(currentRow+1, col, worksheet, analysis[1], length, reverse)
        """for i, line in enumerate(analysis[1]):
            number = i + 1
            if reverse:
                number = length - number
            worksheet.write_row(currentRow + i + 1, col, [number] + line)"""
        return currentRow + 1 + len(analysis[0]), mzColumns
    
    
    def writeIonTable(self, row, col, worksheet, analysis, length, reverse=False):
        for i, line in enumerate(analysis):
            number = i + 1
            if reverse:
                number = length - number
            worksheet.write_row(row + i, col, [number] + self.formatVals(line, ("type","number")))


    @staticmethod
    def formatVals(vals, uninteresting):
        #print("vals",vals,[name for name in ionDType.names if name not in uninteresting])
        #print("vals neu",[vals[name] for name in ionDType.names if name not in uninteresting])
        if vals["m/z"] > 0:
            newVals = [vals[name] for name in ionDType.names if name not in uninteresting]
            if vals['mono_m/z']>0:
                return newVals
            else:
                for i in range(3):
                    newVals[-i-1] = ""
                return newVals
        else:
            return ['' for i in range(len(ionDType.names) - len(uninteresting))]


    def plot(self, worksheet):
        chart = self._workbook.add_chart({'type': 'column'})
        chart.add_series({'name':'best!$P$1',        
                          'categories': 'best!$O$2:$O$4',
                          'values': 'best!$P$2:$P$4',
                          'line': {'none': True},
                          'points': [
                            {'fill': {'color': '#66CC00'}},
                            {'fill': {'color': '#FF6400'}},
                            {'fill': {'color': '#00CCFF'}},
                            ]})
        chart.set_x_axis({'label_position': 'none'})
        chart.set_y_axis({'name':"S/N"})
        chart.set_style(11)
        worksheet.insert_chart('O6', chart)
