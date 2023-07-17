from datetime import datetime
import xlsxwriter
from src.BACHEM_extension.services.EvaluationWriter import EvaluationWriter


class MDEvaluationWriter(object):
    """
    Class that writes a MS/MS MD analysis to Excel file.
    """
    def __init__(self, precursorMass):
        self._precursorMass = precursorMass
        self._digit2Columns = (5,6,7,12)

    def makeOutput(self, filepath, settings, headers, ionLibrary, best, formulaLib, sequence, snapIons, peaks, trail):
        self._workbook = xlsxwriter.Workbook(filepath)
        header_format = self._workbook.add_format()
        header_format.set_bg_color('#DCE6F1')
        #self._format2digit = self._workbook.add_format({'num_format': '0.00'})
        self.writeParameters(settings,sequence)

        highlighted = self._workbook.add_format({'bold': True, 'font_color': 'red'})
        condition = {'type': 'cell', 'criteria': 'between', 'minimum': self._precursorMass - 5,
                     'maximum': self._precursorMass + 5, 'format': highlighted}

        worksheet2 = self._workbook.add_worksheet("ions")
        worksheet2.write_row(0, 0, headers,header_format)
        row = 1
        for cleavageSite in ionLibrary:
            for ion in cleavageSite:
                worksheet2.write_row(row, 0, list(ion)+[self.getFormula(formulaLib, ion)])
                row+=1
        worksheet2.conditional_format(1, 1, row, 2, condition)
        worksheet2.freeze_panes(1, 0)

        worksheet3 = self._workbook.add_worksheet("best")
        worksheet3.write_row(0, 0, headers,header_format)                  
        for i,ion in enumerate(best):
            worksheet3.write_row(i+1, 0, list(ion)+[self.getFormula(formulaLib, ion)])
        worksheet3.conditional_format(1, 1, 1+len(best), 2, condition)
        col = len(headers)+2

        worksheet3.write_row(0,col,("Evaluation:", settings["sequName"]))
        curRow = 1
        snapSNs = "K2:K"+str(len(best)+1)
        peakSNs = "N2:N"+str(len(best)+1)
        if_statement = 'IF('+snapSNs+'>'+peakSNs+","+snapSNs+","+peakSNs+')'
        for i, name in enumerate(("Minimum", "1. Quartile", "Median")):
            worksheet3.write(curRow, col, name)
            worksheet3.write_formula(curRow,col+1, '=QUARTILE('+if_statement+','+str(i)+')')
            curRow += 1
        self.plot(worksheet3)
        
        sortedSnapIons =EvaluationWriter.sortIons(snapIons)
        worksheet4 = self._workbook.add_worksheet("SNAP & Peaks")
        headers = [header for header in sortedSnapIons.dtype.names if header != 'type']
        worksheet4.write_row(0, 0, headers,header_format)
        for i,snapVal in enumerate(sortedSnapIons):
            worksheet4.write_row(i+1, 0, EvaluationWriter.formatVals(snapVal, ('type')))
        
        col = len(headers)+2
        worksheet4.write_row(0, col, [header for header in peaks.dtype.names],header_format)
        for i,peak in enumerate(peaks):
            worksheet4.write_row(i+1, col, peak)
        worksheet4.freeze_panes(1, 0)
        self.writeInfos(trail)
        self._workbook.close()

    def getFormula(self, formulaLib, ion):
        if ion[4]=="":
            return ""
        else:
            return formulaLib[ion[4]]


    def writeParameters(self, settings, sequence):
        worksheet1 = self._workbook.add_worksheet("parameters")
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        worksheet1.write(0, 0, date)
        row = 1
        worksheet1.write(1,3,"".join(sequence))
        for key, val in settings.items():
            if type(val) is list:
                val = '['+",".join(val)+']'
            worksheet1.write_row(row, 0, [key, val])
            row += 1


    def plot(self, worksheet):
        chart = self._workbook.add_chart({'type': 'column'})
        chart.add_series({'name':'best!$T$1',        
                          'categories': 'best!$S$2:$S$4',
                          'values': 'best!$T$2:$T$4',
                          'line': {'none': True},
                          'points': [
                            {'fill': {'color': '#66CC00'}},
                            {'fill': {'color': '#FF6400'}},
                            {'fill': {'color': '#00CCFF'}},
                            ]})
        chart.set_x_axis({'label_position': 'none'})
        chart.set_y_axis({'name':"S/N"})
        chart.set_style(11)
        worksheet.insert_chart('S6', chart)

    def writeInfos(self, info):
        '''
        Writes information about the search (e.g. all user inputs) to _worksheet7
        :param (str) info:  information
        '''
        #self._worksheet7.write(0, 0, "Configurations:")
        protocolSheet = self._workbook.add_worksheet('audit trail')
        for i, line in enumerate(info.split('\n')):
            col = 0
            if line.startswith('\t'):
                col =1
            protocolSheet.write(i, col, line)