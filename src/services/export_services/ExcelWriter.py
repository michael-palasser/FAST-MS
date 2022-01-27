'''
Created on 13 Aug 2020

@author: michael
'''
import xlsxwriter
from numpy import isnan, sign
from datetime import datetime
from string import ascii_uppercase


class BasicExcelWriter(object):
    '''
    Used by OccupancyRecalculator to write xlsx output file
    '''
    def __init__(self, file, modification):
        '''
        :param (str) file: path of the output file
        '''
        self._workbook = xlsxwriter.Workbook(file)
        self._worksheet1 = self._workbook.add_worksheet('analysis')
        self._percentFormat = self._workbook.add_format({'num_format': '0.0%'})
        self._format2digit = self._workbook.add_format({'num_format': '0.00'})
        self._modification = modification
        self._intact = False

    def writeDate(self):
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        self._worksheet1.write(0, 0, date)

    def writeAbundancesOfSpecies(self, row, relAbundanceOfSpecies):
        '''
        Writes percentages of each fragment type in _worksheet1
        :param (int) row: Current row in current sheet
        :param (dict[str,float]) relAbundanceOfSpecies:
        :return: (int) last row
        '''
        self._worksheet1.write(row, 0, "fragmentation:")
        keys = sorted(list(relAbundanceOfSpecies.keys()))
        for species in keys:
            if relAbundanceOfSpecies[species] > 0:
                self._worksheet1.write(row, 1, species)
                self._worksheet1.write(row, 2, relAbundanceOfSpecies[species], self._percentFormat)
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
            self._worksheet1.write(row, col, val, self._percentFormat)

    def writeVal(self,row,col, val):
        '''
        Writes a value in a cell
        :param (int) row: row of cell
        :param (int) col: column of cell
        :param (float) val: percentage value
        '''
        if (val != None) and (not isnan(val)):
            self._worksheet1.write(row, col, val, self._format2digit)


    '''def addOccupancies(self, row, sequence, valueDict, *args):
        return self.addOccupOrCharges('Occupancies: /%', 'Occupancies', row, sequence, valueDict,args)'''

    def addOccupOrCharges(self, mode, row, sequence, valueDict, maxVal, *args):
        '''#ToDo: DRY
        Writes occupancies in _worksheet1
        :param (int) mode: 0 for occupancies, 1 for charges, 2 for charges (reduced)
        :param (int) row: row to start writing in sheet
        :param (list[str]) sequence: list of building blocks
        :param (dict[str,ndarray(dtype=float)]) valueDict: dict {fragment-type : values},
            values (e.g. occupancies) are ordered by number of corresponding building blocks
        :param (int) maxVal: maximum value of y-axis (plot)
        :param (list[str]) args: list of forward fragment types, list of backward fragment types
        :return: (int) last row
        '''
        write = self.writeVal
        if mode == 0:
            title = 'Occupancies: '+ self._modification +' /%'
            plotTitle = 'Occupancies: '+ self._modification
            write = self.writePercentage
        elif mode == 1:
            title = 'Av. Charge per Fragment (intensities):'
            plotTitle = 'Av. Charge (int.)'
        else:
            title = 'Av. Charge per Fragment (abundances):'
            plotTitle = 'Av. Charge (ab.)'
        self._worksheet1.write(row, 0, title)
        row+=1
        self._worksheet1.write(row, 0, "building block")
        self._worksheet1.write_column(row + 1, 0, sequence)
        self._worksheet1.write(row, 1, "#5'/N-term.")
        self._worksheet1.write_column(row + 1, 1, list(range(1, len(sequence) + 1)))
        col=2
        if args and args[1]:
            forwFrags = args[0]
            backFrags = args[1]
        else:
            forwFrags = ['a', 'b', 'c', 'd']  #ToDo
            backFrags = ['w', 'x', 'y', 'z']
        for key in sorted(list(valueDict.keys())):
            currentRow = row
            self._worksheet1.write(currentRow, col, key)
            currentRow += 1
            for i in range(len(sequence)):
                if key in backFrags:
                    val = valueDict[key][len(sequence) - i - 2]
                elif key in forwFrags:
                    val = valueDict[key][i]
                else:
                    raise Exception("Unknown Direction of Fragment:",key)
                if val != None:
                    write(currentRow, col, val)
                currentRow += 1
            col+=1
        self._worksheet1.write(row, col, "#3'/C-term.")
        self._worksheet1.write_column(row + 1, col, reversed(list(range(1, len(sequence)))))
        self.addChart(plotTitle, row, valueDict, sequence, backFrags, maxVal, mode == 0)
        return row+len(sequence)


    def addChart(self, title, row, valueDict, sequence, backwardFrags, maxVal, occupancy=True):
        '''
        Makes a plot in the xlsx file (occupancy or charge plot)
        :param (str) title: title of the chart
        :param (int) row: row to place chart
        :param (dict[str,ndarray(dtype=float)]) valueDict: dict {fragment-type : values},
            values (e.g. occupancies) are ordered by number of corresponding building blocks
        :param (list[str]) sequence: list of building blocks
        :param (list[str]) backwardFrags: list of backward fragment types
        :param (str) format: format of the labels
        :param (int) maxVal: maximum value of y-axis
        :return:
        '''
        if occupancy:
            format = '0%'
            yAxis1 = "O (5'/N-term.) /%"
            yAxis2 = "O (3'/C-term.) /%"
        else:
            format = '0.0'
            yAxis1 = "av. charge (5'-/N-term.)"
            yAxis2 = "av. charge (3'-/C-term.)"
        chart = self._workbook.add_chart({'type': 'line'})
        sequLength= len(sequence)
        lastRow = row + sequLength
        col = 2
        '''if args and args[0]:
            backwardFrags = args[0]
        else:
            backwardFrags = ['w', 'x', 'y', 'z']'''
        for key in sorted(list(valueDict.keys())):
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
        chart.set_size({'width': sequLength * 20 + 100, 'height': 400})
        chart.set_title({'name': title})
        chart.set_x_axis({'name': 'cleavage site',
                           'name_font': {'size': 13},
                          'min':0, 'max':sequLength-1,
                           'position_axis': 'between',
                           'num_font': {'size': 10},})
        chart.set_y_axis({'name': yAxis1,
                           'name_font': {'size': 13},
                           'min': 0, 'max': maxVal,
                           'num_font': {'size': 10},
                           'num_format': format,
                          })
        chart.set_y2_axis({'name': yAxis2,
                            'name_font': {'size': 13},
                           'min': 0, 'max': maxVal,
                            'num_font': {'size': 10},
                            'num_format': format,
                            'reverse': True, })
        chart.set_legend({'font': {'size': 12}})
        # Set an Excel chart style. Colors with white outline and shadow.
        chart.set_style(10)
        # Insert the chart into the worksheet (with an offset).
        self._worksheet1.insert_chart(row, len(valueDict) + 4, chart, {'x_offset': 25, 'y_offset': 10})


    def closeWorkbook(self):
        self._workbook.close()




class ExcelWriter(BasicExcelWriter):
    '''
    Class to write results of top-down MS analysis to xlsx file
    '''
    def __init__(self, file, configurations, options):
        '''
        :param (str) file: path of the output file
        :param (dict[str:Any]) configurations: configurations
        :param (dict[str:str]) options: export options
        '''
        super().__init__(file, '')
        self._configs = configurations
        self._options = options
        self._worksheet2 = self._workbook.add_worksheet('ions')
        self._worksheet3 = self._workbook.add_worksheet('peaks')
        self._worksheet4 = self._workbook.add_worksheet('deleted ions')
        self._worksheet5 = self._workbook.add_worksheet('ions before remodelling')
        self._worksheet6 = self._workbook.add_worksheet('molecular formulas')
        self._worksheet7 = self._workbook.add_worksheet('protocol')
        self._format5digit = self._workbook.add_format({'num_format': '0.00000'})


    def toExcel(self, analyser, intensityModeller, properties, fragmentLibrary, settings, spectrumHandler, infoString):
        '''
        Write results of top-down MS analysis to xlsx file
        :param (Analyser) analyser: analyser
        :param (IntensityModeller) intensityModeller: intensityModeller
        :param (SearchSettings) properties: properties
        :param (list[FragmentIon]) fragmentLibrary: fragmentLibrary
        :param (dict[str:Any]) settings: settings
        :param (SpectrumHandler) spectrumHandler: spectrumHandler
        :param (str) infoString: infoString
        '''
        self._spraymode = sign(settings['charge'])
        self._modification = properties.getModifPattern().getModification()
        try:
            #percentages = list()
            self.writeInfos(infoString)
            self.writeAnalysis({"spectral file:": settings['spectralData'], 'max. m/z:':spectrumHandler.getUpperBound()},
                               analyser, properties, settings['nrMod'], abs(settings['charge']))
            #self.analyser.createPlot(__maxMod)
            observedIons = self.sortByName(intensityModeller.getObservedIons().values())
            deletedIons = self.sortByName(intensityModeller.getDeletedIons().values())
            precursorRegion = intensityModeller.getPrecRegion(settings['sequName'], abs(settings['charge']))
            self.writeIons(self._worksheet2, observedIons, precursorRegion)
            self.writePeaks(self._worksheet3, 0, 0, observedIons)
            row = self.writeIons(self._worksheet4, deletedIons, precursorRegion)
            self.writePeaks(self._worksheet4, row + 3, 0, deletedIons)
            self.writeIons(self._worksheet5, self.sortByName(intensityModeller.getRemodelledIons()), precursorRegion)
            self.writeSumFormulas(fragmentLibrary, spectrumHandler.getSearchedChargeStates())
        finally:
            self.closeWorkbook()

    @staticmethod
    def sortByName(ionList):
        # return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
        return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))



    def writeGeneralParameters(self, row, generalParam):
        '''
        Writes time, name of input file and max. m/z to _worksheet1
        :param (int) row: row to start writing
        :param (dict[str,Any]) generalParam: input file name, max. m/z in spectrum containing non-noise peaks
            (see SpectrumHandler)
        :return: (int) last row
        '''
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        self._worksheet1.write_row(row, 0, ("Time:", date))
        row=1
        for key,val in generalParam.items():
            self._worksheet1.write_row(row, 0, (key, val))
            row +=1
        return row+2


    def writeAnalysis(self, generalParam, analyser, properties, nrMod, maxCharge):
        '''
        Writes summary of analysis to worksheet1
        :param (dict[str,Any]) generalParam: input file name, max. m/z in spectrum containing non-noise peaks
            (see SpectrumHandler)
        :param (Analyser) analyser: analyser
        :param (SearchSettings) properties: properties
        :param (int) nrMod: max. nr. of modifications
        :param (int) maxCharge: abs. value of precursor charge
        '''
        row = self.writeGeneralParameters(0, generalParam)
        row+=1
        self._worksheet1.write(row, 0, ("analysis:"))
        row+=1
        modLoss = analyser.getModificationLoss()
        if modLoss != None:
            self._worksheet1.write(row, 0, 'modification loss:')
            self._worksheet1.write(row, 1, modLoss, self._percentFormat)
            row +=1
        row +=1
        row = self.writeAbundancesOfSpecies(row, analyser.calculateRelAbundanceOfSpecies()[0])
        sequence = properties.getSequenceList()
        forwFrags, backFrags = properties.getFragmentsByDir(1), properties.getFragmentsByDir(-1)
        if (modLoss != None) and ('occupancies' in self._options['analysis']):
            occupPercentages = analyser.calculateOccupancies(self._configs['interestingIons'],
                                          unImportantMods=properties.getUnimportantModifs())[0]
            row = self.addOccupOrCharges(0, row, sequence, occupPercentages, nrMod, forwFrags, backFrags) +8
            #self.writeOccupancies(row, sequence, percentages, forwFrags, backFrags)
        if 'charge states (int.)' in self._options['analysis']:
            charges = analyser.analyseCharges(self._configs['interestingIons'], False)[0]
            row = self.addOccupOrCharges(1, row, sequence, charges, maxCharge, forwFrags, backFrags) +8
        if ('charge states (int./z)' in self._options['analysis']):
            reducedCharges = analyser.analyseCharges(self._configs['interestingIons'], True)[0]
            self.addOccupOrCharges(2, row, sequence, reducedCharges, maxCharge, forwFrags, backFrags)




    def getAttribute(self,ion):
        '''
        Returns a dict of ion attributes
        :param (FragmentIon) ion:
        :return: (dict[str, tuple[Any,Any]]) dict of attribute name (key) and tuples of attribute and format
         '''
        return {'m/z':(ion.getMonoisotopic(),self._format5digit), 'z':(ion.getCharge(),None),
                'intensity':(round(ion.getIntensity()),None), 'int./z':(round(ion.getIntensity()/ion.getCharge()),None),
                'name':(ion.getName(),None),
                'error /ppm':(round(ion.getError(),3), self._format2digit),
                'S/N':(round(ion.getSignalToNoise(),3), self._format2digit),
                'quality':(round(ion.getQuality(),3), self._format2digit),
                'formula':(ion.getFormula().toString(),None),
                'score':(round(ion.getScore(),3), self._format2digit),
                'comment': (ion.getComment(),None),
                'molecular mass':(ion.getMolecularMass(self._spraymode), self._format5digit),
                'average mass':(ion.getAverageMass(self._spraymode), self._format5digit),
                'noise':(int(ion.getNoise()),None)}

    def writeIon(self,worksheet, row,ion):
        '''
        Writes an ion into the corresponding worksheet
        :param (Worksheet) worksheet: corresponding worksheet
        :param (int) row: row where ion should be written
        :param (FragmentIon) ion: corresponding ion
        :return: (int) next row
        '''
        for i,header in enumerate(self._options['columns']):
            tup = self.getAttribute(ion)[header]
            try:
                if tup[1] is None:
                    worksheet.write(row, i, tup[0])
                else:
                    worksheet.write(row, i, tup[0], tup[1])
            except TypeError: #nan values (if intensity = 0)
                continue
        '''worksheet.write(row, 0, ion.getMonoisotopic(), self._format5digit)
        worksheet.write(row, 1, ion.getCharge())
        worksheet.write(row, 2, round(ion.getIntensity()))
        worksheet.write(row, 3, ion.getName())
        worksheet.write(row, 4, round(ion.getError(),3), self._format2digit)
        worksheet.write(row, 5, round(ion.getSignalToNoise(),3), self._format2digit)
        worksheet.write(row, 6, round(ion.getQuality(),3), self._format2digit)
        worksheet.write(row, 7, ion.getFormula().toString())
        worksheet.write(row, 8, round(ion.getScore(),3), self._format2digit)
        worksheet.write(row, 9, ion.getComment())'''
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
        worksheet.write_row(0, 0, self._options['columns'])
        '''worksheet.write_row(0,0,('m/z','z','intensity','fragment','error /ppm', 'S/N','quality',
                                                        'formula','score', 'comment'))'''
        row= 1
        for ion in ionList:
            row = self.writeIon(worksheet,row,ion)
        lengthIonList = str(len(ionList))
        highlighted = self._workbook.add_format({'bold': True, 'font_color': 'red'})
        conditons = {'m/z' : {'type': 'cell', 'criteria': 'between',  'minimum': precursorArea[0],
                            'maximum': precursorArea[1], 'format': highlighted},
                     'quality': {'type': 'cell', 'criteria': 'greater than', 'value': self._configs['shapeMarked'],
                                 'format': highlighted},
                     'score':{'type': 'cell', 'criteria': 'greater than', 'value': self._configs['scoreMarked'],
                              'format': highlighted}}
        for char, header in zip(ascii_uppercase,self._options['columns']):
            if header in conditons.keys():
                column = char+str(2)+":"+char+lengthIonList
                worksheet.conditional_format(column, conditons[header])
        '''worksheet.conditional_format('A2:A'+lengthIonList, {'type': 'cell',
                                               'criteria': 'between',
                                               'minimum': precursorArea[0],
                                               'maximum': precursorArea[1],
                                               'format': highlighted})
        worksheet.conditional_format('G2:G'+lengthIonList, {'type': 'cell',
                                               'criteria': 'greater than',
                                               'value': self._configs['shapeMarked'],
                                               'format': highlighted})
        worksheet.conditional_format('I2:I'+lengthIonList, {'type': 'cell',
                                               'criteria': 'greater than',
                                               'value': self._configs['scoreMarked'],
                                               'format': highlighted})'''
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
        worksheet.write_row(row,col,('m/z','z','intensity','name','error','used'))
        row += 1
        for ion in ionList:
            if self._intact or ion.getType() in self._configs['interestingIons']:
                for peak in ion.getIsotopePattern():
                    worksheet.write(row, col, peak['m/z'], self._format5digit)
                    worksheet.write(row,col+1,ion.getCharge())
                    worksheet.write(row,col+2,int(round(peak['calcInt'])))
                    worksheet.write(row,col+3,ion.getName())
                    worksheet.write(row, col + 4, peak['error'], self._format2digit)
                    worksheet.write(row,col+5,peak['used'])
                    row+=1
        return row


    def writeSumFormulas(self, listOfFragments, chargeStates):
        '''
        Writes the molecular formulas of all calculated fragments and the possible charge states to _worksheet6
        :param (list[Fragment]) listOfFragments: list of fragments
        :param (dict[str,list[int]]) chargeStates: dictionary {fragment name : list of searched charge states}
        '''
        self._worksheet6.write_row(0, 0, ('name', 'formula', 'searched charge st.'))
        row =1
        for fragment in listOfFragments:
            if self._intact or fragment.getType() in self._configs['interestingIons']:
                self._worksheet6.write(row, 0, fragment.getName())
                self._worksheet6.write(row, 1, fragment.getFormula().toString())
                #self._worksheet6.write(row, 2, self.listToString(chargeStates[fragment.getName()]))
                self._worksheet6.write(row, 2, ', '.join([str(z) for z in chargeStates[fragment.getName()]]))
                row+=1


    def writeInfos(self, info):
        '''
        Writes information about the search (e.g. all user inputs) to _worksheet7
        :param (str) info:  information
        '''
        #self._worksheet7.write(0, 0, "Configurations:")
        for i, line in enumerate(info.split('\n')):
            col = 0
            if line.startswith('\t'):
                col =1
            self._worksheet7.write(i, col, line)