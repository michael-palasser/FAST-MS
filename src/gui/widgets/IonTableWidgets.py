from math import log10

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTableWidget

from src.Exceptions import InvalidInputException
from src.gui.GUI_functions import connectTable, showOptions


class IonTableWidget(QTableWidget):
    '''
    Interactive ion table table for checking monoisotopic overlaps and to show ion values when "show peaks" is pressed
    (right click on ion table in top-down search).
    Parent class of IsoPatternIon and TickIonTableWidget
    '''
    def __init__(self, parent, ions, yPos):
        super(IonTableWidget, self).__init__(parent)
        #self._headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self._ions = ions
        self.setColumnCount(len(self.getHeaders()))
        self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setRowCount(len(ions))
        self._smallFnt = QFont()
        self._smallFnt.setPointSize(10)
        self._ionValues = []
        for i, ion in enumerate(ions):
            self.fill(i, ion)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        #connectTable(self, self.showOptions)
        # self.customContextMenuRequested['QPoint'].connect(partial(self.editRow, self, bools))

    '''def getIonValues(self):
        return self._ionValues'''
    '''def getData(self):
        data = []
        for i in range(self.rowCount()):
            data.append([self.item(i,j).text() for j in range(5)] + [self.item(i, 5).checkState()==2])
            #itemList.append([self.item(row, col).text() for col in range(len(self.getHeaders()))])
        print(data)
        return data'''

    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']

    def getHeaders(self):
        return ['m/z','z','intensity','name','error /ppm', 'S/N','quality error']

    def getValue(self,ion):
        return ion.getValues()

    def fill(self, row, ion):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        formats=self.getFormat()
        ionVal = []
        for j, item in enumerate(self.getValue(ion)):
            ionVal.append(item)
            if j == 3 or j==7:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(Qt.AlignLeft)
                if j==7:
                    newItem.setFont(self._smallFnt)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(Qt.DisplayRole, formats[j].format(item))
            newItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(row, j, newItem)
        self.resizeRowsToContents()
        self._ionValues.append(ionVal)

    def getIon(self, row):
        for ion in self._ions:
            if ion.getName() == self.item(row, 3).text() and ion.getCharge() == int(self.item(row, 1).text()):
                return ion

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        vals = self.getData()
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            df = pd.DataFrame([vals[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == copyAllAction:
            df = pd.DataFrame(data=vals, columns=self.getHeaders())
            df.to_clipboard(index=False, header=True)'''

    def getData(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append([self.item(row, col).text() for col in range(len(self.getHeaders()))])
        return itemList

class IsoPatternIon(IonTableWidget):
    '''
    Interactive ion table table for isotope pattern tool.
    '''
    def __init__(self, parent, ions, yPos):
        super(IsoPatternIon, self).__init__(parent, ions, yPos)
        connectTable(self, showOptions)

    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '', '{:10.4f}','{:10.4f}']

    def getHeaders(self):
        return ['m/z','z','intensity','name','quality error', 'formula', 'neutral mass', 'av. mass']

    def fill(self, row, ion):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        formats=self.getFormat()
        for j, item in enumerate(ion):
            if j == 3 or j==5:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(Qt.AlignLeft)
                newItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(Qt.DisplayRole, formats[j].format(item))
                    newItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(row, j, newItem)
        self.resizeRowsToContents()
        #self.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self))

    def getIntensity(self):
        if self._ions == ((),):
            return 1000
        try:
            return int(self.item(0,2).text())
        except ValueError:
            raise InvalidInputException('Unvalid intensity', self.item(0, 2).text())


    def getIon(self, row):
        return self._ions[row]

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        vals = self.getData()
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            df = pd.DataFrame([vals[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == copyAllAction:
            df = pd.DataFrame(data=vals, columns=self.getHeaders())
            df.to_clipboard(index=False, header=True)'''

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedCol = it.column()
            df = pd.DataFrame([self._ions[0][selectedCol]])
            df.to_clipboard(index=False, header=False)
        elif action == copyAllAction:
            df = pd.DataFrame(data=self._ions, columns=self.getHeaders())
            df.to_clipboard(index=False, header=True)'''

    def updateTable(self, newIons):
        self._ions = newIons
        for i, ion in enumerate(newIons):
            self.fill(i, ion)


class TickIonTableWidget(IonTableWidget):
    '''
    Interactive ion table table for checking overlapping ion clusters. Ticked ions are deleted.
    '''
    def __init__(self, parent, data, yPos):
        #self._headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self.checkBoxes = []
        super(TickIonTableWidget, self).__init__(parent, data, yPos)

    def getHeaders(self):
        return super(TickIonTableWidget, self).getHeaders() + ['del.?']

    def fill(self, row, ion):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        super(TickIonTableWidget, self).fill(row, ion)
        checkItem = QtWidgets.QTableWidgetItem()
        checkItem.setCheckState(Qt.Unchecked)  # QtCore.Qt.Unchecked
        self.setItem(row, len(self.getHeaders())-1, checkItem)
        #print(ion)
        self.checkBoxes.append((checkItem, ion))
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()


    def getDumpList(self):
        dumpList = []
        for row in self.checkBoxes:
            #checkBox = self.item(row, self.columnCount()-1)
            if row[0].checkState():
                dumpList.append(row[1])
        return dumpList

    def getData(self):
        itemList = []
        columns = len(self.getHeaders())
        for row in range(self.rowCount()):
            items = [self.item(row, col).text() for col in range(columns-1)]
            items.append(self.item(row, columns-1).checkState() == 2)
            itemList.append(items)
        return itemList


class CalibrationIonTableWidget(QTableWidget):
    '''
    Interactive ion table table for choosing ions for calibration in CalibrationView
    '''
    def __init__(self, parent, ions):
        super(CalibrationIonTableWidget, self).__init__(parent)
        #self._headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self._ions = ions
        self.setColumnCount(len(self.getHeaders()))
        #self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setRowCount(len(ions))
        self._ionValues = []
        for i, ion in enumerate(ions):
            self.fill(i, ion)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        connectTable(self, showOptions)
        #connectTable(self, self.showOptions)
        # self.customContextMenuRequested['QPoint'].connect(partial(self.editRow, self, bools))

    '''def getIonValues(self):
        return self._ionValues'''

    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '', '{:5.2f}', '']

    def getHeaders(self):
        return ['m/z','z','intensity','name','error /ppm', 'use']

    '''def getValue(self,ion):
        return ion.getValues()'''

    def fill(self, row, ionVals):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        formats=self.getFormat()
        #ionVal = []
        for j, item in enumerate(ionVals):
            #ionVal.append(item)
            if j == 3:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(Qt.AlignLeft)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.DisplayRole, formatString.format(item))
                #elif j == 4:
                #    newItem.setData(Qt.DisplayRole, item)
                elif j == 5:
                    continue
                elif j == 6:
                    checkItem = QtWidgets.QTableWidgetItem()
                    if item:
                        checkItem.setCheckState(Qt.Checked)  # Qt.Unchecked
                    else:
                        checkItem.setCheckState(Qt.Unchecked)  # Qt.Unchecked
                    self.setItem(row, 5, checkItem)
                else:
                    newItem.setData(Qt.DisplayRole, formats[j].format(item))
            newItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(row, j, newItem)
        #self.resizeRowsToContents()

    '''def getIon(self, row):
        for ion in self._ions:
            if ion.getName() == self.item(row, 3).text() and ion.getCharge() == int(self.item(row, 1).text()):
                return ion'''

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        vals = self.checkStatus()
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            df = pd.DataFrame([vals[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == copyAllAction:
            df = pd.DataFrame(data=vals, columns=self.getHeaders())
            df.to_clipboard(index=False, header=True)'''

    def checkStatus(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append((self.item(row, 3).text(),int(self.item(row, 1).text()),self.item(row, 5).checkState()))
        return itemList

    def getData(self):
        data = []
        for i in range(self.rowCount()):
            data.append([self.item(i,j).text() for j in range(5)] + [self.item(i, 5).checkState()==2])
            #itemList.append([self.item(row, col).text() for col in range(len(self.getHeaders()))])
        return data


"""class FinalIonTable(TickIonTableWidget):
    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.','comment', 'del.?']

    def getValue(self,ion):
        return ion.getValues()+ [ion.comment]"""