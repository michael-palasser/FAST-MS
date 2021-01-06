from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout, \
    QDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
import sys

from src.FragmentAndModifService import IntactIonService, IntactPattern, ESI_Repository


class IonEditorFactory(object):
    def __init__(self, service):
        self.service = service

    def setUpIntactMod(self):
        """openDialog = OpenDialog(self.repository.getAllPatterns(), "Open Intact Modification")

        if openDialog.exec_() and openDialog.accepted:

            if openDialog.comboBox.currentText() != "--New--":
                pattern = self.repository.getModPattern(openDialog.comboBox.currentText())
            else:
                pattern =  IntactPattern("", ):"""
        w = QMainWindow()
        self.setUpUi(w, "Edit Intact Ions",
                     {"New Modification": self.createModification,
                      "Open Modification": self.openModification,
                      "Delete Modification": self.deleteModification,
                      "Save As": self.saveNew, "Save": self.save, "Close": self.close},
                     {"New Row": self.insertRow, "Copy Row":self.copyRow},
                     self.service.makeNew())
        w.show()

    def setUpUi(self, MainWindow, title, fileOptions, editOptions, pattern):
        """

        :param pattern: dict
        """
        #super(IntactFragmentView, self).__init__()
        """MainWindow.setObjectName("Edit Intact Ions")"""
        self.pattern = pattern
        self._translate = QtCore.QCoreApplication.translate

        self.mainWindow = MainWindow
        self.mainWindow.setObjectName(title)
        MainWindow.setWindowTitle(self._translate(self.mainWindow.objectName(), title))
        #self.mainWindow.resize(460, 370)

        self.centralwidget = QtWidgets.QWidget(self.mainWindow)
        self.mainWindow.setCentralWidget(self.centralwidget)
        self.formLayout = QtWidgets.QFormLayout(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.mainWindow.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.fileMenu, self.fileMenuActions = self.createMenu("File", fileOptions, 3)
        self.editMenu, self.editMenuActions = self.createMenu("Edit", editOptions, 1)
        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.editMenu.menuAction())

        """self.saveButton = QtWidgets.QPushButton(self.centralwidget)
        self.saveButton.setGeometry(QtCore.QRect(350, 10, 80, 32))
        self.saveButton.setText(self._translate("MainWindow", "Save"))"""

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 20, 50, 16))
        self.label.setText(self._translate(self.mainWindow.objectName(), "Name:"))
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)

        self.nameEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.nameEdit.setGeometry(QtCore.QRect(90, 20, 150, 21))
        self.nameEdit.setText(pattern.getName())
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.nameEdit)

        self.table = self.createTableWidget(QtWidgets.QTableWidget(self.centralwidget), pattern.getItems())
        MainWindow.setStatusBar(QtWidgets.QStatusBar(MainWindow))


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


    def createTableWidget(self,tableWidget, data):
        #tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        #tableWidget.setGeometry(QtCore.QRect(20, 70, 420, 200))
        headers = self.service.getHeaders()
        print(headers)
        tableWidget.setColumnCount(len(headers))
        tableWidget.setRowCount(len(data))
        tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        tableWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        tableWidget.move(20,70)
        tableWidget.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(data):
            for j, item in enumerate(row):
                print(i,j, item)
                if headers[j] == 'Enabled':
                    print("enabled", item)
                    newitem = QTableWidgetItem(item)
                    if item == 1:
                        print("enabled",1)
                        newitem.setCheckState(QtCore.Qt.Checked)
                    elif item == 0:
                        print("enabled",0)
                        newitem.setCheckState(QtCore.Qt.Unchecked)
                    tableWidget.setItem(i, j, newitem)
                else:
                    newitem = QTableWidgetItem(str(item))
                    tableWidget.setItem(i, j, newitem)
                print("now",i,j,newitem.text())
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
                self.pattern = self.service.getPattern(openDialog.comboBox.currentText())
            else:
                self.pattern = self.service.makeNew()
            self.nameEdit.setText(self.pattern.getName())
            self.table = self.createTableWidget(self.table, self.pattern.getItems())



    def deleteModification(self):
        #ToDo: Dialog mit Boxen
        pass

    def save(self):
        self.service.savePattern(IntactPattern(self.nameEdit.text(),self.readTable(self.table), self.pattern.getId() ))


    def readTable(self, table):
        itemList = []
        headers = self.service.getHeaders()
        for row in range(table.rowCount()):
            print("hey",table.item(row,0).text(),table.item(row,1).text())
            if table.item(row,0).text() == "":
                continue
            rowData = []
            for col in range(table.columnCount()):
                widgetItem = table.item(row, col)
                #if widgetItem and widgetItem.text():
                print(row, col, type(widgetItem))
                if widgetItem and widgetItem.text():
                    #ToDo
                    rowData.append(widgetItem.text())
                elif headers[col] == 'Enabled':
                    rowData.append(widgetItem.checkState())
                else:
                    rowData.append("")
            itemList.append(rowData)
        return itemList



    def saveNew(self):
        self.service.savePattern(IntactPattern(self.nameEdit.text(),self.readTable(self.table), None ))


    def close(self):
        self.service.close()
        self.mainWindow.close()

    def insertRow(self):
        self.table.insertRow(self.table.rowCount())
        newitem = QTableWidgetItem(0)
        newitem.setCheckState(QtCore.Qt.Checked)
        self.table.setItem(self.table.rowCount()-1, self.table.columnCount()-1, newitem)

    def copyRow(self):
        rowCount = self.table.rowCount()
        columnCount = self.table.columnCount()
        rowSelecter = RowSelecter(rowCount, "Copy Row")
        if rowSelecter.exec_() and rowSelecter.accepted:
            self.table.insertRow(self.table.rowCount())
            copiedRow = rowSelecter.spinBox.value() - 1
            for j in range(columnCount):
                if not self.table.item(copiedRow, j) is None:
                    self.table.setItem(rowCount, j, QTableWidgetItem(self.table.item(copiedRow, j).text()))
            self.table.item(rowCount, columnCount-1).setCheckState(QtCore.Qt.Checked)


class RowSelecter(QDialog):
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
        self.label.setText(_translate("dialog", "Enter Row Index:"))


class OpenDialog(QDialog):
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
    app = QApplication(sys.argv)
    ionEditor = IonEditorFactory(IntactIonService())
    ionEditor.setUpIntactMod()
    #w = QMainWindow()
    #IonEditorFactory().setUpUi(w, "Edit Intact Ions",
                               #{"New Modification", "Open Modification", "Close without Saving", "Save and Close"},
                               #{"New Row", "Copy Row", "Delete Row", "Delete Modification"},
                                #     d,"CMCT")
    #w.show()
    sys.exit(app.exec_())