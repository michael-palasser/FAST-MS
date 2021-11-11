import traceback
from functools import partial

from PyQt5 import QtWidgets, QtCore

from src.Exceptions import CanceledException
from src.services.DataServices import *
from src.gui.AbstractMainWindows import SimpleMainWindow
from src.gui.GUI_functions import createComboBox
from src.gui.dialogs.SimpleDialogs import OpenDialog


class AbstractSimpleEditorController(ABC):
    '''
    Abstract controller class: parent class of AbstractEditorController and SequenceEditorController
    '''
    def __init__(self, pattern, title, options):
        self._pattern = pattern
        #self.pattern = self.service.makeNew()
        self.setUpUi(title)
        self._mainWindow.createMenuBar()
        self._fileMenu, self._fileMenuActions = self._mainWindow.createMenu("File", options, 3)

    def setUpUi(self, title):
        self._mainWindow = SimpleMainWindow(None, title)
        #self.mainWindow.setObjectName(title)
        self._translate = QtCore.QCoreApplication.translate
        self._centralwidget = self._mainWindow.centralWidget()
        self._formLayout = QtWidgets.QFormLayout(self._centralwidget)
        self._formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)


    def createTableWidget(self, parent, data, headers, bools):
        tableWidget = QtWidgets.QTableWidget(parent)
        #headers = self.service.getHeaders()
        tableWidget.setColumnCount(len(headers.keys()))
        #tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #tableWidget.customContextMenuRequested['QPoint'].connect(self.h3_table_right_click)
        #tableWidget.move(20,yPos) #70
        tableWidget = self.formatTableWidget(headers, tableWidget, data, bools)
        tableWidget.setHorizontalHeaderLabels(headers)
        tableWidget.resizeColumnsToContents()
        tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tableWidget.customContextMenuRequested['QPoint'].connect(partial(self.editRow, tableWidget, bools))
        tableWidget.setSortingEnabled(True)
        tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        return tableWidget

    def formatTableWidget(self, headers, tableWidget, data, boolVals):
        '''
        Fills the QTableWidget with data
        :param (list[str] | tuple[str]) headers: names of the headers
        :param (QWidgets.QTableWidget) tableWidget:
        :param data: 2D data
        :param (list[int]) boolVals: indizes of columns with boolean values
        :return: tableWidget
        '''
        headerKeys = list(headers.keys())
        tableWidget.setRowCount(len(data))
        tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        tableWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        for i, row in enumerate(data):
            for j, item in enumerate(row):
                if j in boolVals:
                    newItem = QtWidgets.QTableWidgetItem(item)
                    if item == 1:
                        newItem.setCheckState(QtCore.Qt.Checked)
                    elif item == 0:
                        newItem.setCheckState(QtCore.Qt.Unchecked)
                    tableWidget.setItem(i, j, newItem)
                else:
                    newItem = QtWidgets.QTableWidgetItem(str(item))
                    tableWidget.setItem(i, j, newItem)
                #tableWidget.setItem(i, j, newitem)
                newItem.setToolTip(headers[headerKeys[j]])
        if len(data) < 7:
            for i in range(7-len(data)):
                self.insertRow(tableWidget, boolVals)
        tableWidget.resizeColumnsToContents()
        tableWidget.resizeRowsToContents()
        return tableWidget

    def save(self, *args):
        try:
            self._pattern = self._service.save(args[0])
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self._mainWindow, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)


    def readTable(self, table, boolVals):
        '''
        Reads the values from the table
        :param (QWidgets.QTableWidget) table: tableWidget
        :param (list[int]) boolVals: indizes of columns with boolean values
        :return:
        '''
        itemList = []
        for row in range(table.rowCount()):
            if table.item(row,0) == None or table.item(row,0).text() == "":
                continue
            rowData = []
            for col in range(table.columnCount()):
                widgetItem = table.item(row, col)
                if col in boolVals:
                    try:
                        rowData.append(int(widgetItem.checkState()/2))
                    except AttributeError as e:
                        newItem = QtWidgets.QTableWidgetItem()
                        newItem.setCheckState(QtCore.Qt.Checked)
                        table.setItem(row,col, newItem)
                        rowData.append(1)
                        print(row,col,boolVals,widgetItem)
                        raise Warning(e.__str__())
                elif widgetItem and widgetItem.text():
                    rowData.append(widgetItem.text())
                else:
                    rowData.append("")
            itemList.append(rowData)
        return itemList

    def editRow(self, table, bools, pos):
        '''
        Right click menu options for the table
        :param table:
        :param bools:
        :param pos:
        :return:
        '''
        it = table.itemAt(pos)
        if it is None:
            return
        selectedRowIndex = it.row()
        columnCount = table.columnCount()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, selectedRowIndex, columnCount - 1, selectedRowIndex)
        table.setRangeSelected(item_range, True)
        menu = QtWidgets.QMenu()
        insertRowAction = menu.addAction("Insert row")
        copyRowAction = menu.addAction("Copy and insert row")
        deleteRowAction = menu.addAction("Delete row")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == insertRowAction:
            self.insertRow(table, bools)
            table.resizeRowsToContents()
        elif action == copyRowAction:
            rowCount = table.rowCount()
            emptyRow = rowCount
            for rowNr in range(rowCount):
                if table.item(rowNr, 0) == None or table.item(rowNr, 0).text() == "":
                    emptyRow = rowNr
                    break
            if emptyRow == rowCount:
                #self.insertRow(table, bools)
                table.insertRow(rowCount)
            for j in range(columnCount):
                if not table.item(selectedRowIndex, j) is None:
                    table.setItem(emptyRow, j, QtWidgets.QTableWidgetItem(table.item(selectedRowIndex, j).text()))
                    if j in bools:
                        print('bool',emptyRow, j)
                        table.item(emptyRow, j).setCheckState(table.item(selectedRowIndex, j).checkState())
            table.resizeRowsToContents()
        if action == deleteRowAction:
            table.removeRow(selectedRowIndex)


    def insertRow(self, table, bools):
        '''
        Inserts a row at the end of the table
        :param table:
        :param bools:
        :return:
        '''
        table.insertRow(table.rowCount())
        for i in bools:
            newitem = QtWidgets.QTableWidgetItem(0)
            newitem.setCheckState(QtCore.Qt.Unchecked)
            table.setItem(table.rowCount() - 1, i, newitem)


    def close(self):
        self._service.close()
        self._mainWindow.close()


class AbstractEditorController(AbstractSimpleEditorController, ABC):
    '''
    Abstract controller class to edit patterns with items: parent class of AbstractEditorControllerWithTabs,
    ElementEditorController, IntactIonEditorController, MoleculeEditorController
    '''
    def __init__(self, service, title, name):
        self._service = service
        pattern = self.open('Open ' + name)
        if pattern == None:
            self._service.close()
            raise CanceledException("Closing")
        super(AbstractEditorController, self).__init__(pattern, title,
                   {"Open " + name: (self.openAgain, None,"Ctrl+O"), "Delete " + name: (self.delete,None,None),
                    "Save": (self.save,None,"Ctrl+S"), "Save As": (self.saveNew,None,None),
                    "Close": (self.close,None,"Ctrl+Q")})


    def createWidgets(self, parent, formLayout, labels, widgets, initialValues):
        """
        Formats widgets with labels into a QFormlayout.
        :param labels: list of label names
        :param widgets: dict of {name:widget}
        :return: (int) number of widgets
        """
        maxWidth = 0
        for i, labelName in enumerate(labels):
            label = QtWidgets.QLabel(parent)
            width = len(labelName)*10
            label.setText(self._translate(self._mainWindow.objectName(), labelName))
            formLayout.setWidget(i, QtWidgets.QFormLayout.LabelRole, label)
            if width>maxWidth:
                maxWidth = width
        self._widgets = dict()
        counter = 0
        for widgetName, widget in widgets.items():
            widget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
            formLayout.setWidget(counter, QtWidgets.QFormLayout.FieldRole, widget)
            self._widgets[widgetName] = widget
            counter+=1
        for widget, initVal in zip(self._widgets.values(), initialValues):
            if isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentText(initVal)
            else:
                widget.setText(initVal)
        return counter

    def openAgain(self, title = "Open"):
        '''
        To open a new pattern
        '''
        if title is False:
            title = "Open"
        openedPattern = self.open(title)
        if openedPattern != None:
            self._pattern = openedPattern
        self._widgets["name"].setText(self._pattern.getName())
        self._table = self.formatTableWidget(self._service.getHeaders(), self._table, self._pattern.getItems(),
                                             self._service.getBoolVals())

    def open(self, title):
        '''
        To open a pattern
        '''
        openDialog = OpenDialog(title, self._service.getAllPatternNames() + ['--New--'])
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            name = openDialog.getName()
            if name != "--New--":
                return self._service.get(name)
            else:
                return self._service.makeNew()


    def delete(self):
        '''
        Delets a pattern
        '''
        openDialog = OpenDialog("Delete", self._service.getAllPatternNames())
        #openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            text = openDialog.getName()
            if text != "--New--":
                print('Deleting '+text)
                choice = QtWidgets.QMessageBox.question(self._mainWindow, 'Deleting ',
                                                        "Warning: Deleting " + text +
                                                        " cannot be undone!\n\nResume?",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.Yes:
                    print("deleting",text)
                    self._pattern = self._service.delete(text)



    def saveNew(self):
        self.save(None)



    """def copyRow(self):
        rowCount = self._table.rowCount()
        columnCount = self._table.columnCount()
        rowSelecter = RowSelecter(rowCount, "Copy Row")
        if rowSelecter.exec_() and rowSelecter.accepted:
            self._table.insertRow(self._table.rowCount())
            copiedRow = rowSelecter.spinBox.value() - 1
            for j in range(columnCount):
                if not self._table.item(copiedRow, j) is None:
                    self._table.setItem(rowCount, j, QTableWidgetItem(self._table.item(copiedRow, j).text()))
            self._table.item(rowCount, columnCount-1).setCheckState(QtCore.Qt.Checked)"""




class AbstractEditorControllerWithTabs(AbstractEditorController, ABC):
    '''
    Abstract controller class to edit patterns with multiple item classes: parent class of FragmentEditorController,
    ModificationEditorController
    '''
    def setUpUi(self, title):
        self._mainWindow = SimpleMainWindow(None,title)
        self._translate = QtCore.QCoreApplication.translate
        self._centralwidget = self._mainWindow.centralWidget()
        self._vertLayout = QtWidgets.QVBoxLayout(self._centralwidget)

    def makeTabWidget(self, tabName1, tabName2):
        tabWidget = QtWidgets.QTabWidget(self._centralwidget)
        self._tab1, self._table1 = self.makeTab(tabWidget, self._pattern.getItems(), 0, tabName1)
        self._tab2, self._table2 = self.makeTab(tabWidget, self._pattern.getItems2(), 1, tabName2)
        tabWidget.setEnabled(True)
        self._vertLayout.addWidget(tabWidget)
        return tabWidget

    def makeTab(self, tabWidget, items, index, tabName):
        tab = QtWidgets.QWidget()
        vertLayout = QtWidgets.QVBoxLayout(tab)
        vertLayout.setContentsMargins(4,12,4,12)
        table = self.createTableWidget(tab, items, self._service.getHeaders()[index], self._service.getBoolVals()[index])
        vertLayout.addWidget(table)
        tabWidget.addTab(tab, "")
        tabWidget.setTabText(tabWidget.indexOf(tab), self._translate(self._mainWindow.objectName(), tabName))
        return tab, table


    def makeUpperWidget(self):
        upperWidget = QtWidgets.QWidget(self._centralwidget)
        formLayout = QtWidgets.QFormLayout(upperWidget)
        formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self._vertLayout.addWidget(upperWidget)
        return upperWidget

    def openAgain(self, title='Open'):
        '''
        To open a new pattern
        '''
        openedPattern = self.open(title)
        if openedPattern != None:
            self._pattern = openedPattern
        self._widgets["name"].setText(self._pattern.getName())
        self._table1 = self.formatTableWidget(self._service.getHeaders()[0], self._table1, self._pattern.getItems(),
                                              self._service.getBoolVals()[0])
        self._table2 = self.formatTableWidget(self._service.getHeaders()[1], self._table2, self._pattern.getItems2(),
                                              self._service.getBoolVals()[1])


class MoleculeEditorController(AbstractEditorController):
    '''
    Controller class to edit molecules
    '''
    def __init__(self):
        super(MoleculeEditorController, self).__init__(MoleculeService(), "Edit Molecular Properties", "Molecule")
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
        self._mainWindow.show()

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
        super(MoleculeEditorController, self).openAgain()
        self._widgets["gain"].setText(self._pattern.getGain())
        self._widgets["loss"].setText(self._pattern.getLoss())



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



class SequenceEditorController(AbstractSimpleEditorController):
    '''
    Controller class to edit sequences
    '''
    def __init__(self):
        self._service = SequenceService()
        super(SequenceEditorController, self).__init__(self._service.getSequences(), "Edit Sequences",
                                           {"Save": (self.save, None, "Ctrl+S"), "Close": (self.close, None, "Ctrl+Q")})
        if len(self._pattern)<5:
            [self._pattern.append(self._service.makeNew()) for i in range(6 - len(self._pattern))]
        self._table = self.createTableWidget(self._centralwidget, self._pattern,
                                             self._service.getHeaders(), self._service.getBoolVals())
        self._formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self._table)   #ToDo
        self._mainWindow.show()

    def save(self):
        sequences = []
        for sequTuple in self.readTable(self._table, self._service.getBoolVals()):
            sequences.append((sequTuple[0], sequTuple[1], sequTuple[2]))
        super(SequenceEditorController, self).save(sequences)


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
        table2 = self.readTable(self._table2, self._service.getBoolVals()[1])
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
        super(FragmentEditorController, self).openAgain()
        self.updatePrecBox()
        self._widgets['precursor'].setCurrentText(self._pattern.getPrecursor())



class ModificationEditorController(AbstractEditorControllerWithTabs):
    '''
    Controller class to edit modification patterns
    '''
    def __init__(self):
        super(ModificationEditorController, self).__init__(ModificationService(), "Edit Modifications",
                                                           "Modification-Pattern")
        upperWidget = self.makeUpperWidget()
        self.createWidgets(upperWidget, upperWidget.layout(), ["Name: ", "Modification: "],
                           {"name": QtWidgets.QLineEdit(self._centralwidget),
                                   "modification": QtWidgets.QLineEdit(self._centralwidget)},
                           [self._pattern.getName(), self._pattern.getModification()])
        self._widgets["name"].setToolTip("Pattern will be stored under this name.")
        self._widgets["modification"].setToolTip("Modification of the precursor")
        self._tabWidget = self.makeTabWidget("Modifications", "Excluded Modifications")
        self._tab1.setToolTip("For every fragment, the corresponding modified fragment will be included")
        self._tab2.setToolTip("These modifications will be excluded from ion search")
        self._table2.setColumnWidth(0, 200)
        self._mainWindow.show()

    def openAgain(self, title='Open'):
        '''
        To open a new pattern
        '''
        super(ModificationEditorController, self).openAgain()
        self._widgets["modification"].setText(self._pattern.getModification())

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
                                                                           self._widgets["modification"].text(), self.readTable(self._table1, self._service.getBoolVals()[0]),
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
                print('Deleting ' + text)
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
