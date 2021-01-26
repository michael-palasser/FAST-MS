import sys
from abc import ABC

from PyQt5 import QtWidgets, QtCore

from src.views.IonTableWidget import IonTableWidget, TickIonTableWidget

class AbstractIonView(ABC):
    def __init__(self, patterns, title, message, widths):
        self.patterns = patterns
        #self.headers = ('m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.', 'del.?')
        self.widths = widths
        self.setUpUi(title)
        self.tables = []
        label = QtWidgets.QLabel(self.dialog)
        label.setGeometry(QtCore.QRect(20, 20, 400, 16))
        label.setText(self._translate(self.dialog.objectName(), message))
        yPos = 60
        yPos = self.makeTables(yPos)
        width = sum(self.widths)
        yPos = self.makeButtonBox(width, yPos+20)
        self.dialog.resize(width+80, yPos+20)
        self.dumpList = []
        self.dialog.show()
        self.dialog.raise_()

    def makeTables(self, yPos):
        return yPos

    def setUpUi(self, title):
        self.dialog = QtWidgets.QDialog()
        self.dialog.setObjectName("dialog")
        self._translate = QtCore.QCoreApplication.translate
        self.dialog.setWindowTitle(self._translate(self.dialog.objectName(), title))

    def makeButtonBox(self, width, yPos):
        self.buttonBox = QtWidgets.QDialogButtonBox(self.dialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.move(width - self.buttonBox.width() - 50, yPos)
        return yPos + 30

    def accept(self):
        self.dialog.accept()

    def reject(self):
        choice = QtWidgets.QMessageBox.question(self.dialog, 'Closing ',
            "Unsaved Results!\nDo you really want to cancel?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.dialog.reject()


class CheckOverlapView(AbstractIonView):
    def __init__(self, patterns):
        super(CheckOverlapView, self).__init__(patterns, "Check Overlapping Ions",
           "Complex overlapping patterns - Select ions for deletion:", [100, 30, 90, 120, 70, 60, 60,40])

    def makeTables(self, yPos):
        for i, pattern in enumerate(self.patterns):
            table = TickIonTableWidget(self.dialog, pattern, yPos) #self.createTableWidget(self, pattern, yPos)
            for i,width in enumerate(self.widths):
                table.setColumnWidth(i,width)
            #self.formLayout.setWidget(i+1, QtWidgets.QFormLayout.SpanningRole, table)  # ToDo
            self.tables.append(table)
            yPos += len(pattern)*20+50
        return yPos

    def accept(self):
        for table in self.tables:
            self.dumpList += table.getDumpList()
        print(self.dumpList)
        super(CheckOverlapView, self).accept()


class CheckMonoisotopicOverlapView(AbstractIonView):
    def __init__(self, patterns):
        self.comboBoxes = []
        self.optionDict = dict()
        super(CheckMonoisotopicOverlapView, self).__init__(patterns, "Check Heavily Overlapping Ions",
           "These ions have the same mass - select the ion you want to keep", [100, 30, 90, 120, 70, 60, 60])

    def makeTables(self, yPos):
        for i, pattern in enumerate(self.patterns):
            self.makeComboBox(pattern,yPos)
            table = IonTableWidget(self.dialog, pattern, yPos+40)
            for i,width in enumerate(self.widths):
                table.setColumnWidth(i,width)
            self.tables.append(table)
            yPos += len(pattern)*20+50+50
        return yPos

    def makeComboBox(self, pattern, yPos):
        options = []
        for row in pattern:
            key = row[3]+",    " + str(row[1])
            options.append(key)
            self.optionDict[key] = self.hashRow(row)
        comboBox = QtWidgets.QComboBox(self.dialog)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.dialog.objectName(), option))
        comboBox.setGeometry(QtCore.QRect(30, yPos, 180, 26))
        comboBox.setToolTip("Select the ion which you want to keep, the others will be deleted")
        self.comboBoxes.append(comboBox)

    def hashRow(self, row):
        return (row[3],row[1])

    def accept(self):
        ionsToKeep = []
        for box in self.comboBoxes:
            ionsToKeep.append(self.optionDict[box.currentText()])
        for pattern in self.patterns:
            for row in pattern:
                if self.hashRow(row) not in ionsToKeep:
                    self.dumpList.append(self.hashRow(row))
        print(self.dumpList)
        super(CheckMonoisotopicOverlapView, self).accept()
