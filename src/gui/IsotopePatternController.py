from PyQt5 import QtWidgets, QtCore, Qt

from src.MolecularFormula import MolecularFormula
from src.Services import *
from src.entities.AbstractEntities import AbstractItem1


class IsotopePatternController(object):
    def __init__(self, parent):
        moleculeService = MoleculeService()
        self._fragService = FragmentIonService()
        self._modService = ModificationService()
        self._elements = PeriodicTableService().getAllPatternNames()
        self._moleculeNames = moleculeService.getAllPatternNames()
        #self._fragmentationNames = self._fragService.getAllPatternNames()
        #self._modifNames = self._modService.getAllPatternNames()
        '''self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        self.__fragmentation = FragmentIonService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModifiedItem)'''
        self._view = IsotopePatternView(parent, ['mol. formula']+self._moleculeNames,
                self._fragService.getAllPatternNames(), self._modService.getAllPatternNames(),
                self._fragService.getPatternWithObjects, self._modService.getPatternWithObjects,
                                        self.calculate)
        #self._view.modeBox.currentIndexChanged.connect(self.activateFrame)
        print(self._view.modeBox.currentText())
        #self._view.fragmentationBox.currentTextChanged.connect(self.changeFragValues)
        #self._view.modPatternBox.currentTextChanged.connect(self.changeModValues)

    '''@staticmethod
    def changeFragValues(self, box):
        if self._view.fragmentationBox.currentText() != "":
            self._fragmentation = self._fragService.getPatternWithObjects(self._view.fragmentationBox.currentText())
            self._view.fillComboBox(self._view.fragmentBox,
                                [fragTemplate.getName() for fragTemplate in self._fragmentation.getItems()])

    def changeModValues(self):
        if self._view.modPatternBox.currentText() != "":
            self._modifPattern = self._modService.getPatternWithObjects(self._view.modPatternBox.currentText())
            self._view.fillComboBox(self._view.modifBox,
                                [modifTemplate.getName() for modifTemplate in self._modifPattern.getItems()])'''


    def calculate(self, formulaString, view):
        print('hey')
        #formulaString = self._view.inputForm.text()
        if formulaString == '':
            return
        try:
            formula = self.checkFormula(formulaString)
        except UnvalidInputException as e:
            QtWidgets.QMessageBox.warning(view, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        formula = MolecularFormula(formula)
        isotopePattern = formula.calcIsotopePatternSlowly()
        print(isotopePattern)

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
    def __init__(self, parent, modeOptions, fragmentationOptions, modPatternOption, getFrags, getModifs, getIsoPattern):
        super(IsotopePatternView, self).__init__(parent)
        self._fragmentationOpts = fragmentationOptions
        self._modifPatternOpts = modPatternOption
        self.getFrags = getFrags
        self.getModifs = getModifs
        self.getIsoPattern = getIsoPattern

        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), 'Isotope Pattern Tool'))
        self.resize(610, 625)
        self.centralwidget = QtWidgets.QWidget(self)

        self.inputForm = QtWidgets.QLineEdit(self.centralwidget)
        self.inputForm.setGeometry(QtCore.QRect(15, 30, 185, 21))

        modeLabel = QtWidgets.QLabel(self.centralwidget)
        modeLabel.setGeometry(QtCore.QRect(15, 70, 60, 16))
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        self.modeBox = QtWidgets.QComboBox(self.centralwidget)
        self.modeBox.setGeometry(QtCore.QRect(80, 67, 120, 26))
        self.fillComboBox(self.modeBox, modeOptions)

        chargeLabel = QtWidgets.QLabel(self.centralwidget)
        chargeLabel.setGeometry(QtCore.QRect(15, 100, 60, 16))
        chargeLabel.setText(self._translate(self.objectName(), "Charge:"))
        self.charge = QtWidgets.QSpinBox(self.centralwidget)
        self.charge.setGeometry(QtCore.QRect(85, 98, 70, 24))
        self.charge.setMinimum(-99)

        self.pushCalc = self.makeBtn(26, "Calculate")
        self.pushCalc.clicked.connect(lambda:getIsoPattern(self.inputForm.text(),self))
        self.pushModel = self.makeBtn(66, "Model")
        self.makeOptions()

        self.spectrumView = QtWidgets.QFrame(self.centralwidget)
        self.spectrumView.setGeometry(QtCore.QRect(320, 35, 250, 235))
        self.spectrumView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.spectrumView.setFrameShadow(QtWidgets.QFrame.Raised)
        #self.spectrumView.setAutoFillBackground(True)
        self.spectrumView.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.spectrumView.setStyleSheet('background-color: white')

        self.ionTable = QtWidgets.QTableWidget(self.centralwidget)
        self.ionTable.setGeometry(QtCore.QRect(20, 305, 550, 50))
        self.peakTable = QtWidgets.QTableWidget(self.centralwidget)
        self.peakTable.setGeometry(QtCore.QRect(20, 370, 550, 190))

        self.modeBox.currentIndexChanged.connect(self.activateFrame)
        self.setCentralWidget(self.centralwidget)
        self.show()


    def makeOptions(self):
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(20, 140, 270, 145))
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
        self.boxes = (self.fragmentationBox, self.modPatternBox, self.fragmentBox, self.modifBox)
        self.frame.hide()

    def makeBtn(self, yPos, name):
        btn = QtWidgets.QPushButton(self.centralwidget)
        btn.setGeometry(QtCore.QRect(220, yPos, 81, 32))
        btn.setText(self._translate(self.objectName(), name))
        return btn

    def fillFrame(self, labelNames, boxes, toolTips):
        yPos = 15
        for i, labelName in enumerate(labelNames):
            label = QtWidgets.QLabel(self.frame)
            label.setGeometry(QtCore.QRect(15, yPos, 95, 16))
            label.setText(self._translate(self.objectName(), labelName))
            boxes[i].setGeometry(QtCore.QRect(120, yPos - 4, 135, 26))
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
        print('hey')
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
            fragmentation = self.getFrags(self.fragmentationBox.currentText())
            self.fillComboBox(self.fragmentBox, [fragTemplate.getName() for fragTemplate in fragmentation.getItems()])

    def getModValues(self):
        if (self.modPatternBox.currentText() != "") and (self.modPatternBox.currentText() != "-"):
            modifPattern = self.getModifs(self.modPatternBox.currentText())
            self.fillComboBox(self.modifBox, [modTemplate.getName() for modTemplate in modifPattern.getItems()])