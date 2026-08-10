import traceback

from PyQt5 import QtWidgets

from src.Exceptions import InvalidInputException
from src.entities.GeneralEntities import Element, Macromolecule
from src.entities.IonTemplates import FragmentationPattern, ModificationPattern, IntactPattern
from src.gui.GUI_functions import createComboBox
from src.gui.controller.AbstractEditorController import AbstractEditorController, AbstractSimpleEditorController, \
    AbstractEditorControllerWithTabs
from src.gui.dialogs.OpenDialogs import OpenDialog
from src.services.DataServices import PeriodicTableService, MoleculeService, SequenceService, FragmentationService, \
    ModificationService, IntactIonService


class ElementEditorController(AbstractEditorController):
    '''
    Controller class to edit elements
    '''
    def __init__(self):
        super(ElementEditorController, self).__init__(PeriodicTableService(), "Edit Elements", "Element")
        self.createWidgets(self._centralwidget, self._formLayout, ["Name: "],
                           {"name": QtWidgets.QLineEdit(self._centralwidget)}, [self._pattern.getName()])
        self._widgets['name'].setToolTip('First Letter must be uppercase, all other letters must be lowercase')
        self._table = self.createTableWidget(self._centralwidget, self._pattern.getItems(),
                                            self._service.getHeaders(), self._service.getBoolVals())
        self._formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self._table)   #ToDo
        self._mainWindow.show()

    def save(self, *args):
        id = self._pattern.getId()
        if args and args[0] == None:
            id = None
        super(ElementEditorController, self).save(Element(self._widgets["name"].text(),
                                                          self.readTable(self._table, self._service.getBoolVals()), id))


class MoleculeEditorController(AbstractEditorController):
    '''
    Controller class to edit molecules
    '''
    def __init__(self, patternName=None):
        super(MoleculeEditorController, self).__init__(MoleculeService(), "Edit Molecular Properties", "Molecule", patternName)
        self.createWidgets(self._centralwidget, self._formLayout, ["Name: ", "Gain: ", "Loss: "],
                           {"name": QtWidgets.QLineEdit(self._centralwidget), 'gain': QtWidgets.QLineEdit(self._centralwidget),
                     'loss': QtWidgets.QLineEdit(self._centralwidget)},
                           [self._pattern.getName(), self._pattern.getGain(), self._pattern.getLoss()])
        self._widgets['gain'].setToolTip("Enter the molecular loss of the molecule formula compared to a pure composition"
                                        "of the corresponding building blocks")
        self._widgets['loss'].setToolTip("Enter the molecular gain of the molecule formula compared to a pure composition"
                                        "of the corresponding building blocks")
        self._table = self.createTableWidget(self._centralwidget, self._pattern.getItems(),
                                             self._service.getHeaders(), self._service.getBoolVals())
        self._formLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self._table)   #ToDo
        #QtWidgets.QTableWidget().horizontalHeader().setMaximumSectionSize(20)
        self._mainWindow.show()

    def addBB(self, translations:list[str], formulas:list[str]):
        newRow = self.getEmptyRow(self._table)
        for i in range(len(translations)):
            self.insertRow(self._table, [])
            self._table.setItem(newRow+i, 1, QtWidgets.QTableWidgetItem(translations[i]))
            self._table.setItem(newRow+i, 2, QtWidgets.QTableWidgetItem(formulas[i]))

    def save(self, *args):
        id = self._pattern.getId()
        if args and args[0] == None:
            id = None
        super(MoleculeEditorController, self).save(Macromolecule(self._widgets["name"].text(),
                                                             self._widgets["gain"].text(),self._widgets["loss"].text(),
                                                         self.readTable(self._table, self._service.getBoolVals()), id))

    def openAgain(self, title='Open'):
        '''
        To open a new pattern
        '''
        super(MoleculeEditorController, self).openAgain(title)
        self._widgets["gain"].setText(self._pattern.getGain())
        self._widgets["loss"].setText(self._pattern.getLoss())


class SequenceEditorController(AbstractSimpleEditorController):
    '''
    Controller class to edit sequences
    '''
    def __init__(self):
        self._service = SequenceService()
        self._moleculeService = MoleculeService()
        super(SequenceEditorController, self).__init__(self._service.getSequences(), "Edit Sequences",
                                           {"Save": (self.save, None, "Ctrl+S"), "Close": (self.close, None, "Ctrl+Q")})
        """if len(self._pattern)<5:
            [self._pattern.append(self._service.makeNew()) for i in range(6 - len(self._pattern))]"""
        self._table = self.createTableWidget(self._centralwidget, self._pattern,
                                             self._service.getHeaders(), self._service.getBoolVals())
        self._verticalLayout.addWidget(self._table)   #ToDo
        self._mainWindow.show()

    def copyPaste(self, table, bools, selectedRowIndex):
        newRow = self.getEmptyRow(table)
        self.insertRow(table, table.cellWidget(selectedRowIndex, 2).currentText())
        for j in range(table.columnCount()-1):
            if not table.item(selectedRowIndex, j) is None:
                table.setItem(newRow, j, QtWidgets.QTableWidgetItem(table.item(selectedRowIndex, j).text()))
        table.resizeRowsToContents()

    def insertRow(self, table, text=False):
        '''
        Inserts a row at the end of the table
        :param table:
        :param bools:
        :return:
        '''
        super().insertRow(table, [])
        comboBox = createComboBox(table,self._moleculeService.getAllPatternNames())
        if text:
            comboBox.setCurrentText(text)
        table.setCellWidget(table.rowCount()-1, table.columnCount()-1, comboBox)

    def addSequence(self, sequence:str, molecule:str):
        newRow = self.getEmptyRow(self._table)
        self.insertRow(self._table, molecule)
        self._table.setItem(newRow, 1, QtWidgets.QTableWidgetItem(sequence))


    def save(self):
        sequences = []
        for sequTuple in self.readTable(self._table, self._service.getBoolVals()):
            sequences.append((sequTuple[0], sequTuple[1], sequTuple[2]))
        try:
            super(SequenceEditorController, self).save(sequences)
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self._mainWindow, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    def formatTableWidget(self, headers, tableWidget, data, boolVals):
        '''
        Fills the QTableWidget with data
        :param (list[str] | tuple[str]) headers: names of the headers
        :param (QWidgets.QTableWidget) tableWidget:
        :param data: 2D data
        :param (list[int]) boolVals: indizes of columns with boolean values
        :return: tableWidget
        '''
        super(SequenceEditorController, self).formatTableWidget(headers, tableWidget, data, boolVals)
        allMolecules = self._moleculeService.getAllPatternNames()
        lastCol = len(data[0])-1
        for i, row in enumerate(data):
            comboBox = createComboBox(tableWidget,allMolecules)
            molecule = row[lastCol]
            if molecule in allMolecules:
                comboBox.setCurrentText(row[lastCol])
            else:
                QtWidgets.QMessageBox.warning(None, "Warning",
                                              'The molecule type "'+molecule+'" of sequence "'+ row[0] +
                                              '" is unknown. Change the molecule to an existing type or add '
                                              'the corresponding molecule type.',
                                              QtWidgets.QMessageBox.Ok)
            tableWidget.setCellWidget(i, lastCol, comboBox)
        tableWidget.horizontalHeader().setMaximumSectionSize(1500)
        return tableWidget


class FragmentEditorController(AbstractEditorControllerWithTabs):
    '''
    Controller class to edit fragmentations
    '''
    def __init__(self):
        super(FragmentEditorController, self).__init__(FragmentationService(), "Edit Fragments", "Fragment-Pattern")
        upperWidget = self.makeUpperWidget()
        precBox = createComboBox(self._centralwidget, [item[0] for item in self._pattern.getItems2() if item[5]])
        self.createWidgets(upperWidget, upperWidget.layout(), ["Name: ", 'Precursor: '],
                           {"name": QtWidgets.QLineEdit(self._centralwidget), 'precursor': precBox},
                           [self._pattern.getName(), self._pattern.getPrecursor()])
        self._tabWidget = self.makeTabWidget("Fragments", "Precursor-Fragments")
        self._table2.itemChanged.connect(self.updatePrecBox)
        self._mainWindow.show()

    def updatePrecBox(self):
        precNames = [item[0] for item in self.readTable(self._table2, self._service.getBoolVals()[1]) if item[5]]
        self._mainWindow.updateComboBox(self._widgets['precursor'], precNames)

    def save(self, *args):
        '''prec = self._widgets['precursor'].currentText()
        table2 = self.getData(self._table2, self._service.getBoolVals()[1])
        if prec not in [row[0] for row in table2]:
            QtWidgets.QMessageBox.warning(self._mainWindow, "Problem occured", prec + ' not found in table',
                                          QtWidgets.QMessageBox.Ok)'''
            #raise InvalidInputException('Precursor not found', prec + ' not included in table')
        id = self._pattern.getId()
        if args and args[0] == None:
            id = None
        super(FragmentEditorController, self).save(FragmentationPattern(self._widgets["name"].text(),
                                                    self._widgets['precursor'].currentText(),
                                                    self.readTable(self._table1, self._service.getBoolVals()[0]),
                                                    self.readTable(self._table2, self._service.getBoolVals()[1]), id))


    def openAgain(self, title='Open'):
        '''
        To open a new pattern
        '''
        super(FragmentEditorController, self).openAgain(title)
        self.updatePrecBox()
        self._widgets['precursor'].setCurrentText(self._pattern.getPrecursor())

    def insertRow(self, table, bools):
        super().insertRow(table, bools)
        table.setItem(table.rowCount() - 1, 4, QtWidgets.QTableWidgetItem("0"))


class ModificationEditorController(AbstractEditorControllerWithTabs):
    '''
    Controller class to edit modification patterns
    '''
    def __init__(self):
        super(ModificationEditorController, self).__init__(ModificationService(), "Edit Modifications",
                                                           "Modification-Pattern")
        upperWidget = self.makeUpperWidget()
        self._modNames = self.getNames(self._pattern.getItems())
        self.createWidgets(upperWidget, upperWidget.layout(), ["Name: ", "Precursor Modification: "],
                           {"name": QtWidgets.QLineEdit(self._centralwidget),
                                   "modification": createComboBox(self._centralwidget, [""]+self._modNames)},
                           [self._pattern.getName(), self._pattern.getModification()])
        self._widgets["name"].setToolTip("Pattern will be stored under this name.")
        self._widgets["modification"].setToolTip("Modification of the precursor")
        self._tabWidget = self.makeTabWidget("Modifications", "Excluded Modifications")
        self._tab1.setToolTip("For every fragment, the corresponding modified fragment will be included")
        self._tab2.setToolTip("These modifications will be excluded from ion search")
        self._table2.setColumnWidth(0, 200)
        self._table1.itemChanged.connect(self.updateModBox)
        self._mainWindow.show()

    def getNames(self, data):
        return [row[0] for row in data if row[7]]

    def updateModBox(self):
        names = self.getNames(self.readTable(self._table1, self._service.getBoolVals()[0]))
        if names!=self._modNames:
            self._modNames= names
            """self._widgets["modification"].clear()
            self._widgets["modification"].addItems([""]+self._modNames)"""
            self._mainWindow.updateComboBox(self._widgets['modification'], names, True)


    def openAgain(self, title='Open'):
        '''
        To open a new pattern
        '''
        super(ModificationEditorController, self).openAgain(title)
        self._widgets["modification"].setCurrentText(self._pattern.getModification())

    def open(self, title):
        '''
        To open a pattern
        '''
        openDialog = OpenDialog(title, self._service.getAllPatternNames()[1:] + ['--New--'])
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            name = openDialog.getName()
            if name != "--New--":
                return self._service.get(name)
            else:
                return self._service.makeNew()

    def save(self, *args):
        id = self._pattern.getId()
        if args and args[0] == None:
            id = None
        super(ModificationEditorController, self).save(ModificationPattern(self._widgets["name"].text(),
                                                                           self._widgets["modification"].currentText(), self.readTable(self._table1, self._service.getBoolVals()[0]),
                                                                           self.readTable(self._table2, self._service.getBoolVals()[1]), id))

    def delete(self):
        '''
        Delets a pattern
        '''
        openDialog = OpenDialog("Delete", self._service.getAllPatternNames())
        # openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            text = openDialog.getName()
            if text != "--New--" and text != '-':
                choice = QtWidgets.QMessageBox.question(self._mainWindow, 'Deleting ',
                                                        "Warning: Deleting " + text +
                                                        " cannot be undone!\n\nResume?",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.Yes:
                    print("deleting", text)
                    self._pattern = self._service.delete(text)
            else:
                #raise InvalidInputException('Deleting', 'Deleting "'+text+ '" not possible')
                QtWidgets.QMessageBox.warning(self._mainWindow, "Problem occured", 'Deleting "'+text+ '" not possible',
                                              QtWidgets.QMessageBox.Ok)


    def insertRow(self, table, bools):
        super().insertRow(table, bools)
        if table.columnCount() > 1:
            table.setItem(table.rowCount() - 1, 4, QtWidgets.QTableWidgetItem("0"))
            table.setItem(table.rowCount() - 1, 5, QtWidgets.QTableWidgetItem("0"))


class IntactIonEditorController(AbstractEditorController):
    '''
    Controller class to intact ion patterns
    '''
    def __init__(self):
        super(IntactIonEditorController, self).__init__(IntactIonService(),
                                                        "Edit Intact Ions", "Modification")
        self.createWidgets(self._centralwidget, self._formLayout, ["Name: "],
                                  {"name": QtWidgets.QLineEdit(self._centralwidget)}, [self._pattern.getName()])
        self._table = self.createTableWidget(self._centralwidget, self._pattern.getItems(), self._service.getHeaders(),
                                             self._service.getBoolVals())
        self._formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self._table)
        self._mainWindow.resize(500, 300)
        self._mainWindow.show()

    def save(self, *args):
        id = self._pattern.getId()
        if args and args[0] == None:
            id = None
        super(IntactIonEditorController, self).save(IntactPattern(self._widgets["name"].text(),
                                                                  self.readTable(self._table, self._service.getBoolVals()), id))


    def insertRow(self, table, bools):
        super().insertRow(table, bools)
        table.setItem(table.rowCount() - 1, 3, QtWidgets.QTableWidgetItem("0"))
        table.setItem(table.rowCount() - 1, 4, QtWidgets.QTableWidgetItem("0"))