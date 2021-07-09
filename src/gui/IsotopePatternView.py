from PyQt5 import QtWidgets, QtCore

from src.IsotopePatternLogics import IsotopePatternLogics
from src.Services import *
from src.gui.AbstractMainWindows import SimpleMainWindow
from src.gui.widgets.IonTableWidgets import IsoPatternIon
from src.gui.widgets.PeakWidgets import IsoPatternPeakWidget
from src.gui.dialogs.SimpleDialogs import OpenDialog
from src.gui.widgets.SpectrumView import TheoSpectrumView


class IsotopePatternView(SimpleMainWindow):
    '''
    Main window for Isotope Pattern Tool
    '''
    def __init__(self, parent):
        super(IsotopePatternView, self).__init__(parent, 'Isotope Pattern Tool')
        self._controller = IsotopePatternLogics()
        self._fragmentationOpts = self._controller.getFragmentationNames()
        self._modifPatternOpts = self._controller.getModifPatternNames()
        self._intensity = None
        self._vertLayout = QtWidgets.QVBoxLayout(self._centralwidget)
        self._upperW =QtWidgets.QWidget(self._centralwidget)

        self._inputForm = QtWidgets.QLineEdit(self._upperW)
        self._inputForm.setGeometry(QtCore.QRect(15, 20, 185, 21))
        self._inputForm.returnPressed.connect(self.calculateIsotopePattern)

        modeLabel = QtWidgets.QLabel(self._upperW)
        modeLabel.setGeometry(QtCore.QRect(250, 20, 60, 16))
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        self._modeBox = QtWidgets.QComboBox(self._upperW)
        self._modeBox.setGeometry(QtCore.QRect(290, 17, 120, 26))
        self.updateComboBox(self._modeBox, self._controller.getMolecules())

        chargeLabel = QtWidgets.QLabel(self._upperW)
        chargeLabel.setGeometry(QtCore.QRect(15, 60, 60, 16))
        chargeLabel.setText(self._translate(self.objectName(), "Charge:"))
        self._charge = QtWidgets.QSpinBox(self._upperW)
        self._charge.setGeometry(QtCore.QRect(70, 57, 50, 24))
        self._charge.setMinimum(-99)
        self._charge.valueChanged.connect(self.calculateIsotopePattern)
        radicalLabel = QtWidgets.QLabel(self._upperW)
        radicalLabel.setGeometry(QtCore.QRect(130, 60, 60, 16))
        radicalLabel.setText(self._translate(self.objectName(), "Electrons:"))
        self._radicals = QtWidgets.QSpinBox(self._upperW)
        self._radicals.setGeometry(QtCore.QRect(190, 57, 40, 24))
        self._radicals.setMinimum(-9)
        self._radicals.setMaximum(9)
        self._radicals.valueChanged.connect(self.calculateIsotopePattern)

        self._pushCalc = self.makeBtn(60, 100, "Calculate")
        self._pushCalc.clicked.connect(self.calculateIsotopePattern)
        self._pushModel = self.makeBtn(140, 100, "Model")
        self._pushModel.clicked.connect(self.modelInt)
        self.makeOptions()

        self._spectrumView = QtWidgets.QFrame(self._upperW)

        self._spectrumView.setGeometry(QtCore.QRect(250, 50, 350, 280))
        self._spectrumView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._spectrumView.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self._spectrumView.setStyleSheet('background-color: white')
        self._vertLayout.addWidget(self._upperW)
        self._vertLayout.addSpacing(10)
        self.makeIonTable(None, None, None)
        #self._vertLayout.addWidget(self._ionTable)
        self._spaceItem = QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Expanding)
        self._vertLayout.addItem(self._spaceItem)
        # self.ionTable.setGeometry(QtCore.QRect(20, 335, 550, 50))
        self._peakLabel = QtWidgets.QLabel(self._centralwidget)
        self._peakLabel.setGeometry(QtCore.QRect(25, 415, 60, 16))
        self._peakLabel.setText(self._translate(self.objectName(), "Peaks:"))
        self._vertLayout.addWidget(self._peakLabel)
        self.makePeakTable(((),))

        self._modeBox.currentIndexChanged.connect(self.activateFrame)
        width = 615
        self._upperW.setGeometry(QtCore.QRect(0,0,width,335))
        self._upperW.setMinimumHeight(325)
        self._centralwidget.setLayout(self._vertLayout)
        self.setGeometry(QtCore.QRect(100,50,width, 400))
        self.createMenuBar()
        self.createMenu('File', {'Load Sequence': (self.loadSequence, '', "Ctrl+O"),}, None)
        self.show()

    def makeOptions(self):
        self._frame = QtWidgets.QFrame(self._upperW)
        self._frame.setGeometry(QtCore.QRect(15, 155, 220, 170))
        self._frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frameLabels = ("Fragmentation:", "Fragment:", "Modif.Pattern:", "Modification:", "Nr.of Mod.:")
        self._fragmentationBox = QtWidgets.QComboBox(self._frame)
        self._fragmentBox = QtWidgets.QComboBox(self._frame)
        self._fragmentationBox.currentIndexChanged.connect(self.getFragValues)
        self._modPatternBox = QtWidgets.QComboBox(self._frame)
        self._modPatternBox.currentIndexChanged.connect(self.getModValues)
        self._modifBox = QtWidgets.QComboBox(self._frame)
        self._nrOfMods = QtWidgets.QSpinBox(self._frame)
        self.fillFrame(frameLabels, (self._fragmentationBox, self._fragmentBox,
                                     self._modPatternBox, self._modifBox, self._nrOfMods),
                       ("", "", "", "", ''))
        self._frame.hide()

    def makeBtn(self,xPos, yPos, name):
        btn = QtWidgets.QPushButton(self._upperW)
        btn.setGeometry(QtCore.QRect(xPos-int(81/2), yPos, 81, 32))
        btn.setText(self._translate(self.objectName(), name))
        return btn

    def fillFrame(self, labelNames, widgets, toolTips):
        yPos = 10
        for i, labelName in enumerate(labelNames):
            label = QtWidgets.QLabel(self._frame)
            label.setGeometry(QtCore.QRect(10, yPos, 90, 16))
            label.setText(self._translate(self.objectName(), labelName))
            widgets[i].setGeometry(QtCore.QRect(100, yPos - 4, 120, 26))
            widgets[i].setToolTip(toolTips[i])
            yPos += 30
            if i == 1:
                yPos += 10


    '''def fillFragmentBox(self, box, options1, options2):
        [box.model().item(i).setEnabled(True) for i in range(box.count())]
        self.updateComboBox(box,options1+['']+options2)
        box.model().item(len(options1)).setEnabled(False)'''

    def loadSequence(self):
        service = SequenceService()
        openDialog = OpenDialog('Sequences', service.getAllSequenceNames())
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            sequence = service.get(openDialog.getName())
            self._inputForm.setText(''.join(sequence.getSequenceString()))
            self._modeBox.setCurrentText(sequence.getMolecule())
            #self.activateFrame()


    def activateFrame(self):
        if self._frame.isVisible() and self._modeBox.currentIndex() == 0:
            self._frame.hide()
        elif not self._frame.isVisible() and self._modeBox.currentIndex() != 0:
            self.updateComboBox(self._fragmentationBox, self._fragmentationOpts)
            self.updateComboBox(self._modPatternBox, self._modifPatternOpts)
            self.getFragValues()
            self.getModValues()
            self._frame.show()


    def getFragValues(self):
        if self._fragmentationBox.currentText() != "":
            fragItems, precItems = self._controller.getFragItems(self._fragmentationBox.currentText())
            #self.fillFragmentBox(self._fragmentBox, fragItems, precItems)
            [self._fragmentBox.model().item(i).setEnabled(True) for i in range(self._fragmentBox.count())]
            self.updateComboBox(self._fragmentBox, fragItems + [''] + precItems)
            self._fragmentBox.model().item(len(fragItems)).setEnabled(False)

    def getModValues(self):
        if (self._modPatternBox.currentText() != "") and (self._modPatternBox.currentText() != "-"):
            self.updateComboBox(self._modifBox, self._controller.getModifItems(self._modPatternBox.currentText()))

    def calculateIsotopePattern(self):
        if self._inputForm.text() == '':
            return
        try:
            charge = int(self._charge.text())
            self._intensity = self._ionTable.getIntensity()
            if self._modeBox.currentIndex() == 0:
                ion, neutralMass, avMass = self._controller.calculate(self._modeBox.currentText(),
                                         self._inputForm.text(), charge, int(self._radicals.text()), self._intensity)
            else:
                ion, neutralMass, avMass= self._controller.calculate(self._modeBox.currentText(),
                                                                     self._inputForm.text(), charge, int(self._radicals.text()), self._intensity,
                                                                     self._fragmentationBox.currentText(), self._fragmentBox.currentText(),
                                                                     self._modPatternBox.currentText(), self._modifBox.currentText(), self._nrOfMods.value())
        except InvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        self.renderView(ion, neutralMass, avMass)

    def renderView(self, ion, neutralMass, avMass):
        self.renderSpectrumView(ion)
        self._ionTable.updateTable((self.getIonVals(ion,neutralMass,avMass),))
        self._ionTable.resizeColumnsToContents()
        self._peakTable.updateTable(ion.getIsotopePattern())
        self._peakTable.resizeColumnsToContents()

    def renderSpectrumView(self, ion):
        self._spectrumView.hide()
        del self._spectrumView
        isotopePattern = self._controller.getIsotopePattern(ion)
        self._spectrumView = TheoSpectrumView(self._centralwidget, isotopePattern, 365)
        self._spectrumView.setGeometry(QtCore.QRect(250, 50, 365, 300))

    def getIonVals(self, ion, neutralMass, avMass):
        if ion is None:
            return ()
        return (ion.getIsotopePattern()['m/z'][0], abs(ion.getCharge()), self._intensity, ion.getName(),
                ion.getQuality(),ion.getFormula().toString(), neutralMass, avMass)

    def makeIonTable(self, ion, neutralMass, avMass):
        self._ionTable = IsoPatternIon(self._centralwidget, (self.getIonVals(ion, neutralMass, avMass),), 0)
        self._ionTable.resizeColumnsToContents()
        self._vertLayout.insertWidget(2,self._ionTable)
        self._ionTable.show()

    def makePeakTable(self, peaks):
        scrollArea = QtWidgets.QScrollArea(self)
        verticalLayout = QtWidgets.QVBoxLayout(scrollArea)
        scrollArea.setWidgetResizable(True)
        self._peakTable = IsoPatternPeakWidget(scrollArea, peaks)
        self._peakTable.resizeColumnsToContents()

        scrollArea.setWidget(self._peakTable)
        verticalLayout.addWidget(self._peakTable)
        self._vertLayout.insertWidget(5, scrollArea)
        self._peakTable.show()


    def modelInt(self):
        try:
            inputVals = sorted(self._peakTable.readTable(), key=lambda tup: tup[2])
            peaks = []
            for i, peak in enumerate(self._peakTable.getPeaks()):
                peaks.append((peak[0], inputVals[i][0], peak[2], inputVals[i][1]))
            ion = self._controller.model(peaks)
            self._intensity = round(ion.getIntensity())
        except InvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        self.renderView(ion, self._controller.getNeutralMass(), self._controller.getAvMass())