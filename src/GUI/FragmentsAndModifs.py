from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout, \
    QDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
import sys

data = {'col1': ['1', '2', '3', '4'],
        'col2': ['1', '2', '1', '3'],
        'col3': ['1', '1', '2', '1']}


class TableView(QTableWidget):
    def __init__(self, data, *args):
        """

        :param data: dict: {header:[col-items]}
        :param args: rows, cols
        """
        QTableWidget.__init__(self, *args)
        self.data = data
        self.setData()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def setData(self):
        headers = []
        for n, key in enumerate(sorted(self.fragments.keys())):
            headers.append(key)
            for m, item in enumerate(self.fragments[key]):
                newitem = QTableWidgetItem(item)
                self.setItem(m, n, newitem)
        self.setHorizontalHeaderLabels(headers)


class IonEditorFactory(object):
    """def __init__(self):
        pass"""

    def setUpIntactMod(self, data, modificationName):
        w = QMainWindow()
        self.setUpUi(w, "Edit Intact Ions",
                     {"New Modification": self.createModification,
                      "Open Modification": self.openModification,
                      "Delete Modification": self.deleteModification,
                      "Save": self.save, "Close": self.close},
                     {"New Row": self.insertRow, "Copy Row":self.copyRow},
                     data, modificationName)
        w.show()

    def setUpUi(self, MainWindow, title, fileOptions, editOptions, data, modificationName):
        """

        :param data: dict
        """
        #super(IntactFragmentView, self).__init__()
        """MainWindow.setObjectName("Edit Intact Ions")"""
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
        self.fileMenu, self.fileMenuActions = self.createMenu("File", fileOptions, 2)
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
        self.nameEdit.setText(modificationName)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.nameEdit)

        self.table = self.createTableWidget(data)
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


    def createTableWidget(self, data):
        tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        #tableWidget.setGeometry(QtCore.QRect(20, 70, 420, 200))
        tableWidget.setColumnCount(len(data.keys()))
        tableWidget.setRowCount([len(val) for val in data.values()][0])
        tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        tableWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        tableWidget.move(20,70)
        headers = []
        for n, key in enumerate(data.keys()):
            headers.append(key)
            for m, item in enumerate(data[key]):
                newitem = QTableWidgetItem(item)
                if item == True:
                    newitem.setCheckState(QtCore.Qt.Checked)
                if item == False:
                    newitem.setCheckState(QtCore.Qt.Unchecked)
                tableWidget.setItem(m, n, newitem)
        tableWidget.setHorizontalHeaderLabels(headers)
        tableWidget.resizeColumnsToContents()
        tableWidget.resizeRowsToContents()
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, tableWidget)
        return tableWidget

    def createModification(self):
        pass

    def openModification(self):
        pass

    def deleteModification(self):
        pass

    def save(self):
        pass

    def close(self):
        self.mainWindow.close()


    def insertRow(self):
        self.table.insertRow(self.table.rowCount())

    def copyRow(self):
        rowCount = self.table.rowCount()
        columnCount = self.table.columnCount()
        rowSelecter = RowSelecter(rowCount)
        if rowSelecter.exec_() and rowSelecter.accepted:
            self.table.insertRow(self.table.rowCount())
            copiedRow = rowSelecter.spinBox.value() - 1
            for j in range(columnCount):
                if not self.table.item(copiedRow, j) is None:
                    self.table.setItem(rowCount, j, QTableWidgetItem(self.table.item(copiedRow, j).text()))
            self.table.item(rowCount, columnCount-1).setCheckState(QtCore.Qt.Checked)


class RowSelecter(QDialog):
    def __init__(self, max):
        super(RowSelecter, self).__init__()
        self.value = None
        self.setObjectName("dialog")
        self.resize(208, 100)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(25, 60, 164, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox_2")
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(20, 20, 121, 16))
        self.spinBox = QtWidgets.QSpinBox(self)
        self.spinBox.setGeometry(QtCore.QRect(140, 18, 48, 24))
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(max)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.show()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("dialog", "Copy Row"))
        self.label.setText(_translate("dialog", "Enter Row Index:"))

    """def accept(self):
        self.value = self.spinBox.value()
        self.close()

    def reject(self):
        self.close()
"""








d = {"Name":["+Na","K", "+CMCT", "+CMCT+Na", "+CMCT+K", "+2CMCT"],
     "Gain":["H", "H", "", "H", "H", ""],
     "Loss":["Na", "K", "C14H25N3O", "C14H25N3ONa", "C14H25N3OK", "C14H25N3OC14H25N3O"],
     "NrOfMod":["0", "0", "1", "1", "1", "2"],
     "enabled": [0,True,True,True,True,False]}

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ionEditor = IonEditorFactory()
    ionEditor.setUpIntactMod(d, "CMCT")
    #w = QMainWindow()
    #IonEditorFactory().setUpUi(w, "Edit Intact Ions",
                               #{"New Modification", "Open Modification", "Close without Saving", "Save and Close"},
                               #{"New Row", "Copy Row", "Delete Row", "Delete Modification"},
                                #     d,"CMCT")
    #w.show()
    sys.exit(app.exec_())