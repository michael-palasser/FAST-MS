from abc import ABC
from functools import partial

from PyQt5 import QtWidgets, QtCore
import sys


from src.Services import *
from src.gui.SimpleDialogs import OpenDialog


class AbstractSimpleEditorController(ABC):
    def __init__(self, service, pattern, title, options):
        self.service = service
        if pattern == None:
            self.pattern = self.service.makeNew()
        else:
            self.pattern = pattern
        #self.pattern = self.service.makeNew()
        self.setUpUi(title)
        self.createMenuBar(options)

    def setUpUi(self, title):
        self.mainWindow = QtWidgets.QMainWindow()
        self.mainWindow.setObjectName(title)
        self._translate = QtCore.QCoreApplication.translate
        self.mainWindow.setWindowTitle(self._translate(self.mainWindow.objectName(), title))
        self.centralwidget = QtWidgets.QWidget(self.mainWindow)

        self.mainWindow.setCentralWidget(self.centralwidget)
        #self.formLayout = QtWidgets.QFormLayout(self.centralwidget)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.upperWidget = QtWidgets.QWidget(self.centralwidget)
        self.formLayout = QtWidgets.QFormLayout(self.upperWidget)

        self.mainWindow.setStatusBar(QtWidgets.QStatusBar(self.mainWindow))


    def createMenuBar(self, options):
        self.menubar = QtWidgets.QMenuBar(self.mainWindow)
        self.mainWindow.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.fileMenu, self.fileMenuActions = self.createMenu("File", options, 3)
        #self.editMenu, self.editMenuActions = self.createMenu("Edit", {"Insert Row": self.insertRow}, 1)
        self.menubar.addAction(self.fileMenu.menuAction())
        #self.menubar.addAction(self.editMenu.menuAction())


    def createMenu(self, name, options, separatorPosition):
        menu = QtWidgets.QMenu(self.menubar)
        menu.setTitle(self._translate(self.mainWindow.objectName(), name))
        menuActions = dict()
        pos = len(options)
        for option, function in options.items():
            if pos == separatorPosition:
                menu.addSeparator()
            action = QtWidgets.QAction(self.mainWindow)
            action.setText(self._translate(self.mainWindow.objectName(),option))
            if 'Open' in option:
                action.setShortcut("Ctrl+O")
            elif option == 'Save':
                action.setShortcut("Ctrl+S")
            elif option == 'Close':
                action.setShortcut("Ctrl+Q")
            action.triggered.connect(function)
            menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        return menu, menuActions

    def createTableWidget(self, parent, data, yPos, headers, bools):
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
        return tableWidget

    def formatTableWidget(self, headers, tableWidget, data, bools):
        headerKeys = list(headers.keys())
        tableWidget.setRowCount(len(data))
        tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        tableWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        for i, row in enumerate(data):
            for j, item in enumerate(row):
                if j in bools:
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
                self.insertRow(tableWidget, bools)
        tableWidget.resizeColumnsToContents()
        tableWidget.resizeRowsToContents()
        return tableWidget

    def save(self, *args):
        pass


    def readTable(self, table):
        itemList = []
        for row in range(table.rowCount()):
            if table.item(row,0) == None or table.item(row,0).text() == "":
                continue
            rowData = []
            for col in range(table.columnCount()):
                widgetItem = table.item(row, col)
                if col in self.service.getBoolVals():
                    rowData.append(int(widgetItem.checkState()/2))
                elif widgetItem and widgetItem.text():
                    rowData.append(widgetItem.text())
                else:
                    rowData.append("")
            itemList.append(rowData)
        return itemList


    def editRow(self, table, bools, pos):
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
            """table.insertRow(table.rowCount())
            for i in bools:
                newitem = QtWidgets.QTableWidgetItem(0)
                newitem.setCheckState(QtCore.Qt.Checked)
                table.setItem(table.rowCount() - 1, i, newitem)"""
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
                table.insertRow(rowCount)
            for j in range(columnCount):
                if not table.item(selectedRowIndex, j) is None:
                    table.setItem(emptyRow, j, QtWidgets.QTableWidgetItem(table.item(selectedRowIndex, j).text()))
                    if j in bools:
                        table.item(emptyRow, j).setCheckState(table.item(selectedRowIndex, j).checkState())
            table.resizeRowsToContents()
        if action == deleteRowAction:
            table.removeRow(selectedRowIndex)


    def insertRow(self, table, bools):
        table.insertRow(table.rowCount())
        for i in bools:
            newitem = QtWidgets.QTableWidgetItem(0)
            newitem.setCheckState(QtCore.Qt.Unchecked)
            table.setItem(table.rowCount() - 1, i, newitem)


    def close(self):
        self.service.close()
        self.mainWindow.close()


class AbstractEditorController(AbstractSimpleEditorController, ABC):
    def __init__(self, service, title, name):
        self.service = service
        super(AbstractEditorController, self).__init__(service, self.open('Open '+name), title,
                   {#"New " + name: self.createNew,
                    "Open " + name: self.openAgain,
                    "Delete a  " + name: self.delete,
                    "Save": self.save, "Save As": self.saveNew, "Close": self.close})

    def createWidgets(self, labels, widgets, initYPos, widgetWith, initialValues):
        """

        :param labels: list of Strings
        :param widgets: dict of {name:widget}
        :return:
        """
        maxWidth = 0
        yPos = initYPos
        for i, labelName in enumerate(labels):
            label = QtWidgets.QLabel(self.upperWidget)
            width = len(labelName)*10
            label.setGeometry(QtCore.QRect(20, yPos, width, 16))
            label.setText(self._translate(self.mainWindow.objectName(), labelName))
            self.formLayout.setWidget(i, QtWidgets.QFormLayout.LabelRole, label)
            if width>maxWidth:
                maxWidth = width
            #yPos += 30
        #yPos = initYPos
        self.widgets = dict()
        counter = 0
        for widgetName, widget in widgets.items():
            #widget = QtWidgets.QLineEdit(self.centralwidget)
            widget.setGeometry(QtCore.QRect(maxWidth+20, yPos, widgetWith, 21))
            self.formLayout.setWidget(counter, QtWidgets.QFormLayout.FieldRole, widget)
            self.widgets[widgetName] = widget
            #yPos += 30
            counter+=1
        for widget, initVal in zip(self.widgets.values(),initialValues):
            widget.setText(initVal) #self.pattern.getName()
        self.verticalLayout.addWidget(self.upperWidget)
        return counter


    """def createNew(self):
        self.openAgain("Choose a Template")"""

    def openAgain(self, *args):
        title = "Open"
        if args and args[0]:
            title = args[0]
        """openDialog = OpenDialog(title, self.service.getAllPatternNames())
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            if openDialog.comboBox.currentText() != "--New--":
                print("openAgain",openDialog.comboBox.currentText())
                self.pattern = self.service.get(openDialog.comboBox.currentText())
            else:
                self.pattern = self.service.makeNew()"""
        openedPattern = self.open(title)
        if openedPattern != None:
            self.pattern = openedPattern
        self.widgets["name"].setText(self.pattern.getName())
        self.table = self.formatTableWidget(self.service.getHeaders(), self.table, self.pattern.getItems(),
                                            self.service.getBoolVals())

    def open(self, title):
        openDialog = OpenDialog(title, self.service.getAllPatternNames())
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            if openDialog.comboBox.currentText() != "--New--":
                return self.service.get(openDialog.comboBox.currentText())
            else:
                return self.service.makeNew()


    def delete(self):
        """title = "Delete Intact Modification"
        if args != (False,):
            title = args[0]"""
        openDialog = OpenDialog("Delete", self.service.getAllPatternNames())
        #openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            if openDialog.comboBox.currentText() != "--New--":
                print('Deleting '+openDialog.comboBox.currentText())
                choice = QtWidgets.QMessageBox.question(self.mainWindow, 'Deleting ',
                                                        "Warning: Deleting " +  openDialog.comboBox.currentText() +
                                                        " cannot be undone!\n\nResume?",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.Yes:
                    print("deleting",openDialog.comboBox.currentText())
                    self.pattern = self.service.delete(openDialog.comboBox.currentText())



    def saveNew(self):
        self.save(None)



    """def copyRow(self):
        rowCount = self.table.rowCount()
        columnCount = self.table.columnCount()
        rowSelecter = RowSelecter(rowCount, "Copy Row")
        if rowSelecter.exec_() and rowSelecter.accepted:
            self.table.insertRow(self.table.rowCount())
            copiedRow = rowSelecter.spinBox.value() - 1
            for j in range(columnCount):
                if not self.table.item(copiedRow, j) is None:
                    self.table.setItem(rowCount, j, QTableWidgetItem(self.table.item(copiedRow, j).text()))
            self.table.item(rowCount, columnCount-1).setCheckState(QtCore.Qt.Checked)"""




class AbstractEditorControllerWithTabs(AbstractEditorController, ABC):


    """def setUpUi(self, title):
        super(AbstractEditorControllerWithTabs, self).setUpUi(title)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.centralwidget.setLayout(self.verticalLayout)
        self.upperWidget = QtWidgets.QWidget(self.centralwidget)
        self.formLayout = QtWidgets.QFormLayout(self.upperWidget)
        self.verticalLayout.addWidget(self.upperWidget)"""

    def makeTabWidget(self, yPos, tabName1, tabName2):
        tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        #tabWidget.setGeometry(QtCore.QRect(20, yPos+50, 201, 181))
        self.tab1 = QtWidgets.QWidget()

        #print('1')
        #verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        #print('2')
        #self.tab1.setLayout(verticalLayout)

        #print('3')
        self.table1 = self.createTableWidget(self.tab1, self.pattern.getItems(), yPos+50, self.service.getHeaders()[0],
                                             self.service.getBoolVals()[0])
        '''tabWidget.resize(200,200)
        self.tab1.resize(200,200)'''

        tabWidget.addTab(self.tab1, "")
        tabWidget.setTabText(tabWidget.indexOf(self.tab1), self._translate("MainWindow", tabName1))

        #verticalLayout.addWidget(self.tab1)
        self.tab2 = QtWidgets.QWidget(self.centralwidget)
        #print("2:", self.pattern.getItems2())
        self.table2 = self.createTableWidget(self.tab2, self.pattern.getItems2(), yPos+50, self.service.getHeaders()[1],
                                             self.service.getBoolVals()[1])
        tabWidget.addTab(self.tab2, "")
        tabWidget.setTabText(tabWidget.indexOf(self.tab2), self._translate("MainWindow", tabName2))
        tabWidget.setEnabled(True)
        #self.formLayout.setWidget(yPos+1, QtWidgets.QFormLayout.SpanningRole, tabWidget)   #ToDo
        #self.formLayout.setWidget(yPos+2, QtWidgets.QFormLayout.SpanningRole, self.tab1)   #ToDo

        self.table1.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        #verticalSpacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        #self.formLayout.setItem(yPos+2, QtWidgets.QFormLayout.SpanningRole, verticalSpacer)   #ToDo
        tabWidget.setMinimumSize(500,300)
        self.verticalLayout.addWidget(tabWidget)
        return tabWidget


    """def makeTabWidget(self, yPos, tabName1, tabName2):
        tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        #tabWidget.setGeometry(QtCore.QRect(20, yPos+50, 201, 181))
        '''self.tab1 = QtWidgets.QWidget(self.centralwidget)
        verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tab1.setLayout()
        self.table1 = self.createTableWidget(self.tab1, self.pattern.getItems(), yPos+50, self.service.getHeaders()[0],
                                             self.service.getBoolVals()[0])
        tabWidget.addTab(self.tab1, "")
        verticalLayout.addWidget(self.table1)'''
        self.tab1, self.table1 = self.makeTab(yPos+50, tabWidget)
        tabWidget.setTabText(tabWidget.indexOf(self.tab1), self._translate(self.mainWindow.objectName(), tabName1))
        '''self.tab2 = QtWidgets.QWidget()
        print("2:", self.pattern.getItems2())
        self.table2 = self.createTableWidget(self.tab2, self.pattern.getItems2(), yPos+50, self.service.getHeaders()[1],
                                             self.service.getBoolVals()[1])
        tabWidget.addTab(self.tab2, "")'''
        self.tab1, self.table1 = self.makeTab(yPos, tabWidget)
        tabWidget.setTabText(tabWidget.indexOf(self.tab2), self._translate("MainWindow", tabName2))
        tabWidget.setEnabled(True)


        self.formLayout.setWidget(yPos+1, QtWidgets.QFormLayout.SpanningRole, tabWidget)   #ToDo
        self.table1.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        return tabWidget

    def makeTab(self,yPos,tabWidget):
        tab = QtWidgets.QWidget(self.centralwidget)
        verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        tab.setLayout(verticalLayout)
        table = self.createTableWidget(tab, self.pattern.getItems(), yPos + 50,
                                             self.service.getHeaders()[0],
                                             self.service.getBoolVals()[0])
        tabWidget.addTab(tab, "")
        verticalLayout.addWidget(table)
        return tab, table"""

    def openAgain(self, *args):
        title = "Open"
        if args and args[0]:
            title = args[0]
        openedPattern = self.open(title)
        if openedPattern != None:
            self.pattern = openedPattern
        self.widgets["name"].setText(self.pattern.getName())
        self.table1 = self.formatTableWidget(self.service.getHeaders()[0], self.table1, self.pattern.getItems(),
                                            self.service.getBoolVals()[0])
        self.table2 = self.formatTableWidget(self.service.getHeaders()[1], self.table2, self.pattern.getItems2(),
                                             self.service.getBoolVals()[1])


class MoleculeEditorController(AbstractEditorController):
    def __init__(self):
        super(MoleculeEditorController, self).__init__(MoleculeService(), "Edit Molecular Properties", "Molecule")
        yPos = self.createWidgets(["Name: ", "Gain: ", "Loss: "],
                    {"name": QtWidgets.QLineEdit(self.upperWidget), 'gain': QtWidgets.QLineEdit(self.upperWidget),
                     'loss': QtWidgets.QLineEdit(self.upperWidget)},
                    20, 150, [self.pattern.getName(), self.pattern.getGain(), self.pattern.getLoss()])
        self.widgets['gain'].setToolTip("Enter the molecular loss of the molecule formula compared to a pure composition"
                                        "of the corresponding building blocks")
        self.widgets['loss'].setToolTip("Enter the molecular gain of the molecule formula compared to a pure composition"
                                        "of the corresponding building blocks")
        self.table = self.createTableWidget(self.centralwidget, self.pattern.getItems(), yPos+50,
                                            self.service.getHeaders(), self.service.getBoolVals())
        self.verticalLayout.addWidget(self.table)
        #self.formLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.table)   #ToDo
        self.mainWindow.show()

    def save(self, *args):
        id = self.pattern.getId()
        if args and args[0]:
            id = args[0]
        self.service.savePattern(Makromolecule(self.widgets["name"].text(), self.widgets["gain"].text(),
                                               self.widgets["loss"].text(), self.readTable(self.table), id))

    def openAgain(self, *args):
        super(MoleculeEditorController, self).openAgain()
        self.widgets["gain"].setText(self.pattern.getGain())
        self.widgets["loss"].setText(self.pattern.getLoss())

    """def saveNew(self):
        self.service.savePattern(Makromolecule(self.widgets["name"].text(), self.readTable(self.table), None))"""

class ElementEditorController(AbstractEditorController):
    def __init__(self):
        super(ElementEditorController, self).__init__(PeriodicTableService(), "Edit Elements", "Element")
        """self.pattern = self.open('Open Element')
        if self.pattern == None:
            self.pattern = self.service.makeNew()"""
        yPos = self.createWidgets(["Name: "], {"name": QtWidgets.QLineEdit(self.upperWidget)},
                                  20, 150, [self.pattern.getName()])
        self.widgets['name'].setToolTip('First Letter must be uppercase, all other letters must be lowercase')
        self.table = self.createTableWidget(self.centralwidget, self.pattern.getItems(), yPos + 50,
                                            self.service.getHeaders(), self.service.getBoolVals())
        #self.formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.table)   #ToDo
        self.verticalLayout.addWidget(self.table)
        self.mainWindow.show()

    def save(self, *args):
        id = self.pattern.getId()
        if args and args[0]:
            id = args[0]
        self.service.savePattern(Element(self.widgets["name"].text(), self.readTable(self.table), id))

    """def saveNew(self):
        self.service.savePattern(Element(self.widgets["name"].text(), self.readTable(self.table), None))"""


class SequenceEditorController(AbstractSimpleEditorController):
    def __init__(self):
        service = SequenceService()
        super(SequenceEditorController, self).__init__(service, service.getSequences(), "Edit Sequences",
                                       {"Save": self.save, "Close": self.close})
        if len(self.pattern)<5:
            [self.pattern.append(self.service.makeNew()) for i in range(6- len(self.pattern))]
        self.table = self.createTableWidget(self.centralwidget, self.pattern, 20,
                                            self.service.getHeaders(), self.service.getBoolVals())
        self.verticalLayout.addWidget(self.table)
        #self.formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.table)   #ToDo
        self.mainWindow.show()

    def save(self):
        sequences = []
        for sequTuple in self.readTable(self.table):
            sequences.append(Sequence(sequTuple[0], sequTuple[1], sequTuple[2], None))
        self.service.save(sequences)


class FragmentEditorController(AbstractEditorControllerWithTabs):
    def __init__(self):
        super(FragmentEditorController, self).__init__(FragmentIonService(), "Edit Fragments", "Fragment-Pattern")
        yPos = self.createWidgets(["Name: "], {"name": QtWidgets.QLineEdit(self.upperWidget)}, 20, 150,
                                  [self.pattern.getName()])
        self.tabWidget = self.makeTabWidget(yPos, "Fragments", "Precursor-Fragments")
        self.mainWindow.show()

    """def openAgain(self, *args):
        super(FragmentEditorController, self).openAgain()"""

    def save(self, *args):
        id = self.pattern.getId()
        if args and args[0]:
            id = args[0]
        self.service.savePattern(FragmentationPattern(self.widgets["name"].text(), self.readTable(self.table1),
                                                      self.readTable(self.table2), id))



class ModificationEditorController(AbstractEditorControllerWithTabs):
    def __init__(self):
        super(ModificationEditorController, self).__init__(ModificationService(), "Edit Modifications",
                                                           "Modification-Pattern")
        yPos = self.createWidgets(["Name: ", "Modification: "],
                                  {"name": QtWidgets.QLineEdit(self.upperWidget),
                                   "modification": QtWidgets.QLineEdit(self.upperWidget)},
                                  20, 150, [self.pattern.getName(), self.pattern.getModification()])
        self.tabWidget = self.makeTabWidget(yPos, "Modifications", "Excluded Modifications")
        self.tab1.setToolTip("For every fragment, the corresponding modified fragment will be included")
        self.tab2.setToolTip("These modifications will be excluded from ion search")
        self.table2.setColumnWidth(0,200)
        self.mainWindow.show()

    def openAgain(self, *args):
        super(ModificationEditorController, self).openAgain()
        self.widgets["modification"].setText(self.pattern.getModification())

    def save(self, *args):
        id = self.pattern.getId()
        if args and args[0]:
            id = args[0]
        self.service.savePattern(ModificationPattern(self.widgets["name"].text(), self.widgets["modification"].text(),
                                     self.readTable(self.table1),self.readTable(self.table2), id))


class IntactIonEditorController(AbstractEditorController):
    def __init__(self):
        super(IntactIonEditorController, self).__init__(IntactIonService(),
                                                        "Edit Intact Ions", "Modification")
        yPos = self.createWidgets(["Name: ", "Initial Gain", "Initial Loss"],
                                  {"name": QtWidgets.QLineEdit(self.upperWidget),
                                   "gain": QtWidgets.QLineEdit(self.upperWidget),
                                   "loss": QtWidgets.QLineEdit(self.upperWidget)}, 20, 150,
                                  [self.pattern.getName(), self.pattern.getInitGain(), self.pattern.getInitLoss()])
        self.widgets['gain'].setToolTip("This formula will be added to all fragments (e.g. H2O for proteins / "
                                                "H for RNA")
        self.widgets['loss'].setToolTip("This formula will be subtracted from all fragments (e.g. PO2 for RNA")
        self.table = self.createTableWidget(self.centralwidget, self.pattern.getItems(), yPos, self.service.getHeaders(),
                                            self.service.getBoolVals())
        self.verticalLayout.addWidget(self.table)
        #self.formLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.table)   #ToDo
        self.mainWindow.show()

    def save(self, *args):
        id = self.pattern.getId()
        if args and args[0]:
            id = args[0]
        self.service.savePattern(IntactPattern(self.widgets["name"].text(), self.widgets["gain"].text(),
                      self.widgets["loss"].text(), self.readTable(self.table), id))






d = {"Name":["+Na","K", "+CMCT", "+CMCT+Na", "+CMCT+K", "+2CMCT"],
     "Gain":["H", "H", "", "H", "H", ""],
     "Loss":["Na", "K", "C14H25N3O", "C14H25N3ONa", "C14H25N3OK", "C14H25N3OC14H25N3O"],
     "NrOfMod":["0", "0", "1", "1", "1", "2"],
     "enabled": [0,True,True,True,True,False]}

if __name__ == '__main__':
    #esi = IntactRepository()
    #esi.makeTables()
    app = QtWidgets.QApplication(sys.argv)
    ionEditor = IntactIonEditorController()
    #editor = ModificationEditorController()
    #ionEditor.setUpIntactMod()
    #w = QMainWindow()
    #IntactIonEditorController().setUpUi(w, "Edit Intact Ions",
                               #{"New Modification", "Open Modification", "Close without Saving", "Save and Close"},
                               #{"New Row", "Copy Row", "Delete Row", "Delete Modification"},
                                #     d,"CMCT")
    #w.show()
    sys.exit(app.exec_())