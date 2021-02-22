import copy

from PyQt5 import QtWidgets, QtCore, Qt

from src.MolecularFormula import MolecularFormula
from src.Services import *
from src.entities.AbstractEntities import AbstractItem1
from src.gui.IonTableWidget import IsoPatternIon
from src.gui.ResultView import PeakWidget, IsoPatternPeakWidget
from src.gui.SpectrumView import TheoSpectrumView
from src.top_down.SpectrumHandler import SpectrumHandler


class IsotopePatternController(object):
    def __init__(self):
        self._moleculeService = MoleculeService()
        self._fragService = FragmentIonService()
        self._modService = ModificationService()
        self._elements = PeriodicTableService().getAllPatternNames()
        self._formula = None
        self._isotopePattern = None
        #self._moleculeNames = moleculeService.getAllPatternNames()
        #self._fragmentationNames = self._fragService.getAllPatternNames()
        #self._modifNames = self._modService.getAllPatternNames()
        #self.__molecule = None
        #self.__fragmentation = None
        #self.__modifPattern = None
        '''self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        self.__fragmentation = FragmentIonService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModifiedItem)'''
        '''self._view = IsotopePatternView(parent, ['mol. formula']+self._moleculeNames,
                self._fragService.getAllPatternNames(), self._modService.getAllPatternNames(),
                self._fragService.getPatternWithObjects, self._modService.getPatternWithObjects,
                                        self.calculate)'''
        #self._view.modeBox.currentIndexChanged.connect(self.activateFrame)
        #print(self._view.modeBox.currentText())
        #self._view.fragmentationBox.currentTextChanged.connect(self.getFragItems)
        #self._view.modPatternBox.currentTextChanged.connect(self.getModifItems)

    def getMolecules(self):
        return ['mol. formula']+self._moleculeService.getAllPatternNames()

    def getFragmentationNames(self):
        return self._fragService.getAllPatternNames()

    def getModifPatternNames(self):
        return self._modService.getAllPatternNames()

    def getFragItems(self, fragmentationName):
        return [fragTemplate.getName() for fragTemplate in
                self._fragService.getPatternWithObjects(fragmentationName).getItems()]

    def getModifItems(self, modifPatternName):
        return [modTemplate.getName() for modTemplate in
                self._modService.getPatternWithObjects(modifPatternName).getItems()]

    def calculate(self, formulaString, charge, intensity):
        formula = self.checkFormula(formulaString)
        formula = MolecularFormula(formula)
        if formula != self._formula:
            if formula.calcIsotopePatternSlowly(1)['m/z'][0]>6000:
                self._isotopePattern = formula.calculateIsotopePattern()
            else:
                self._isotopePattern = formula.calcIsotopePatternSlowly()
            self._isotopePattern['calcInt'] *= intensity
        isotopePattern = copy.deepcopy(self._isotopePattern)
        if charge!= 0:
            isotopePattern['m/z'] = SpectrumHandler.getMz(isotopePattern['m/z'],charge,0)
        print(isotopePattern)
        peaks = []
        for row in isotopePattern:
            peaks.append((row['m/z'],0,round(row['calcInt']),1))
        return isotopePattern, peaks

    def checkFormula(self,formulaString):
        formula = AbstractItem1.stringToFormula(formulaString,{},1)
        if formula == {}:
            raise UnvalidInputException(formulaString, ", Unvalid format")
        for key in formula.keys():
            if key not in self._elements:
                print("Element: " + key + " unknown")
                raise UnvalidInputException(formulaString, ", Element: " + key + " unknown")
        return formula



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

        modeLabel = QtWidgets.QLabel(self.centralwidget)
        modeLabel.setGeometry(QtCore.QRect(15, 70, 60, 16))
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        self.modeBox = QtWidgets.QComboBox(self.centralwidget)
        self.modeBox.setGeometry(QtCore.QRect(80, 67, 120, 26))
        self.fillComboBox(self.modeBox, self._controller.getMolecules())

        chargeLabel = QtWidgets.QLabel(self.centralwidget)
        chargeLabel.setGeometry(QtCore.QRect(15, 100, 60, 16))
        chargeLabel.setText(self._translate(self.objectName(), "Charge:"))
        self.charge = QtWidgets.QSpinBox(self.centralwidget)
        self.charge.setGeometry(QtCore.QRect(85, 98, 70, 24))
        self.charge.setMinimum(-99)

        self.pushCalc = self.makeBtn(60, 140, "Calculate")
        self.pushCalc.clicked.connect(self.calculateIsotopePattern)
        self.pushModel = self.makeBtn(140,140, "Model")
        self.makeOptions()

        self.spectrumView = QtWidgets.QFrame(self.centralwidget)

        self.spectrumView.setGeometry(QtCore.QRect(270, 30, 300, 290))
        self.spectrumView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #self.spectrumView.setFrameShadow(QtWidgets.QFrame.Raised)
        self.spectrumView.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.spectrumView.setStyleSheet('background-color: white')

        self.makeIonTable(())
        #self.ionTable.setGeometry(QtCore.QRect(20, 335, 550, 50))
        peakLabel = QtWidgets.QLabel(self.centralwidget)
        peakLabel.setGeometry(QtCore.QRect(25, 400, 60, 16))
        peakLabel.setText(self._translate(self.objectName(), "Peaks:"))

        self.makePeakTable((()))
        #self.peakTable.setGeometry(QtCore.QRect(20, 400, 550, 190))

        self.modeBox.currentIndexChanged.connect(self.activateFrame)
        self.setCentralWidget(self.centralwidget)
        self.resize(585, 400)
        self.show()


    def makeOptions(self):
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(20, 180, 235, 140))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frameLabels = ("Fragmentation:", "Fragment:", "Modif. Pattern:", "Modification:")
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
            label.setGeometry(QtCore.QRect(10, yPos, 95, 16))
            label.setText(self._translate(self.objectName(), labelName))
            boxes[i].setGeometry(QtCore.QRect(105, yPos - 4, 120, 26))
            boxes[i].setToolTip(toolTips[i])
            yPos += 30
            if i == 1:
                yPos += 10


    def fillComboBox(self, box, options):
        toAdjust = box.count()-len(options)
        print(box.count(),len(options), toAdjust)
        if toAdjust > 0:
            [box.removeItem(i) for i in range(len(options), len(options)+toAdjust)]
        elif toAdjust < 0:
            #print('hey',  [i for i in range(toAdjust)])
            [box.addItem("") for i in range(-1*toAdjust)]
        for i, option in enumerate(options):
            box.setItemText(i, self._translate(self.objectName(), option))


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
            self.fillComboBox(self.fragmentBox, self._controller.getFragItems(self.fragmentationBox.currentText()))

    def getModValues(self):
        if (self.modPatternBox.currentText() != "") and (self.modPatternBox.currentText() != "-"):
            self.fillComboBox(self.modifBox, self._controller.getModifItems(self.modPatternBox.currentText()))

    def calculateIsotopePattern(self):
        if self.inputForm.text() == '':
            return
        try:
            charge = int(self.charge.text())
            self._intensity = self._ionTable.getIntensity()
            isotopePattern, peaks = self._controller.calculate(self.inputForm.text(),charge, self._intensity)
        except UnvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        self.spectrumView = TheoSpectrumView(self.centralwidget,(),isotopePattern)
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
        self.makeIonTable((isotopePattern['m/z'][0],abs(charge), self._intensity,"-", 0))
        hight = self.makePeakTable(peaks)
        self.resize(585, 420+hight+30)
        #self.peakTable.show()

    def makeIonTable(self, ion):
        self._ionTable = IsoPatternIon(self.centralwidget,(ion,),335)
        self._ionTable.resize(550,50)
        self._ionTable.resizeColumnsToContents()
        self._ionTable.show()

    def makePeakTable(self, peaks):
        self.peakTable = IsoPatternPeakWidget(self.centralwidget, peaks)
        hight = len(peaks) * 21 + 28
        if hight>400:
            hight=400
        self.peakTable.setGeometry(QtCore.QRect(20, 420, 550, hight)) #290
        self.peakTable.resizeColumnsToContents()
        self.peakTable.show()
        return hight
    #def formatSpectrumView(self):
     #   self.spectrumView.setGeometry(QtCore.QRect(320, 35, 250, 235))
