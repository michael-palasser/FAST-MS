import copy

from PyQt5 import QtWidgets, QtCore
import numpy as np

from src.MolecularFormula import MolecularFormula
from src.Services import *
from src.entities.AbstractEntities import AbstractItem1
from src.entities.GeneralEntities import Sequence
from src.entities.Ions import FragmentIon, Fragment
from src.gui.IonTableWidget import IsoPatternIon
from src.gui.ResultView import IsoPatternPeakWidget
from src.gui.SpectrumView import TheoSpectrumView
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
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
        self._ion = None
        self._neutralMass = None

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
                self._fragService.getPatternWithObjects(fragmentationName).getItems2()][1:]


    def getModifItems(self, modifPatternName):
        return [modTemplate.getName() for modTemplate in
                self._modService.getPatternWithObjects(modifPatternName).getItems()]

    def getIon(self):
        return self._ion

    def getNeutralMass(self):
        return self._neutralMass

    def calculate(self, mode, inputString, charge, radicals, intensity, *args):
        if mode == self.getMolecules()[0]:
            fragment = Fragment('-',0,'',MolecularFormula(self.checkFormula(inputString)),[],radicals)
        else:
            fragment = self.getFormula(mode, inputString, args[0], args[1], args[2], args[3], args[4])
        if fragment.formula != self._formula:
            self._formula = fragment.formula
            #self._fragment = fragment
            if self._formula.calcIsotopePatternSlowly(1)['m/z'][0]>6000:
                self._isotopePattern = self._formula.calculateIsotopePattern()
            else:
                self._isotopePattern = self._formula.calcIsotopePatternSlowly()
        isotopePattern = copy.deepcopy(self._isotopePattern)
        isotopePattern['calcInt'] *= intensity
        self._neutralMass = isotopePattern['m/z'][0]
        isotopePattern['m/z'] = SpectrumHandler.getMz(isotopePattern['m/z'],charge,radicals)
        peaks = []
        for row in isotopePattern:
            peaks.append((row['m/z'],0,round(row['calcInt']),1))
        peaks = np.array(peaks, dtype=self._peakDtype)
        self._ion = FragmentIon(fragment, np.min(peaks['m/z']), charge, peaks,0)
        self._ion.quality = 0
        return self._ion, self._neutralMass

    def checkFormula(self,formulaString):
        formula = AbstractItem1.stringToFormula(formulaString,{},1)
        if formula == {}:
            raise UnvalidInputException(formulaString, ", Unvalid format")
        for key in formula.keys():
            if key not in self._elements:
                print("Element: " + key + " unknown")
                raise UnvalidInputException(formulaString, ", Element: " + key + " unknown")
        return formula

    def getFormula(self, molecule, sequString, fragmentationName, fragTemplName, modifPatternName, modifName, nrMod):
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
            species = 'intact'
            number = 0
            rest = fragTempl.getName()
        else:
            fragTempl = [fragTempl for fragTempl in fragmentation.getItems() if fragTempl.getName()==fragTemplName][0]
            species, rest = FragmentLibraryBuilder.processTemplateName(fragTempl.getName())
            number = len(sequenceList)
        formula = formula.addFormula(fragTempl.getFormula())
        if modifPatternName != '-' and nrMod != 0:
            modPattern = self._modService.getPatternWithObjects(modifPatternName)
            modif = [modif for modif in modPattern.getItems() if modif.getName()==modifName][0]
            formula = formula.addFormula({key:val*nrMod for key,val in modif.getFormula().items()})
            if nrMod != 1:
                rest+=str(nrMod)
            rest+=modifName
        return Fragment(species, number, rest, formula, sequenceList, fragTempl.getRadicals())

    def model(self, peaks):
        peakArr = np.array(peaks, dtype=self._peakDtype)
        if np.all(peakArr['relAb']==0):
            raise UnvalidInputException('All Intensities = 0', '')
        self._ion.isotopePattern, self._ion.intensity, self._ion.quality =  self._intensityModeller.modelSimply(peakArr)
        return self._ion


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
        self._vertLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self._upperW =QtWidgets.QWidget(self.centralwidget)

        self.inputForm = QtWidgets.QLineEdit(self._upperW)
        self.inputForm.setGeometry(QtCore.QRect(15, 20, 185, 21))
        self.inputForm.returnPressed.connect(self.calculateIsotopePattern)

        modeLabel = QtWidgets.QLabel(self._upperW)
        modeLabel.setGeometry(QtCore.QRect(250, 20, 60, 16))
        modeLabel.setText(self._translate(self.objectName(), "Mode:"))
        self.modeBox = QtWidgets.QComboBox(self._upperW)
        self.modeBox.setGeometry(QtCore.QRect(290, 17, 120, 26))
        self.fillComboBox(self.modeBox, self._controller.getMolecules())

        chargeLabel = QtWidgets.QLabel(self._upperW)
        chargeLabel.setGeometry(QtCore.QRect(15, 60, 60, 16))
        chargeLabel.setText(self._translate(self.objectName(), "Charge:"))
        self.charge = QtWidgets.QSpinBox(self._upperW)
        self.charge.setGeometry(QtCore.QRect(70, 57, 50, 24))
        self.charge.setMinimum(-99)
        self.charge.valueChanged.connect(self.calculateIsotopePattern)
        radicalLabel = QtWidgets.QLabel(self._upperW)
        radicalLabel.setGeometry(QtCore.QRect(130, 60, 60, 16))
        radicalLabel.setText(self._translate(self.objectName(), "Radicals:"))
        self.radicals = QtWidgets.QSpinBox(self._upperW)
        self.radicals.setGeometry(QtCore.QRect(190, 57, 40, 24))
        self.radicals.setMinimum(-9)
        self.radicals.setMaximum(9)
        self.radicals.valueChanged.connect(self.calculateIsotopePattern)

        self.pushCalc = self.makeBtn(60, 100, "Calculate")
        self.pushCalc.clicked.connect(self.calculateIsotopePattern)
        self.pushModel = self.makeBtn(140, 100, "Model")
        self.pushModel.clicked.connect(self.modelInt)
        self.makeOptions()

        self.spectrumView = QtWidgets.QFrame(self._upperW)

        self.spectrumView.setGeometry(QtCore.QRect(250, 50, 350, 280))
        self.spectrumView.setFrameShape(QtWidgets.QFrame.StyledPanel)
        # self.spectrumView.setFrameShadow(QtWidgets.QFrame.Raised)
        self.spectrumView.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.spectrumView.setStyleSheet('background-color: white')
        self._vertLayout.addWidget(self._upperW)
        self._vertLayout.addSpacing(10)
        self.makeIonTable(None, None)
        #self._vertLayout.addWidget(self._ionTable)
        self._spaceItem = QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Expanding)
        self._vertLayout.addItem(self._spaceItem)
        print(self._vertLayout.indexOf(self._ionTable))
        # self.ionTable.setGeometry(QtCore.QRect(20, 335, 550, 50))
        self._peakLabel = QtWidgets.QLabel(self.centralwidget)
        self._peakLabel.setGeometry(QtCore.QRect(25, 415, 60, 16))
        self._peakLabel.setText(self._translate(self.objectName(), "Peaks:"))
        self._vertLayout.addWidget(self._peakLabel)
        print(self._vertLayout.indexOf(self._peakLabel))
        self.makePeakTable((()))
        #self._vertLayout.addWidget(self.peakTable)
        print(self._vertLayout.indexOf(self.peakTable))
        # self.peakTable.setGeometry(QtCore.QRect(20, 400, 550, 190))

        self.modeBox.currentIndexChanged.connect(self.activateFrame)
        width = 615
        self._upperW.setGeometry(QtCore.QRect(0,0,width,335))
        self._upperW.setMinimumHeight(325)
        #self._vertLayout.addWidget(self._upperW)
        #self._vertLayout.addWidget(self._ionTable)
        #self._vertLayout.addWidget(self._peakLabel)
        #self._vertLayout.addWidget(self.peakTable)
        self.centralwidget.setLayout(self._vertLayout)
        self.setCentralWidget(self.centralwidget)
        self.setGeometry(QtCore.QRect(100,50,width, 400))
        self.show()



    def makeOptions(self):
        self.frame = QtWidgets.QFrame(self._upperW)
        self.frame.setGeometry(QtCore.QRect(15, 155, 220, 170))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        frameLabels = ("Fragmentation:", "Fragment:", "Modif.Pattern:", "Modification:", "Nr.of Mod.:")
        self.fragmentationBox = QtWidgets.QComboBox(self.frame)
        self.fragmentBox = QtWidgets.QComboBox(self.frame)
        self.fragmentationBox.currentIndexChanged.connect(self.getFragValues)
        self.modPatternBox = QtWidgets.QComboBox(self.frame)
        self.modPatternBox.currentIndexChanged.connect(self.getModValues)
        self.modifBox = QtWidgets.QComboBox(self.frame)
        self.nrOfMods = QtWidgets.QSpinBox(self.frame)
        self.fillFrame(frameLabels, (self.fragmentationBox, self.fragmentBox,
                                     self.modPatternBox, self.modifBox, self.nrOfMods),
                       ("", "", "", "", ''))
        #self.boxes = (self.fragmentationBox, self.modPatternBox, self.fragmentBox, self.modifBox)
        self.frame.hide()

    def makeBtn(self,xPos, yPos, name):
        btn = QtWidgets.QPushButton(self._upperW)
        btn.setGeometry(QtCore.QRect(xPos-int(81/2), yPos, 81, 32))
        btn.setText(self._translate(self.objectName(), name))
        return btn

    def fillFrame(self, labelNames, widgets, toolTips):
        yPos = 10
        for i, labelName in enumerate(labelNames):
            label = QtWidgets.QLabel(self.frame)
            label.setGeometry(QtCore.QRect(10, yPos, 90, 16))
            label.setText(self._translate(self.objectName(), labelName))
            widgets[i].setGeometry(QtCore.QRect(100, yPos - 4, 120, 26))
            widgets[i].setToolTip(toolTips[i])
            yPos += 30
            if i == 1:
                yPos += 10


    def fillComboBox(self, box, options, *args):
        #[box.removeItem(i) for i in range(box.count())]
        #box.item
        #box.rem
        [box.model().item(i).setEnabled(True) for i in range(box.count())]
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
            #box.insertSeparator(lastIndex)
            #box.setItemText(lastIndex+1, self._translate(self.objectName(), 'intact'))
            box.setItemText(lastIndex, self._translate(self.objectName(), ''))
            box.model().item(lastIndex).setEnabled(False)
            lastIndex += 1
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
                ion, neutralMass= self._controller.calculate(self.modeBox.currentText(),
                                            self.inputForm.text(), charge, int(self.radicals.text()), self._intensity)
            else:
                ion, neutralMass= self._controller.calculate(self.modeBox.currentText(),
                                self.inputForm.text(), charge, int(self.radicals.text()), self._intensity,
                                self.fragmentationBox.currentText(), self.fragmentBox.currentText(),
                                self.modPatternBox.currentText(), self.modifBox.currentText(), self.nrOfMods.value())
        except UnvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        self.restartView(ion, neutralMass)
        '''self.restartView((ion.isotopePattern['m/z'][0],abs(charge), self._intensity,"-", 0.,ion.formula,
                          neutralMass), ion.isotopePattern)'''
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

    def restartView(self, ion, neutralMass):
        self.spectrumView.hide()
        del self.spectrumView
        self.spectrumView = TheoSpectrumView(self.centralwidget, ion.isotopePattern, 365)
        self.spectrumView.setGeometry(QtCore.QRect(250, 50, 365, 300))
        #self.spectrumView.setGeometry(QtCore.QRect(250, 50, 350, 280))
        self.peakTable.hide()
        self._ionTable.hide()
        print('ion',self._vertLayout.indexOf(self._ionTable))
        #self._vertLayout.removeWidget(self._ionTable)
        #self._vertLayout.removeWidget(self.peakTable)
        print('label',self._vertLayout.indexOf(self._peakLabel))
        print('peak',self._vertLayout.indexOf(self.peakTable))
        #self._vertLayout.removeWidget(self._peakLabel)
        del self.peakTable
        del self._ionTable
        self.makeIonTable(ion, neutralMass)
        #self._vertLayout.addSpacing(10)
        self._vertLayout.insertItem(3, self._spaceItem)
        self._vertLayout.insertWidget(4, self._peakLabel)
        #self._vertLayout.insertWidget(2, self._ionTable)
        #self._vertLayout.addSpacing(10)
        #self._vertLayout.addWidget(self._peakLabel)
        hight = self.makePeakTable(ion.isotopePattern)
        #self._vertLayout.insertWidget(5, self.peakTable)
        self.resize(615, 420 + hight + 30)

    #def getIonVals(self, ion, neutralMass):
    #    return (ion.isotopePattern['m/z'][0], abs(ion.charge), self._intensity, "-", 0., ion.formula, neutralMass)

    def makeIonTable(self, ion, neutralMass):
        vals = ()
        if ion != None:
            vals = (ion.isotopePattern['m/z'][0], abs(ion.charge), self._intensity, ion.getName(), ion.quality,
                    ion.formula.toString(), neutralMass)
        self._ionTable = IsoPatternIon(self.centralwidget, (vals,), 0)
        #self._ionTable.setGeometry(QtCore.QRect(15, 0, 585, 49))
        self._ionTable.resizeColumnsToContents()
        self._vertLayout.insertWidget(2,self._ionTable)
        print('ion',self._vertLayout.indexOf(self._ionTable))
        #self._vertLayout.addWidget(self._ionTable)
        self._ionTable.show()

    def makePeakTable(self, peaks):
        self.peakTable = IsoPatternPeakWidget(self.centralwidget, peaks)
        hight = len(peaks) * 21 + 28
        if hight>400:
            hight=400
        #self.peakTable.setGeometry(QtCore.QRect(50, 440, 450, hight)) #290
        self.peakTable.resizeColumnsToContents()
        #self._vertLayout.addWidget(self.peakTable)
        self._vertLayout.insertWidget(5,self.peakTable)
        print('peak',self._vertLayout.indexOf(self.peakTable))
        self.peakTable.show()
        return hight


    def modelInt(self):
        inputVals = sorted(self.peakTable.readTable(), key=lambda tup:tup[2])
        peaks = []
        for i, peak in enumerate(self.peakTable.getPeaks()):
            peaks.append((peak[0],inputVals[i][0], peak[2], inputVals[i][1]))
        try:
            ion = self._controller.model(peaks)
            self._intensity = round(ion.intensity)
        except UnvalidInputException as e:
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            return
        #ionVals = list(self._ionTable.getIon(0))
        #ionVals[2] = round(self._intensity)
        #ionVals[4] = quality
        self.restartView(ion, self._controller.getNeutralMass())