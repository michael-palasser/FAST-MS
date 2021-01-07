from functools import partial

from PyQt5 import QtWidgets, QtCore
import sys

from src.FragmentAndModifService import IntactIonService, IntactPattern


class IntactIonEditorController(object):
    def __init__(self):
        self.service = IntactIonService()
        self.pattern = self.service.makeNew()
        self.setUpUi("Edit Intact Ions", )
        self.setUpMenuBar({"New Modification": self.createModification,
                      "Open Modification": self.openModification,
                      "Delete Modification": self.deleteModification,
                      "Save": self.save, "Save As": self.saveNew, "Close": self.close},
                          {"New Row": self.insertRow}) #"Copy Row":self.copyRow
        yPos = self.createNames(["Name:"], {"name":QtWidgets.QLineEdit(self.centralwidget)}, 20, 150,
                                [self.pattern.getName()])
        self.table = self.createTableWidget(yPos+50)
        self.mainWindow.show()


    def setUpUi(self, title):
        self.mainWindow = QtWidgets.QMainWindow()
        self.mainWindow.setObjectName(title)
        self._translate = QtCore.QCoreApplication.translate
        self.mainWindow.setWindowTitle(self._translate(self.mainWindow.objectName(), title))
        self.centralwidget = QtWidgets.QWidget(self.mainWindow)
        self.mainWindow.setCentralWidget(self.centralwidget)
        self.formLayout = QtWidgets.QFormLayout(self.centralwidget)
        self.mainWindow.setStatusBar(QtWidgets.QStatusBar(self.mainWindow))


    def setUpMenuBar(self, fileOptions, editOptions):
        self.menubar = QtWidgets.QMenuBar(self.mainWindow)
        self.mainWindow.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.fileMenu, self.fileMenuActions = self.createMenu("File", fileOptions, 3)
        self.editMenu, self.editMenuActions = self.createMenu("Edit", editOptions, 1)
        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.editMenu.menuAction())

        """self.saveButton = QtWidgets.QPushButton(self.centralwidget)
        self.saveButton.setGeometry(QtCore.QRect(350, 10, 80, 32))
        self.saveButton.setText(self._translate("MainWindow", "Save"))"""


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
            action.triggered.connect(function)
            menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        return menu, menuActions

    def createNames(self, labels, widgets, initYPos, widgetWith, initialValues):
        """

        :param labels: list of Strings
        :param widgets: dict of {name:widget}
        :return:
        """
        maxWidth = 0
        yPos = initYPos
        for labelName in labels:
            label = QtWidgets.QLabel(self.centralwidget)
            width = len(labelName)*10
            label.setGeometry(QtCore.QRect(20, yPos, width, 16))
            label.setText(self._translate(self.mainWindow.objectName(), labelName))
            self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, label)
            if width>maxWidth:
                maxWidth = width
            yPos += 30
        yPos = initYPos
        self.widgets = dict()
        for widgetName, widget in widgets.items():
            #widget = QtWidgets.QLineEdit(self.centralwidget)
            widget.setGeometry(QtCore.QRect(maxWidth+20, yPos, widgetWith, 21))
            self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, widget)
            self.widgets[widgetName] = widget
            yPos += 30
        for widget, initVal in zip(self.widgets.values(),initialValues):
            widget.setText(initVal) #self.pattern.getName()
        return yPos

    def createTableWidget(self, yPos):
        tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        headers = self.service.getHeaders()
        tableWidget.setColumnCount(len(headers))
        #tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #tableWidget.customContextMenuRequested['QPoint'].connect(self.h3_table_right_click)
        #tableWidget.move(20,yPos) #70
        tableWidget = self.formatTableWidget(headers, tableWidget, self.pattern.getItems())
        tableWidget.setHorizontalHeaderLabels(headers)
        tableWidget.resizeColumnsToContents()
        tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tableWidget.customContextMenuRequested['QPoint'].connect(partial(self.editRow, tableWidget))
        return tableWidget

    def formatTableWidget(self, headers, tableWidget, data):
        #tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        #tableWidget.setGeometry(QtCore.QRect(20, 70, 420, 200))
        #headers = self.service.getHeaders()
        tableWidget.setRowCount(len(data))
        tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        tableWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        for i, row in enumerate(data):
            for j, item in enumerate(row):
                if headers[j] == 'Enabled':
                    newitem = QtWidgets.QTableWidgetItem(item)
                    if item == 1:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    elif item == 0:
                        newitem.setCheckState(QtCore.Qt.Unchecked)
                    tableWidget.setItem(i, j, newitem)
                else:
                    newitem = QtWidgets.QTableWidgetItem(str(item))
                    tableWidget.setItem(i, j, newitem)
                #tableWidget.setItem(i, j, newitem)
        tableWidget.resizeColumnsToContents()
        tableWidget.resizeRowsToContents()
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, tableWidget)
        return tableWidget

    def createModification(self):
        self.openModification("Choose a Template")

    def openModification(self, *args):
        title = "Open Intact Modification"
        if args != (False,):
            title = args[0]
        openDialog = OpenDialog(self.service.getAllPatternNames(), title)
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            if openDialog.comboBox.currentText() != "--New--":
                print("open",openDialog.comboBox.currentText())
                self.pattern = self.service.getPattern(openDialog.comboBox.currentText())
            else:
                self.pattern = self.service.makeNew()
            self.widgets["name"].setText(self.pattern.getName())
            self.table = self.formatTableWidget(self.service.getHeaders(), self.table, self.pattern.getItems())



    def deleteModification(self):
        """title = "Delete Intact Modification"
        if args != (False,):
            title = args[0]"""
        openDialog = OpenDialog(self.service.getAllPatternNames(), "Delete Intact Modification")
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            if openDialog.comboBox.currentText() != "--New--":
                print("deleting",openDialog.comboBox.currentText())
                self.pattern = self.service.delete(openDialog.comboBox.currentText())
            else:
                return

    def save(self):
        self.service.savePattern(IntactPattern(self.widgets["name"].text(),self.readTable(self.table), self.pattern.getId() ))


    def readTable(self, table):
        itemList = []
        headers = self.service.getHeaders()
        for row in range(table.rowCount()):
            if table.item(row,0).text() == "":
                continue
            rowData = []
            for col in range(table.columnCount()):
                widgetItem = table.item(row, col)
                #if widgetItem and widgetItem.text():
                if headers[col] == 'Enabled':
                    rowData.append(int(widgetItem.checkState()/2))
                elif widgetItem and widgetItem.text():
                    #ToDo
                    rowData.append(widgetItem.text())
                #elif headers[col] == 'Enabled':
                    #rowData.append(widgetItem.checkState())
                else:
                    rowData.append("")
            itemList.append(rowData)
        return itemList



    def saveNew(self):
        self.service.savePattern(IntactPattern(self.widgets["name"].text(),self.readTable(self.table), None ))


    def close(self):
        self.service.close()
        self.mainWindow.close()

    def insertRow(self):
        self.table.insertRow(self.table.rowCount())
        newitem = QtWidgets.QTableWidgetItem(0)
        newitem.setCheckState(QtCore.Qt.Checked)
        self.table.setItem(self.table.rowCount()-1, self.table.columnCount()-1, newitem)

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

    def editRow(self, table, pos):
        it = table.itemAt(pos)
        if it is None:
            return
        selectedRowIndex = it.row()
        columnCount = table.columnCount()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, selectedRowIndex, columnCount - 1, selectedRowIndex)
        table.setRangeSelected(item_range, True)
        menu = QtWidgets.QMenu()
        deleteColumnAction = menu.addAction("Delete row")
        copyColumnAction = menu.addAction("Copy and insert row")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == deleteColumnAction:
            table.removeRow(selectedRowIndex)
        elif action == copyColumnAction:
            rowCount = table.rowCount()
            table.insertRow(rowCount)
            for j in range(columnCount):
                if not table.item(selectedRowIndex, j) is None:
                    table.setItem(rowCount, j, QtWidgets.QTableWidgetItem(table.item(selectedRowIndex, j).text()))
            table.item(rowCount, columnCount-1).setCheckState(QtCore.Qt.Checked)



"""class RowSelecter(QDialog):
    def __init__(self, max, title):
        super(RowSelecter, self).__init__()
        self.setObjectName("dialog")
        self.resize(208, 100)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(25, 60, 164, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(20, 20, 121, 16))
        self.spinBox = QtWidgets.QSpinBox(self)
        self.spinBox.setGeometry(QtCore.QRect(140, 18, 48, 24))
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(max)

        self.retranslateUi(title)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.show()

    def retranslateUi(self, title):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("dialog", title))
        self.label.setText(_translate("dialog", "Enter Row Index:"))"""


class OpenDialog(QtWidgets.QDialog):
    def __init__(self, names, title):
        super(OpenDialog, self).__init__()
        self._translate = QtCore.QCoreApplication.translate
        self.setObjectName("dialog")
        self.resize(300, 110)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(68, 70, 164, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox_2")
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(20, 20, 121, 16))
        self.comboBox = QtWidgets.QComboBox(self)
        self.comboBox.setGeometry(QtCore.QRect(120, 17, 160, 26))
        self.comboBox.addItem("")
        self.comboBox.setItemText(0, self._translate(self.objectName(), "--New--"))
        for i,name in enumerate(names):
            self.comboBox.addItem("")
            self.comboBox.setItemText(i+1, self._translate(self.objectName(), name))

        self.retranslateUi(title)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.show()

    def retranslateUi(self,title):
        self.setWindowTitle(self._translate("dialog", title))
        self.label.setText(self._translate("dialog", "Enter Name:"))




d = {"Name":["+Na","K", "+CMCT", "+CMCT+Na", "+CMCT+K", "+2CMCT"],
     "Gain":["H", "H", "", "H", "H", ""],
     "Loss":["Na", "K", "C14H25N3O", "C14H25N3ONa", "C14H25N3OK", "C14H25N3OC14H25N3O"],
     "NrOfMod":["0", "0", "1", "1", "1", "2"],
     "enabled": [0,True,True,True,True,False]}

if __name__ == '__main__':
    #esi = ESI_Repository()
    #esi.makeTables()
    app = QtWidgets.QApplication(sys.argv)
    ionEditor = IntactIonEditorController()
    #ionEditor.setUpIntactMod()
    #w = QMainWindow()
    #IntactIonEditorController().setUpUi(w, "Edit Intact Ions",
                               #{"New Modification", "Open Modification", "Close without Saving", "Save and Close"},
                               #{"New Row", "Copy Row", "Delete Row", "Delete Modification"},
                                #     d,"CMCT")
    #w.show()
    sys.exit(app.exec_())