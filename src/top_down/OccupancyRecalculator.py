import subprocess
import sys

import numpy as np
import os
import re
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from src.Services import SequenceService
from src.entities.Ions import Fragment,FragmentIon
from src.top_down.Analyser import Analyser
from src.top_down.ExcelWriter import BasicExcelWriter
from src import path

def run(mainWindow):
    """open everything"""

    service = SequenceService()
    dlg = SimpleStartDialog(mainWindow, service.getAllSequenceNames())
    dlg.exec_()
    if dlg and dlg.sequence != None:
        sequenceName = dlg.sequence
        sequence = service.get(dlg.sequence).getSequenceList()
        modification = dlg.modification

        """import ion-list"""
        spectralFile = path + 'Spectral_data/Occupancies_in.csv'
        with open(spectralFile, 'w') as f:
            f.write("m/z,z,int,name")
        subprocess.call(['open',spectralFile])
        start = QtWidgets.QMessageBox.question(mainWindow, 'Calculating Occupancies ',
            'Paste the ions (format: m/z, z, Int., fragment-name) in the csv-file and press "Ok"',
                                                        QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if start == QtWidgets.QMessageBox.Ok:
            try:
                arr = np.loadtxt(spectralFile, delimiter=',', skiprows=1,
                                 dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')])
            except ValueError:
                arr = np.loadtxt(spectralFile, delimiter='\t', skiprows=1,
                                 dtype=[('m/z', np.float64), ('z', np.uint8), ('intensity', np.float64), ('name', 'U32')])
            ionList = list()
            speciesList = list()
            for ion in arr:
                species = re.findall(r"([a-z]+)", ion['name'])[0]
                if (species not in speciesList) and (species!=sequenceName):
                    speciesList.append(species)
                number = int(re.findall(r"([0-9]+)", ion['name'])[0])
                if ion['name'].find('+') != -1:
                    modif = ion['name'][ion['name'].find('+'):]
                else:
                    modif = ""
                newIon = FragmentIon(Fragment(species, number, modif, dict(), [], 0), ion['z'], np.zeros(1), 0)
                newIon.intensity = ion['intensity']
                ionList.append(newIon)

            """Analysis and Output"""
            analyser = Analyser(ionList, sequence, 1, modification)
            excelWriter = BasicExcelWriter(os.path.join(path, "Spectral_data","Occupancies_out.xlsx"))
            date = datetime.now().strftime("%d/%m/%Y %H:%M")
            excelWriter.worksheet1.write(0,0,date)
            row = excelWriter.writeAbundancesOfSpecies(2, analyser.calculateRelAbundanceOfSpecies())
            excelWriter.writeOccupancies(row,sequence,analyser.calculatePercentages(speciesList))
            excelWriter.closeWorkbook()
            try:
                subprocess.call(['open', os.path.join(path, "Spectral_data","Occupancies_out.xlsx")])
            except:
                pass
        else:
            return
    else:
        return



class SimpleStartDialog(QtWidgets.QDialog):
    def __init__(self, parent, sequences):
        super().__init__(parent)
        self.setObjectName('dialog')
        self.widgets = dict()
        self.lineSpacing = 35
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), "Calculate Occupancies"))
        xPos = self.createLabels(("Sequence Name: ", "Modification: "))
        widgets =((self.createComboBox(sequences), "sequName", "Name of the sequence"),
                 (QtWidgets.QLineEdit(self),  "modification",
                        "Name of the modification/ligand you want to search for.\n" "If you want to search for a "
                        "special number of modifications, enter the number as a prefix without any spaces"))
        self.sequence = None
        self.modification = None
        xPos, yPos = self.createWidgets(widgets,xPos,150)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.move(int(xPos/3),yPos)
        self.move(300,100)
        self.resize(xPos+25, yPos+50)
        self.show()

    def createComboBox(self, options):
        comboBox = QtWidgets.QComboBox(self)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), option))
        return comboBox

    def createLabels(self, labelNames):
        yPos = 30
        width = 0
        for label in labelNames:
            length = len(label)*10
            if length > width:
                width = length
        for labelname in labelNames:
            label = QtWidgets.QLabel(self)
            label.setGeometry(QtCore.QRect(20,yPos,width,16))
            label.setText(self._translate(self.objectName(), labelname))
            yPos += self.lineSpacing
        return width+20


    def createWidgets(self, widgetTuples, xPos, lineWidth):
        """

        :param widgetTuples: (widget,name,toolTip)
        :param xPos:
        :param lineWidth:
        :return:
        """
        yPos = 30
        for widgetTuple in widgetTuples:
            widget = widgetTuple[0]
            """if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.setGeometry(QtCore.QRect(xPos, yPos-1, lineWidth, 24))"""
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setGeometry(QtCore.QRect(xPos, yPos, lineWidth, 21))
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.setGeometry(QtCore.QRect(xPos - 3, yPos, lineWidth + 6, 26))
            else:
                raise Exception('Unknown type of widget')
            widget.setObjectName(widgetTuple[1])
            widget.setToolTip(self._translate(self.objectName(), widgetTuple[2]))
            self.widgets[widgetTuple[1]] = widget
            yPos += self.lineSpacing
        return xPos+lineWidth, yPos

    def accept(self):
        self.sequence = self.widgets['sequName'].currentText()
        self.modification = self.widgets['modification'].text()
        super(SimpleStartDialog, self).accept()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    run(None)
    sys.exit(app.exec_())