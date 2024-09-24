from PyQt5 import QtWidgets, QtCore
from pandas import DataFrame

from src.resources import DEVELOP
from src.services.IsotopePatternLogics import IsotopePatternLogics
from src.services.DataServices import *
from src.gui.mainWindows.AbstractMainWindows import SimpleMainWindow
from src.gui.GUI_functions import makeFormLayout, shoot, connectTable
from src.gui.widgets.IonTableWidgets import IsoPatternIon
from src.gui.widgets.PeakWidgets import IsoPatternPeakWidget
from src.gui.dialogs.SimpleDialogs import OpenDialog
from src.gui.widgets.SpectrumView import TheoSpectrumView


class IsotopePatternView(SimpleMainWindow):
    '''
    Main window for Isotope Pattern Tool
    '''
    def __init__(self, parent):
        super(IsotopePatternView, self).__init__(parent, 'Model Ion')
        self._ion= None
        self._logics = IsotopePatternLogics()
        self._fragmentationOpts = self._logics.getFragmentationNames()
        self._modifPatternOpts = self._logics.getModifPatternNames()
        self._intensity = None
        self._vertLayout = QtWidgets.QVBoxLayout(self._centralwidget)
        self._widget1,self._horizLayout1 = self.getHorizWidget(self._centralwidget, self._vertLayout, 15,5)

        self._inputForm = QtWidgets.QLineEdit(self._widget1)
        self._inputForm.returnPressed.connect(self.calculateIsotopePattern)
        self._inputForm.textChanged.connect(self.calculateIsotopePattern)
        self._horizLayout1.addWidget(self._inputForm)
        modeLabel = QtWidgets.QLabel(self._widget1)
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        self._horizLayout1.addWidget(modeLabel)
        self._modeBox = QtWidgets.QComboBox(self._widget1)
        self.updateComboBox(self._modeBox, self._logics.getMolecules())
        self._horizLayout1.addWidget(self._modeBox)

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
        self._radicals.setRange(-9,9)
        self._radicals.valueChanged.connect(self.calculateByChange)
        chargeRadLayout.addWidget(self._radicals)

        btnWidget, btnLayout = self.getHorizWidget(self._leftWidget, self._vertLayoutLeft,0,10)
        self._exact = QtWidgets.QCheckBox('Exact',btnWidget)
        #self._exact.setEnabled(False)
        #self._exact.setChecked(True)
        btnLayout.addWidget(self._exact)
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
        #self._peakTable.model().rowsRemoved.connect(lambda: self.renderView(self._ion, self._logics.getNeutralMass(), self._logics.getAvMass()))

        self._modeBox.currentIndexChanged.connect(self.renderFrame)
        self._centralwidget.setLayout(self._vertLayout)
        self.createMenuBar()
        actions = {'Load Sequence': (self.loadSequence, None, "Ctrl+O"),
                                    'Pause Calculation': (self.pauseCalculation, None, None),
                                    #'Shoot': (lambda: shoot(self), None, None),
                                    'Close': (self.close, 'Closes Window', 'Ctrl+Q')}

        if DEVELOP:
            actions['Shoot']=(lambda: shoot(self), None, None)
        self._menubar, self._menuActions = self.createMenu('Options', actions, None)
        self.makeHelpMenu()
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
        formlayout = makeFormLayout(self._frame)
        formlayout.setContentsMargins(5,5,5,5)
        self._frame.setLayout(formlayout)
        self._frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._options = {key:QtWidgets.QComboBox(self._frame) for key in ('fragmentation', 'fragment', 'modPattern', 'modif')}
        for key, fun in {'fragmentation':self.getFragValues, 'fragment':self.changeRadicals,
                         'modPattern':self.getModValues, 'modif':self.changeRadicals}.items():
            self._options[key].currentIndexChanged.connect(fun)
        '''self._options['fragmentation'].currentIndexChanged.connect(self.getFragValues)
        self._options['fragment'].currentIndexChanged.connect(self.changeRadicals)
        self._options['modPattern'].currentIndexChanged.connect(self.getModValues)
        self._options['modif'].currentIndexChanged.connect(self.changeRadicals)'''
        self._options['nrMod'] = QtWidgets.QSpinBox(self._frame)
        self._options['nrMod'].setValue(0)
        self._options['nrMod'].valueChanged.connect(self.calculateByChange)
        self.fillFrame(formlayout, ("", "", "", "", ''))
        self._vertLayoutLeft.addWidget(self._frame)

    def makeBtn(self, parent, layout, name, fun):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(self._translate(self.objectName(), name))
        layout.addWidget(btn)
        btn.clicked.connect(fun)
        return btn

    def fillFrame(self,formlayout, toolTips):
        '''
        Inserts the ion option (fragmentation, modification, ...) widgets into the QFrame
        '''
        labelNames = ("Fragmentation:", "Fragment:", "Modif. Pattern:", "Modification:", "Nr. of Mod.:")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        for i, key in enumerate(self._options.keys()):
            label = QtWidgets.QLabel(self._frame)
            label.setText(self._translate(self.objectName(), labelNames[i]))
            self._options[key].setToolTip(toolTips[i])
            self._options[key].setDisabled(True)
            self._options[key].setSizePolicy(sizePolicy)
            formlayout.setWidget(i, QtWidgets.QFormLayout.LabelRole, label)
            formlayout.setWidget(i, QtWidgets.QFormLayout.FieldRole, self._options[key])

    def changeRadicals(self):
        radicals = self._logics.getRadicals(self._modeBox.currentText(), self._inputForm.text(),
                                 self._options['fragmentation'].currentText(),
                                 self._options['fragment'].currentText(), self._options['modPattern'].currentText(),
                                 self._options['modif'].currentText(), self._options['nrMod'].value())
        self._radicals.setValue(radicals)
        self.calculateByChange()


    def loadSequence(self):
        service = SequenceService()
        openDialog = OpenDialog('Sequences', service.getAllSequenceNames())
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            sequence = service.get(openDialog.getName())
            self._modeBox.setCurrentText(sequence.getMolecule())
            self._inputForm.setText(''.join(sequence.getSequenceString()))
            allItems = [self._options["fragmentation"].itemText(i) for i in
                        range(self._options["fragmentation"].count())]
            if "NA" in sequence.getMolecule():
                if "RNA CAD" in allItems:
                    self._options["fragmentation"].setCurrentIndex(allItems.index("RNA CAD"))
            elif "Protein CAD" in allItems:
                self._options["fragmentation"].setCurrentIndex(allItems.index("Protein CAD"))
            allItems2 = [self._options["fragment"].itemText(i) for i in range(self._options["fragment"].count())]
            if "intact" in allItems2:
                self._options["fragment"].setCurrentIndex(allItems2.index("intact"))

    def pauseCalculation(self):
        if self._pause:
            self._pause = False
            self._menuActions['Pause Calculation'].setText('Pause Calculation')
        else:
            self._pause = True
            self._menuActions['Pause Calculation'].setText('Resume Calculation')

    def renderFrame(self):
        if self._modeBox.currentIndex() == 0:
            self._options['nrMod'].setValue(0)
            self._options['nrMod'].setDisabled(True)
            for box in list(self._options.values())[:-1]:
                box.setCurrentText('')
                box.setDisabled(True)
        elif self._modeBox.currentIndex() != 0:
            for box in self._options.values():
                box.setDisabled(False)
            self.updateComboBox(self._options['fragmentation'], self._fragmentationOpts)
            self.updateComboBox(self._options['modPattern'], self._modifPatternOpts)
            self.getFragValues()
            self.getModValues()


    def getFragValues(self):
        if self._options['fragmentation'].currentText() != "":
            fragItems, precItems = self._logics.getFragItems(self._options['fragmentation'].currentText())
            [self._options['fragment'].model().item(i).setEnabled(True) for i in range(self._options['fragment'].count())]
            self.updateComboBox(self._options['fragment'], fragItems + [''] + precItems)
            self._options['fragment'].model().item(len(fragItems)).setEnabled(False)
            self.calculateByChange()

    def getModValues(self):
        if self._options['modPattern'].currentText() not in  ('',"-"):
            self.updateComboBox(self._options['modif'], self._logics.getModifItems(self._options['modPattern'].currentText()))
            self._options['modif'].setEnabled(True)
            self._options['nrMod'].setEnabled(True)
        else:
            self.updateComboBox(self._options['modif'], ('',))
            self._options['modif'].setDisabled(True)
            self._options['nrMod'].setValue(0)
            self._options['nrMod'].setDisabled(True)

        self.calculateByChange()

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
            accelerate = 10
            if self._exact.isChecked():
                accelerate = None
            if self._modeBox.currentIndex() == 0:
                self._ion, neutralMass, avMass = self._logics.calculate(self._modeBox.currentText(),
                                                                        self._inputForm.text(), charge, int(self._radicals.text()), self._intensity,
                                                                        accelerate=accelerate)
            else:
                self._ion, neutralMass, avMass= self._logics.calculate(self._modeBox.currentText(),
                                                                       self._inputForm.text(), charge, int(self._radicals.text()), self._intensity,
                                                                       self._options['fragmentation'].currentText(), self._options['fragment'].currentText(),
                                                                       self._options['modPattern'].currentText(), self._options['modif'].currentText(), self._options['nrMod'].value(),
                                                                       accelerate)
        except InvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        self.renderView(self._ion, neutralMass, avMass,charge)

    def renderView(self, ion, neutralMass, avMass, charge):
        self.renderSpectrumView(ion,charge)
        self._ionTable.updateTable((self.getIonVals(ion,neutralMass,avMass),))
        self._ionTable.resizeColumnsToContents()
        self._peakTable.updateTable(ion.getIsotopePattern())
        self._peakTable.resizeColumnsToContents()

    def renderSpectrumView(self, ion, charge):
        self._spectrumView.hide()
        self._vertLayoutRight.removeWidget(self._spectrumView)
        del self._spectrumView
        #isotopePattern = self._logics.getIsotopePattern(ion)
        self._spectrumView = TheoSpectrumView(self._rightWidget, ion.getIsotopePattern(), 365, charge)
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
        connectTable(self._peakTable, self.showOptions)
        self._peakTable.show()


    def modelInt(self):
        try:
            #inputVals = sorted(self._peakTable.readTable(), key=lambda tup: tup[2])
            inputVals = sorted(self._peakTable.getData(), key=lambda tup: tup[0])
            peaks = []
            for i, peak in enumerate(self._peakTable.getPeaks()):
                peaks.append((peak[0], inputVals[i][1], peak[2], inputVals[i][3]))
            self._ion = self._logics.model(peaks)
            self._intensity = round(self._ion.getIntensity())
        except InvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        self.renderView(self._ion, self._logics.getNeutralMass(), self._logics.getAvMass(), int(self._charge.text()))

    def showOptions(self, table, pos):
        '''
        Right click options of the table
        '''
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        deleteAction = menu.addAction("Delete Last Peak")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAllAction:
            # df = self.getDataframe()
            df = DataFrame(table.getData(), columns=table.getHeaders())
            df.to_clipboard(index=False, header=True)
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            # df = pd.DataFrame([self._peaks[selectedRow][selectedCol]])
            df = DataFrame([self.getData()[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == deleteAction:
            self._peakTable.deleteLastPeak() #To
            ion = self._logics.getIon()
            ion.setIsotopePattern(ion.getIsotopePattern()[:-1])
            self._logics.setIon(ion)
            self.renderSpectrumView(ion,int(self._charge.text()))


class AddIonView(IsotopePatternView):
    '''
    QMainWindow which is used to add new ions to ion list in top-down search
    '''
    def __init__(self, parent, mode, sequence, sequenceName, charge, fragmentation, modification, fun):
        super(AddIonView, self).__init__(parent)
        self.setWindowTitle(self._translate(self.objectName(),'New Ion'))
        self.setBox(self._modeBox,mode)
        self._inputForm.setText(sequence)
        self._sequenceName = sequenceName
        self.setChargeRange(charge)
        self.setBox(self._options['fragmentation'],fragmentation)
        self.setBox(self._options['modPattern'],modification)
        self._signal = fun
        self._saveBtn = self.makeBtn(self._widget1,self._horizLayout1, 'Save', self.accept)

    def setChargeRange(self, charge):
        if charge<0:
            self._charge.setMinimum(charge)
            self._charge.setMaximum(-1)
        else:
            self._charge.setMaximum(charge)
            self._charge.setMinimum(1)

    def setBox(self, box, value):
        box.setCurrentText(value)
        box.setEnabled(False)

    def getIon(self):
        if "Prec" in self._ion.getName():
            self._ion.setType(self._sequenceName)
        return self._ion

    def accept(self):
        if self._ion == None:
            dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Invalid Request',
                                        'No input, sequence is empty', QtWidgets.QMessageBox.Ok, self)
            dlg.show()
        if self._ion.getIntensity() == 0:
            dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Invalid Request',
                                        'Intensity of the new ion must not be 0!', QtWidgets.QMessageBox.Ok, self)
            dlg.show()
        elif self._ion.getCharge() == 0:
            dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Invalid Request',
                                        'Charge of the new ion must not be 0!', QtWidgets.QMessageBox.Ok, self)
            dlg.show()
        else:
            self._signal(self)


    def getIonVals(self, ion, neutralMass, avMass):
        if ion is None:
            return ()
        self.correctName(ion)
        return (ion.getIsotopePattern()['m/z'][0], abs(ion.getCharge()), self._intensity, ion.getName(),
                ion.getQuality(),ion.getFormula().toString(), neutralMass, avMass)

    def correctName(self, ion):
        type = ion.getType()
        if "Prec" in type:
            ion.setType(self._sequenceName+type[4:])
