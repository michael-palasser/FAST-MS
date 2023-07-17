
from PyQt5 import QtWidgets, QtCore
from src.Exceptions import InvalidInputException
from src.services.MolecularFormula import MolecularFormula

from src.gui.GUI_functions import createComboBox
from src.gui.tableviews.TableModels import AbstractTableModel
from src.gui.tableviews.TableViews import TableView
from src.services.DataServices import MoleculeService

"""class SequenceTranslater(object):
    def __init__(self):
        #super().__init__(None, "SequenceTranslater")
        #self._libraryBuilder = IntactLibraryBuilder()
        self._service = SequenceTranslaterLogics()
        openDialog = OpenDialog("Molecule", self._service.getAllMoleculeNames())
        openDialog.show()
        if openDialog.exec_() and openDialog.accepted:
            moleculeName = openDialog.getName()
            self._window = SequenceTranslaterWindow(self._service.getBBs(moleculeName))"""

class SequenceTranslaterWindow(QtWidgets.QDialog):
    def __init__(self):
        self._service = SequenceTranslaterLogics()
        self._moleculeNames = self._service.getAllMoleculeNames()
        self._service.setMolecule(self._moleculeNames[0])
        super().__init__(None)
        self.setWindowTitle("SequenceTranslater")
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.makeUpperWidget(),1)
        
        lowerWidget= QtWidgets.QWidget(self)
        QtWidgets.QHBoxLayout(lowerWidget)
        self.makeLeftWidget(lowerWidget)
        self.makeRightWidget(lowerWidget, self._service.getBBs())
        layout.addWidget(lowerWidget,20)
        if self._moleculeNames[0].startswith("P"):
            self._widgets[1].setCurrentIndex(0)
        else:
            self._widgets[1].setCurrentIndex(1)
        self.show()
    
    def makeUpperWidget(self):
        upperWidget= QtWidgets.QWidget(self)
        upperLayout = QtWidgets.QVBoxLayout(upperWidget)
        self._inputWidgets = []
        for label in ("Input Sequence", "Output Sequence"):
            label = QtWidgets.QLabel(label,upperWidget)
            upperLayout.addWidget(label)
            lineEdit = QtWidgets.QLineEdit(upperWidget)
            self._inputWidgets.append(lineEdit)
            upperLayout.addWidget(lineEdit)
        #self._inputWidgets[1].setEnabled(False)
        return upperWidget

    def makeLeftWidget(self, parent):
        leftWidget = QtWidgets.QWidget(parent)
        formLayout = QtWidgets.QFormLayout(leftWidget)
        labels = ("Molecule:", "Mode:","Molecular Formula:", "Monoisotopic Mass:")
        self._widgets = (createComboBox(leftWidget,self._service.getAllMoleculeNames()),
                         createComboBox(leftWidget,("3-Letter", "HELM")),
                         QtWidgets.QLabel(leftWidget),
                         QtWidgets.QLabel(leftWidget))
                         
        """for widget in self._widgets:
            leftLayout.addWidget(widget)"""
        button = QtWidgets.QPushButton("Translate" ,leftWidget)
        formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, button)
        button.pressed.connect(self.translate)
        formLayout.addItem(QtWidgets.QSpacerItem(0, 10))
        for i, label in enumerate(labels[:2]):
            
            formLayout.setWidget(i+2, QtWidgets.QFormLayout.LabelRole, QtWidgets.QLabel(label,leftWidget))
            self._widgets[i].setToolTip("")
            #self._widgetSizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
            #widget.setSizePolicy(self._widgetSizePolicy)
            #self._widgets[widgetName] = widget
            formLayout.setWidget(i+2, QtWidgets.QFormLayout.FieldRole, self._widgets[i])
        formLayout.addItem(QtWidgets.QSpacerItem(0, 10))
        
        for i, label in enumerate(labels[2:]):
            formLayout.setWidget(i+5, QtWidgets.QFormLayout.LabelRole, QtWidgets.QLabel(label,leftWidget))
            self._widgets[i+2].setToolTip("")
            #self._widgetSizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
            #widget.setSizePolicy(self._widgetSizePolicy)
            #self._widgets[widgetName] = widget
            self._widgets[i+2].setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)#Qt::TextSelectableByMouse
            formLayout.setWidget(i+5, QtWidgets.QFormLayout.FieldRole, self._widgets[i+2])
        parent.layout().addWidget(leftWidget)
        self._widgets[0].currentIndexChanged.connect(self.updateRightWidget)
        

    def makeRightWidget(self, parent, buildingBlocks):
        scrollArea = QtWidgets.QScrollArea(parent)
        layout = QtWidgets.QVBoxLayout(scrollArea)

        tableModel = BuildingBlockTable(buildingBlocks)

        self._table = TableView(scrollArea, tableModel)
        self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self._table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self._table.resizeRowsToContents()
        self._table.resizeColumnsToContents()
        layout.addWidget(self._table)
        parent.layout().addWidget(scrollArea)
        scrollArea.setWidgetResizable(True)
        return scrollArea

    def updateRightWidget(self):
        moleculeName = self._widgets[0].currentText()
        self._service.setMolecule(moleculeName)
        self._table.model().setData(self._service.getBBs())
        if moleculeName.startswith("P"):
            self._widgets[1].setCurrentIndex(0)
        else:
            self._widgets[1].setCurrentIndex(1)

    def translate(self):
        input = self._inputWidgets[0].text()
        if input !="":
            try:
                if self._widgets[1].currentIndex() == 1:
                    translated = self._service.translateHELM(input)
                else:
                    translated = self._service.translatePeptide(input)
                self._inputWidgets[1].setText("".join(translated))
                formula, monoisotopic = self._service.calculateProperties(translated)
                self._widgets[2].setText(formula)
                self._widgets[3].setText(str(round(monoisotopic,4)))
            except InvalidInputException as e:
                QtWidgets.QMessageBox.warning(self, "Building Block not Found", e.__str__(), QtWidgets.QMessageBox.Ok)


class BuildingBlockTable(AbstractTableModel):
    def __init__(self, data):
        super().__init__(data, ('','',''), ("name", "translation","formula"))
    
    def data(self, index, role):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return self._data[index.row()][index.column()]


class SequenceTranslaterLogics(object):
    def __init__(self) -> None:
        self._moleculeService = MoleculeService()
        self._molecule = None

    def setMolecule(self, moleculeName):
        self._molecule = self._moleculeService.getPatternWithObjects(moleculeName)

    def getAllMoleculeNames(self):
        return self._moleculeService.getAllPatternNames()

    def getBBs(self):
        self._buildingBlocks = self._molecule.getItems()
        bbList = []
        for bb in self._buildingBlocks:
            """formula = ""
            for key, val in bb.getFormula():
                [formula+key+str(val)""]"""
            bbList.append([bb.getName(), bb.getTranslation(), bb.getFormulaString()])
           #bbList.append((vbb.getName(), bb.getTranslation(), "".join([key,bb.getFormula()])))
        return bbList

        
    def translateHELM(self, helmString):
        if (helmString[0]=='{') and (helmString[-1]=='}'):
            bbList = helmString[1:-1].split(".")
        else:
            bbList = helmString.split(".")
        if "P" not in bbList[-1]:
            bbList[-1] = bbList[-1]+"P"
        return self.translate(bbList)

    def translatePeptide(self, threeLetterString):
        bbList = threeLetterString.split("-")
        correctedBBList = bbList[1:-1]
        if bbList[0] != "H":
            correctedBBList[0] += "_"+bbList[0]
        if bbList[-1] != "OH":
            correctedBBList[-1] += "_"+bbList[-1]
        return self.translate(correctedBBList)
    
    def translate(self, bbList):
        d = {}
        for bb in self._molecule.getItems():
            d[bb.getTranslation()] = bb.getName()
        translated = []
        for bb in bbList:
            if bb in d.keys():
                translated.append(d[bb])
            else:
                raise InvalidInputException("Building Block not found", bb)
        return translated
    
    def calculateProperties(self, sequenceList):
        formula = MolecularFormula(self._molecule.getFormula())
        d = self._molecule.getBBDict()
        for link in sequenceList:
            formula = formula.addFormula(d[link].getFormula())
        return formula.toString(), formula.calculateMonoIsotopic()