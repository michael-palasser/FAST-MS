import copy

from PyQt5 import QtWidgets, QtCore
import numpy as np

from src.MolecularFormula import MolecularFormula
from src.Services import *
from src.entities.AbstractEntities import AbstractItem1
from src.entities.GeneralEntities import Sequence
from src.gui.IonTableWidget import IsoPatternIon
from src.gui.ResultView import IsoPatternPeakWidget
from src.gui.SpectrumView import TheoSpectrumView
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.SpectrumHandler import SpectrumHandler
from src.intact.LibraryBuilder import IntactLibraryBuilder


class IsotopePatternController(object):
    def __init__(self):
        self._moleculeService = MoleculeService()
        self._fragService = FragmentIonService()
        self._modService = ModificationService()
        self._elements = PeriodicTableService().getAllPatternNames()
        self._molecules = self._moleculeService.getAllPatternNames()
        self._intensityModeller = IntensityModeller(ConfigurationHandlerFactory.getTD_ConfigHandler().getAll())
        self._peakDtype = np.dtype([('m/z', np.float64), ('relAb', np.int32), ('calcInt', np.int32), ('used', np.bool_)])
        #self._peakDtype = np.dtype([('m/z', float), ('relAb', float), ('calcInt', float), ('used', np.bool_)])

        self._formula = None
        self._isotopePattern = None

    def getMolecules(self):
        return ['mol. formula']+self._molecules

    def getFragmentationNames(self):
        return self._fragService.getAllPatternNames()

    def getModifPatternNames(self):
        return self._modService.getAllPatternNames()

    def getFragItems(self, fragmentationName):
        return [fragTemplate.getName() for fragTemplate in
                self._fragService.getPatternWithObjects(fragmentationName).getItems()],\
               ['intact']+[precTemplate.getName() for precTemplate in
                self._fragService.getPatternWithObjects(fragmentationName).getItems2()]


    def getModifItems(self, modifPatternName):
        return [modTemplate.getName() for modTemplate in
                self._modService.getPatternWithObjects(modifPatternName).getItems()]

    def calculate(self, mode, inputString, charge, radicals, intensity, *args):
        if mode == self.getMolecules()[0]:
            formula = MolecularFormula(self.checkFormula(inputString))
        else:
            formula = self.getFormula(mode, inputString, args[0], args[1], args[2], args[3])
        if formula != self._formula:
            if formula.calcIsotopePatternSlowly(1)['m/z'][0]>6000:
                self._isotopePattern = formula.calculateIsotopePattern()
            else:
                self._isotopePattern = formula.calcIsotopePatternSlowly()
            self._isotopePattern['calcInt'] *= intensity
        neutralMass = self._isotopePattern['m/z'][0]
        isotopePattern = copy.deepcopy(self._isotopePattern)
        isotopePattern['m/z'] = SpectrumHandler.getMz(isotopePattern['m/z'],charge,radicals)
        peaks = []
        for row in isotopePattern:
            peaks.append((row['m/z'],0,round(row['calcInt']),1))
        peaks = np.array(peaks, dtype=self._peakDtype)
        return peaks, formula.toString(),neutralMass

    def checkFormula(self,formulaString):
        formula = AbstractItem1.stringToFormula(formulaString,{},1)
        if formula == {}:
            raise UnvalidInputException(formulaString, ", Unvalid format")
        for key in formula.keys():
            if key not in self._elements:
                print("Element: " + key + " unknown")
                raise UnvalidInputException(formulaString, ", Element: " + key + " unknown")
        return formula

    def getFormula(self, molecule, sequString, fragmentationName, fragTemplName, modifPatternName, modifName):
        molecule = self._moleculeService.get(molecule)
        sequenceList = Sequence("",sequString,molecule.getName(),0).getSequenceList()
        #formula = MolecularFormula(molecule.getFormula())
        buildingBlocks = molecule.getBBDict()
        formula = MolecularFormula({})
        for link in sequenceList:
            formula = formula.addFormula(buildingBlocks[link].getFormula())
        fragmentation = self._fragService.getPatternWithObjects(fragmentationName)
        if fragTemplName in (['intact']+[precTempl.getName() for precTempl in fragmentation.getItems2()]):
            formula = formula.addFormula(molecule.getFormula())
            if fragTemplName != 'intact':
                fragTempl = [precTempl for precTempl in fragmentation.getItems2() if precTempl.getName()==fragTemplName][0]
            else:
                fragTempl = PrecursorItem(("", "", "", "", 0, True))
            #name = 'intact'+ fragTempl.getName()
        else:
            fragTempl = [fragTempl for fragTempl in fragmentation.getItems() if fragTempl.getName()==fragTemplName][0]
            #name = fragTempl.getName()+len(sequenceList)
        formula = formula.addFormula(fragTempl.getFormula())
        if modifPatternName != '-':
            modPattern = self._modService.getPatternWithObjects(modifPatternName)
            modif = [modif for modif in modPattern.getItems() if modif.getName()==modifName][0]
            formula = formula.addFormula(modif.getFormula())
        return formula

    def model(self, peaks):
        peakArr = np.array(peaks, dtype=self._peakDtype)
        if np.all(peakArr['relAb']==0):
            raise UnvalidInputException('All Intensities = 0', '')
        return self._intensityModeller.modelSimply(peakArr)


class IsotopePatternView(QtWidgets.QMainWindow):
    def __init__(self, parent):
        super(IsotopePatternView, self).__init__(parent)
        self._controller = IsotopePatternController()
        self._fragmentationOpts = self._controller.getFragmentationNames()
        self._modifPatternOpts = self._controller.getModifPatternNames()
        self._intensity = 100
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), 'Isotope Pattern Tool'))
        self.centralwidget = QtWidgets.QWidget(self)

        self.inputForm = QtWidgets.QLineEdit(self.centralwidget)
        self.inputForm.setGeometry(QtCore.QRect(15, 30, 185, 21))
        self.inputForm.returnPressed.connect(self.calculateIsotopePattern)

        modeLabel = QtWidgets.QLabel(self.centralwidget)
        modeLabel.setGeometry(QtCore.QRect(15, 70, 60, 16))
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        self.modeBox = QtWidgets.QComboBox(self.centralwidget)
        self.modeBox.setGeometry(QtCore.QRect(65, 67, 120, 26))
        self.fillComboBox(self.modeBox, self._controller.getMolecules())

        chargeLabel = QtWidgets.QLabel(self.centralwidget)
        chargeLabel.setGeometry(QtCore.QRect(15, 100, 60, 16))
        chargeLabel.setText(self._translate(self.objectName(), "Charge:"))
        self.charge = QtWidgets.QSpinBox(self.centralwidget)
        self.charge.setGeometry(QtCore.QRect(70, 97, 50, 24))
        self.charge.setMinimum(-99)
        self.charge.valueChanged.connect(self.calculateIsotopePattern)
        radicalLabel = QtWidgets.QLabel(self.centralwidget)
        radicalLabel.setGeometry(QtCore.QRect(130, 100, 60, 16))
        radicalLabel.setText(self._translate(self.objectName(), "Radicals:"))
        self.radicals = QtWidgets.QSpinBox(self.centralwidget)
        self.radicals.setGeometry(QtCore.QRect(190, 97, 40, 24))
        self.radicals.setMinimum(-9)
        self.radicals.setMaximum(9)
        self.radicals.valueChanged.connect(self.calculateIsotopePattern)

        self.pushCalc = self.makeBtn(60, 140, "Calculate")
        self.pushCalc.clicked.connect(self.calculateIsotopePattern)
        self.pushModel = self.makeBtn(140,140, "Model")
        self.pushModel.clicked.connect(self.modelInt)
        self.makeOptions()

        self.spectrumView = QtWidgets.QFrame(self.centralwidget)

        self.spectrumView.setGeometry(QtCore.QRect(250, 30, 350, 290))
        self.spectrumView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #self.spectrumView.setFrameShadow(QtWidgets.QFrame.Raised)
        self.spectrumView.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.spectrumView.setStyleSheet('background-color: white')

        self.makeIonTable(())
        #self.ionTable.setGeometry(QtCore.QRect(20, 335, 550, 50))
        peakLabel = QtWidgets.QLabel(self.centralwidget)
        peakLabel.setGeometry(QtCore.QRect(25, 415, 60, 16))
        peakLabel.setText(self._translate(self.objectName(), "Peaks:"))

        self.makePeakTable((()))
        #self.peakTable.setGeometry(QtCore.QRect(20, 400, 550, 190))

        self.modeBox.currentIndexChanged.connect(self.activateFrame)
        self.setCentralWidget(self.centralwidget)
        self.resize(615, 400)
        self.show()


    def makeOptions(self):
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(15, 180, 220, 140))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frameLabels = ("Fragmentation:", "Fragment:", "Modif.Pattern:", "Modification:")
        self.fragmentationBox = QtWidgets.QComboBox(self.frame)
        self.fragmentBox = QtWidgets.QComboBox(self.frame)
        self.fragmentationBox.currentIndexChanged.connect(self.getFragValues)
        self.modPatternBox = QtWidgets.QComboBox(self.frame)
        self.modPatternBox.currentIndexChanged.connect(self.getModValues)
        self.modifBox = QtWidgets.QComboBox(self.frame)
        self.fillFrame(frameLabels, (self.fragmentationBox, self.fragmentBox, self.modPatternBox, self.modifBox),
                       ("", "", "", ""))
        #self.boxes = (self.fragmentationBox, self.modPatternBox, self.fragmentBox, self.modifBox)
        self.frame.hide()

    def makeBtn(self,xPos, yPos, name):
        btn = QtWidgets.QPushButton(self.centralwidget)
        btn.setGeometry(QtCore.QRect(xPos-int(81/2), yPos, 81, 32))
        btn.setText(self._translate(self.objectName(), name))
        return btn

    def fillFrame(self, labelNames, boxes, toolTips):
        yPos = 10
        for i, labelName in enumerate(labelNames):
            label = QtWidgets.QLabel(self.frame)
            label.setGeometry(QtCore.QRect(10, yPos, 90, 16))
            label.setText(self._translate(self.objectName(), labelName))
            boxes[i].setGeometry(QtCore.QRect(100, yPos - 4, 120, 26))
            boxes[i].setToolTip(toolTips[i])
            yPos += 30
            if i == 1:
                yPos += 10


    def fillComboBox(self, box, options, *args):
        toAdjust = box.count()-len(options)
        if args:
            toAdjust-=len(args[0])-1
        if toAdjust > 0:
            [box.removeItem(i) for i in range(len(options), len(options)+toAdjust)]
        elif toAdjust < 0:
            #print('hey',  [i for i in range(toAdjust)])
            [box.addItem("") for i in range(-1*toAdjust)]
        for i, option in enumerate(options):
            box.setItemText(i, self._translate(self.objectName(), option))
        if args:
            lastIndex = len(options)
            box.insertSeparator(lastIndex)
            for i,option in enumerate(args[0]):
                box.setItemText(i+lastIndex, self._translate(self.objectName(), option))


    def activateFrame(self):
        if self.frame.isVisible() and self.modeBox.currentIndex() == 0:
            self.frame.hide()
            #for box in self.boxes:
            #    self.fillComboBox(box, [""])
        elif not self.frame.isVisible() and self.modeBox.currentIndex() != 0:
            self.fillComboBox(self.fragmentationBox, self._fragmentationOpts)
            self.fillComboBox(self.modPatternBox, self._modifPatternOpts)
            self.getFragValues()
            self.getModValues()
            self.frame.show()


    def getFragValues(self):
        if self.fragmentationBox.currentText() != "":
            fragItems, precItems = self._controller.getFragItems(self.fragmentationBox.currentText())
            self.fillComboBox(self.fragmentBox, fragItems, precItems)

    def getModValues(self):
        if (self.modPatternBox.currentText() != "") and (self.modPatternBox.currentText() != "-"):
            self.fillComboBox(self.modifBox, self._controller.getModifItems(self.modPatternBox.currentText()))

    def calculateIsotopePattern(self):
        if self.inputForm.text() == '':
            return
        try:
            charge = int(self.charge.text())
            self._intensity = self._ionTable.getIntensity()
            if self.modeBox.currentIndex() == 0:
                peaks, formula, neutralMass= self._controller.calculate(self.modeBox.currentText(),
                                            self.inputForm.text(), charge, int(self.radicals.text()), self._intensity)
            else:
                peaks, formula, neutralMass= self._controller.calculate(self.modeBox.currentText(),
                                        self.inputForm.text(), charge, int(self.radicals.text()), self._intensity,
                                        self.fragmentationBox.currentText(), self.fragmentBox.currentText(),
                                        self.modPatternBox.currentText(), self.modifBox.currentText())
        except UnvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return

        self.restartView((peaks['m/z'][0],abs(charge), self._intensity,"-", 0.,formula, neutralMass), peaks)
        '''self.spectrumView = TheoSpectrumView(self.centralwidget,(),isotopePattern)
        self.spectrumView.setGeometry(QtCore.QRect(270, 30, 300, 290))
        self.peakTable.hide()
        del self.peakTable
        del self._ionTable
        #self._ionTable = IsoPatternIon(self.centralwidget,((isotopePattern['m/z'][0],abs(charge),
        #           int(np.around(np.sum(isotopePattern['calcInt']))), 0),),335)
        #self.peakTable = IsoPatternPeakWidget(self.centralwidget,peaks)
        #hight = len(peaks)*21+28
        #if hight>400:
        #    hight=400
        #self.peakTable.setGeometry(QtCore.QRect(20, 400, 550, hight)) #290
        self.makeIonTable((isotopePattern['m/z'][0],abs(charge), self._intensity,"-", 0.,formula))
        hight = self.makePeakTable(peaks)
        self.resize(585, 420+hight+30)'''
        #self.peakTable.show()

    def restartView(self, ion, peaks):
        self.spectrumView = TheoSpectrumView(self.centralwidget, peaks, 350)
        self.spectrumView.setGeometry(QtCore.QRect(250, 30, 350, 290))
        self.peakTable.hide()
        del self.peakTable
        del self._ionTable
        self.makeIonTable(ion)
        hight = self.makePeakTable(peaks)
        self.resize(615, 420 + hight + 30)

    def makeIonTable(self, ion):
        self._ionTable = IsoPatternIon(self.centralwidget,(ion,),335)
        self._ionTable.setGeometry(QtCore.QRect(15, 340,585,55))
        self._ionTable.resizeColumnsToContents()
        self._ionTable.show()

    def makePeakTable(self, peaks):
        self.peakTable = IsoPatternPeakWidget(self.centralwidget, peaks)
        hight = len(peaks) * 21 + 28
        if hight>400:
            hight=400
        self.peakTable.setGeometry(QtCore.QRect(50, 440, 450, hight)) #290
        self.peakTable.resizeColumnsToContents()
        self.peakTable.show()
        return hight
    #def formatSpectrumView(self):
     #   self.spectrumView.setGeometry(QtCore.QRect(320, 35, 250, 235))

    def modelInt(self):
        inputVals = sorted(self.peakTable.readTable(), key=lambda tup:tup[2])
        peaks = []
        for i, peak in enumerate(self.peakTable.getPeaks()):
            peaks.append((peak[0],inputVals[i][0], peak[2], inputVals[i][1]))
        try:
            peaks, self._intensity, quality = self._controller.model(peaks)
        except UnvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        ionVals = list(self._ionTable.getIon(0))
        ionVals[2] = round(self._intensity)
        ionVals[4] = quality
        self.restartView(ionVals, peaks)