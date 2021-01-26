import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow

from src.views.IonTableWidget import IonTableWidget, TickIonTableWidget


class CheckOverlapView(QtWidgets.QDialog):
    def __init__(self, patterns):
        super(CheckOverlapView, self).__init__()
        self.patterns = patterns
        #self.headers = ('m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.', 'del.?')
        self.widths = [100, 30, 90, 120, 70, 60, 60,40]
        self.setUpUi()
        self.tables = []
        label = QtWidgets.QLabel(self)
        label.setGeometry(QtCore.QRect(20, 20, 400, 16))
        label.setText(self._translate(self.dialog.objectName(), "Complex overlapping patterns: Select ions for deletion:"))
        yPos = 50
        for i, pattern in enumerate(patterns):
            table = TickIonTableWidget(self, pattern, yPos) #self.createTableWidget(self, pattern, yPos)
            for i,width in enumerate(self.widths):
                table.setColumnWidth(i,width)
            #self.formLayout.setWidget(i+1, QtWidgets.QFormLayout.SpanningRole, table)  # ToDo
            self.tables.append(table)
            yPos += len(pattern)*20+50
        width = sum(self.widths)
        yPos = self.makeButtonBox(width, yPos+20)
        self.resize(width+80, yPos+20)

    def setUpUi(self):
        self.dialog = QtWidgets.QDialog()
        self.dialog.setObjectName("Check Overlaps")
        self._translate = QtCore.QCoreApplication.translate
        self.dialog.setWindowTitle(self._translate(self.dialog.objectName(), "Check Overlaps"))

    def makeButtonBox(self, width, yPos):
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.move(width-self.buttonBox.width()-50, yPos)
        return yPos +30

    def accept(self):
