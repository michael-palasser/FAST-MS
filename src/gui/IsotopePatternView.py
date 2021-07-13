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
        widget1,horizLayout1 = self.getHorizWidget(self._centralwidget, self._vertLayout, 15,5)

        self._inputForm = QtWidgets.QLineEdit(widget1)
        self._inputForm.returnPressed.connect(self.calculateIsotopePattern)
        horizLayout1.addWidget(self._inputForm)
        modeLabel = QtWidgets.QLabel(widget1)
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        horizLayout1.addWidget(modeLabel)
        self._modeBox = QtWidgets.QComboBox(widget1)
        self.updateComboBox(self._modeBox, self._controller.getMolecules())
        horizLayout1.addWidget(self._modeBox)

        widget2,chargeRadLayout = self.getHorizWidget(self._centralwidget, self._vertLayout,5,15)

        self._leftWidget, self._vertLayoutLeft = self.getVertWidget(widget2, chargeRadLayout)
        self._leftWidget.setMaximumWidth(260)
        self._rightWidget, self._vertLayoutRight = self.getVertWidget(widget2, chargeRadLayout)
        chargeRadWidget, chargeRadLayout = self.getHorizWidget(self._leftWidget, self._vertLayoutLeft)
        chargeLabel = QtWidgets.QLabel(chargeRadWidget)
        chargeLabel.setText(self._translate(self.objectName(), "Charge:"))
        chargeRadLayout.addWidget(chargeLabel)
        self._charge = QtWidgets.QSpinBox(chargeRadWidget)
        self._charge.setMinimum(-99)
        self._charge.valueChanged.connect(self.calculateByChange)
        chargeRadLayout.addWidget(self._charge)
        radicalLabel = QtWidgets.QLabel(chargeRadWidget)
        radicalLabel.setText(self._translate(self.objectName(), "Electrons:"))
        chargeRadLayout.addWidget(radicalLabel)
        self._radicals = QtWidgets.QSpinBox(chargeRadWidget)
        self._radicals.setMinimum(-9)
        self._radicals.setMaximum(9)
        self._radicals.valueChanged.connect(self.calculateByChange)
        chargeRadLayout.addWidget(self._radicals)
        btnWidget, btnLayout = self.getHorizWidget(self._leftWidget, self._vertLayoutLeft,0,10)

        self.makeBtn(self._leftWidget, btnLayout, "Calculate", self.calculateIsotopePattern)
        self.makeBtn(self._leftWidget, btnLayout, "Model",self.modelInt)

        self.makeOptions()

        self._spectrumView = QtWidgets.QFrame(self._rightWidget)
        self._spectrumView.setMinimumSize(335, 270)
        self._spectrumView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._spectrumView.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self._spectrumView.setStyleSheet('background-color: white')
        self._vertLayoutRight.addWidget(self._spectrumView)
        self._vertLayout.addSpacing(10)
        self.makeIonTable(None, None, None)

        self._vertLayout.addItem(QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Expanding))

        self._peakLabel = QtWidgets.QLabel(self._centralwidget)
        self._peakLabel.setText(self._translate(self.objectName(), "Peaks:"))
        self._vertLayout.addWidget(self._peakLabel)
        self.makePeakTable(((),))

        self._modeBox.currentIndexChanged.connect(self.renderFrame)
        self._centralwidget.setLayout(self._vertLayout)
        self.createMenuBar()
        self.createMenu('Options', {'Load Sequence': (self.loadSequence, None, "Ctrl+O"),
                                    'Pause Calculation': (self.pauseCalculation, None, None)}, None)
        self._pause = False
        self.show()

    def getHorizWidget(self, parent, layout, top=0, bottom=0):
        widget = QtWidgets.QWidget(parent)
        horizLayout = QtWidgets.QHBoxLayout(widget)
        horizLayout.setContentsMargins(5, top, 5, bottom)
        widget.setLayout(horizLayout)
        layout.addWidget(widget)
        return widget, horizLayout

    def getVertWidget(self, parent, layout):
        widget = QtWidgets.QWidget(parent)
        vertLayout = QtWidgets.QVBoxLayout(widget)
        vertLayout.setContentsMargins(0,0,0,0)
        widget.setLayout(vertLayout)
        layout.addWidget(widget)
        return widget,vertLayout

    def makeOptions(self):
        '''
        Constructs the QFrame with the ion options (fragmentation, modification, ...)
        '''
        self._frame = QtWidgets.QFrame(self._leftWidget)
        self._frame.setMinimumSize(230, 180)
        formlayout = QtWidgets.QFormLayout(self._frame)
        formlayout.setContentsMargins(5,5,5,5)
        formlayout.setLabelAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        formlayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        formlayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self._frame.setLayout(formlayout)
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
        self._nrOfMods.setValue(0)
        self._optionWidgets = (self._fragmentationBox, self._fragmentBox,
                                     self._modPatternBox, self._modifBox, self._nrOfMods)
        self.fillFrame(formlayout,frameLabels, self._optionWidgets, ("", "", "", "", ''))
        self._vertLayoutLeft.addWidget(self._frame)

    def makeBtn(self, parent, layout, name, fun):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(self._translate(self.objectName(), name))
        layout.addWidget(btn)
        btn.clicked.connect(fun)
        return btn

    def fillFrame(self,formlayout, labelNames, widgets, toolTips):
        '''
        Inserts the ion option (fragmentation, modification, ...) widgets into the QFrame
        '''
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        for i, labelName in enumerate(labelNames):
            label = QtWidgets.QLabel(self._frame)
            label.setText(self._translate(self.objectName(), labelName))
            widgets[i].setToolTip(toolTips[i])
            widgets[i].setDisabled(True)
            widgets[i].setSizePolicy(sizePolicy)
            formlayout.setWidget(i, QtWidgets.QFormLayout.LabelRole, label)
            formlayout.setWidget(i, QtWidgets.QFormLayout.FieldRole, widgets[i])

    def loadSequence(self):
        service = SequenceService()
        openDialog = OpenDialog('Sequences', service.getAllSequenceNames())
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            sequence = service.get(openDialog.getName())
            self._inputForm.setText(''.join(sequence.getSequenceString()))
            self._modeBox.setCurrentText(sequence.getMolecule())

    def pauseCalculation(self):
        if self._pause:
            self._pause = False
        else:
            self._pause = True

    def renderFrame(self):
        if self._modeBox.currentIndex() == 0:
            self._nrOfMods.setValue(0)
            self._nrOfMods.setDisabled(True)
            for box in self._optionWidgets[:-1]:
                box.setCurrentText('')
                box.setDisabled(True)
        elif self._modeBox.currentIndex() != 0:
            for box in self._optionWidgets:
                box.setDisabled(False)
            self.updateComboBox(self._fragmentationBox, self._fragmentationOpts)
            self.updateComboBox(self._modPatternBox, self._modifPatternOpts)
            self.getFragValues()
            self.getModValues()


    def getFragValues(self):
        if self._fragmentationBox.currentText() != "":
            fragItems, precItems = self._controller.getFragItems(self._fragmentationBox.currentText())
            [self._fragmentBox.model().item(i).setEnabled(True) for i in range(self._fragmentBox.count())]
            self.updateComboBox(self._fragmentBox, fragItems + [''] + precItems)
            self._fragmentBox.model().item(len(fragItems)).setEnabled(False)

    def getModValues(self):
        if (self._modPatternBox.currentText() != "") and (self._modPatternBox.currentText() != "-"):
            self.updateComboBox(self._modifBox, self._controller.getModifItems(self._modPatternBox.currentText()))

    def calculateByChange(self):
        '''
        If nr of electrons or charge is changed
        '''
        if not self._pause:
            self.calculateIsotopePattern()

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
        self._vertLayoutRight.removeWidget(self._spectrumView)
        del self._spectrumView
        isotopePattern = self._controller.getIsotopePattern(ion)
        self._spectrumView = TheoSpectrumView(self._rightWidget, isotopePattern, 365)
        self._spectrumView.setMinimumSize(365, 300)
        self._vertLayoutRight.addWidget(self._spectrumView)

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
        self._vertLayout.insertWidget(6, scrollArea)
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