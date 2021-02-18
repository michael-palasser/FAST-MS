from PyQt5 import QtWidgets, QtCore, Qt

from src.Services import *
from src.entities.AbstractEntities import AbstractItem1


class IsotopePatternController(object):
    def __init__(self, parent):
        moleculeService = MoleculeService()
        self._fragService = FragmentIonService()
        self._modService = ModificationService()
        self._elements = PeriodicTableService().getAllPatternNames()
        self._moleculeNames = moleculeService.getAllPatternNames()
        self._fragmentationNames = self._fragService.getAllPatternNames()
        self._modifNames = self._modService.getAllPatternNames()
        '''self.__molecule = MoleculeService().getPatternWithObjects(self.__sequence.getMolecule(), BuildingBlock)
        self.__fragmentation = FragmentIonService().getPatternWithObjects(fragmentation, FragItem)
        self.__modifPattern = ModificationService().getPatternWithObjects(modificationPattern, ModifiedItem)'''
        self._view = IsotopePatternView(parent, ['mol. formula']+self._moleculeNames)
        self._view.modeBox.currentIndexChanged.connect(self.activateFrame)
        print(self._view.modeBox.currentText())
        self._view.fragmentationBox.currentTextChanged.connect(self.changeFragValues)
        self._view.modPatternBox.currentTextChanged.connect(self.changeModValues)

    def activateFrame(self):
        print('hey')
        if self._view.modeBox.currentIndex() == 0:
            for box in self._view.boxes:
                self._view.fillComboBox(box, [""])
        else:
            self._view.fillComboBox(self._view.fragmentationBox, self._fragmentationNames)
            self._view.fillComboBox(self._view.modPatternBox, self._modifNames)


    def changeFragValues(self):
        if self._view.fragmentationBox.currentText() != "":
            self._fragmentation = self._fragService.getPatternWithObjects(self._view.fragmentationBox.currentText())
            self._view.fillComboBox(self._view.fragmentBox,
                                [fragTemplate.getName() for fragTemplate in self._fragmentation.getItems()])

    def changeModValues(self):
        if self._view.modPatternBox.currentText() != "":
            self._modifPattern = self._fragService.getPatternWithObjects(self._view.modPatternBox.currentText())
            self._view.fillComboBox(self._view.modifBox,
                                [modifTemplate.getName() for modifTemplate in self._modifPattern.getItems()])


    def calculate(self, formulaString):
        formula = AbstractItem1.stringToFormula(formulaString,{},1)
        try:
            for key in formula.keys():
                if key not in self._elements:
                    print("Element: " + key + " unknown")
                    raise UnvalidInputException(formulaString, ", Element: " + key + " unknown")
        except UnvalidInputException:
            return



class IsotopePatternView(QtWidgets.QMainWindow):
    def __init__(self, parent, modeOptions):
        super(IsotopePatternView, self).__init__(parent)
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
        self.setCentralWidget(self.centralwidget)
        self.show()

    def makeOptions(self):
        frame = QtWidgets.QFrame(self.centralwidget)
        frame.setGeometry(QtCore.QRect(20, 140, 270, 145))
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frameLabels = ("Fragmentation:", "Fragment:", "Modif. Pattern:", "Modification:")
        self.fragmentationBox = QtWidgets.QComboBox(frame)
        self.fragmentBox = QtWidgets.QComboBox(frame)
        self.modPatternBox = QtWidgets.QComboBox(frame)
        self.modifBox = QtWidgets.QComboBox(frame)
        self.fillFrame(frame, frameLabels, (self.fragmentationBox, self.fragmentBox, self.modPatternBox, self.modifBox),
                       ("", "", "", ""))
        self.boxes = (self.fragmentationBox, self.modPatternBox, self.fragmentBox, self.modifBox)
        return frame


    def makeBtn(self, yPos, name):
        btn = QtWidgets.QPushButton(self.centralwidget)
        btn.setGeometry(QtCore.QRect(220, yPos, 81, 32))
        btn.setText(self._translate(self.objectName(), name))
        return btn

    def fillFrame(self, frame, labelNames, boxes, toolTips):
        yPos = 15
        for i, labelName in enumerate(labelNames):
            label = QtWidgets.QLabel(frame)
            label.setGeometry(QtCore.QRect(15, yPos, 95, 16))
            label.setText(self._translate(self.objectName(), labelName))
            boxes[i].setGeometry(QtCore.QRect(120, yPos - 4, 135, 26))
            boxes[i].setToolTip(toolTips[i])
            yPos += 30
            if i == 1:
                yPos += 10


    def fillComboBox(self, box, options):
        for i, option in enumerate(options):
            box.addItem("")
            box.setItemText(i, self._translate(self.objectName(), option))