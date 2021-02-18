import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog
from os.path import join, isfile, isdir

from src import path
from src.Exceptions import UnvalidInputException
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.Services import FragmentIonService, ModificationService, SequenceService
from src.gui.StartDialogs import OpenFileWidget

dataPath = join(path, 'src', 'data')



class AbstractDialog(QDialog):
    def __init__(self, parent, title, lineSpacing, widgetWidth):
        super().__init__(parent)
        self.setObjectName(title)
        self.lineSpacing = lineSpacing
        self.widgetWidth = widgetWidth
        self.widgets = dict()
        self.labels = dict()
        #self.formLayout = QtWidgets.QVBoxLayout(self)
        self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.newSettings = None
        self.move(300,100)
        self.canceled = False

    @staticmethod
    def setNewSizePolicy(horizontal, vertical):
        sizePolicy = QtWidgets.QSizePolicy(horizontal, vertical)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        return sizePolicy


    def createLabels(self, labels, widgets, parent):
        yPos = 30
        maxWidth = 0
        self.labels = {widget[1]:labelName for widget, labelName in zip(widgets,labels)}
        for i, labelName in enumerate(labels):
            label = QtWidgets.QLabel(parent)
            width = len(labelName)*7
            label.setGeometry(QtCore.QRect(20, yPos, width, 16))
            label.setText(self._translate(self.objectName(), labelName))
            if width>maxWidth:
                maxWidth = width
            yPos += self.lineSpacing
        return maxWidth+20


    def createWidgets(self, widgetTuples, xPos):
        """

        :param widgetTuples: (widget,name,toolTip)
        :param xPos:
        :param lineWidth:
        :return:
        """
        yPos = 30
        for i, widgetTuple in enumerate(widgetTuples):
            widget = widgetTuple[0]
            if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.setGeometry(QtCore.QRect(xPos, yPos-4, self.widgetWidth, 24))
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.setGeometry(QtCore.QRect(xPos, yPos-2, self.widgetWidth, 21))
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.setGeometry(QtCore.QRect(xPos - 5, yPos, self.widgetWidth + 6, 26))
            elif isinstance(widget, OpenFileWidget):
                widget.setGeometry(QtCore.QRect(xPos, yPos-10, self.widgetWidth + 20, 36))
            else:
                raise Exception('Unknown type of widget: ', type(widget))
            widget.setObjectName(widgetTuple[1])
            widget.setToolTip(self._translate(self.objectName(), widgetTuple[2]))
            self.widgets[widgetTuple[1]] = widget
            #self.formLayout.addWidget(widget)
            yPos += self.lineSpacing
        return xPos+self.widgetWidth, yPos


    def createComboBox(self, box, options):
        comboBox = QtWidgets.QComboBox(box)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), option))
        return comboBox



    @staticmethod
    def getValueOfWidget(widget):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QLineEdit) or isinstance(widget, OpenFileWidget):
            return widget.text()
        elif isinstance(widget, QtWidgets.QComboBox):
            return widget.currentText()
        else:
            raise Exception('Unknown type of widget')

    @staticmethod
    def setValueOfWidget(widget, value):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QLineEdit) or isinstance(widget, OpenFileWidget):
            widget.setText(value)
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentText(value)
        else:
            raise Exception('Unknown type of widget')


    def backToLast(self):
        if self.configHandler.getAll()!=None:
            for name, item in self.widgets.items():
                self.setValueOfWidget(item, self.configHandler.get(name))

    def reject(self):
        self.canceled = True
        super(AbstractDialog, self).reject()

    def makeDictToWrite(self):
        newSettings = dict()
        for name, item in self.widgets.items():
            newSettings[name] = self.getValueOfWidget(item)
        return newSettings


    def accept(self):
        self.ok = True
        super(AbstractDialog, self).accept()

    def checkValues(self, configs):
        pass

    def reshape(self, xPos, yPos):
        self.resize(xPos+25, yPos+70)
        QtCore.QMetaObject.connectSlotsByName(self)


class StartDialog(AbstractDialog):
    """def startProgram(self, mainMethod):
        self.makeDictToWrite()
        #try:
        mainMethod()"""
        #    super(StartDialog, self).accept()
        #except:
        #    traceback.print_exc()
         #   QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)

    def makeDefaultButton(self):
        defaultButton = QtWidgets.QPushButton(self)
        self.sizePolicy.setHeightForWidth(defaultButton.sizePolicy().hasHeightForWidth())
        defaultButton.setSizePolicy(self.sizePolicy)
        defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        defaultButton.clicked.connect(self.backToLast)
        defaultButton.setText(self._translate(self.objectName(), "last settings"))
        return defaultButton

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
        except UnvalidInputException:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)
        return newSettings

    def checkValues(self, configs, *args):
        if configs['sequName'] not in SequenceService().getAllSequenceNames():
            raise UnvalidInputException(configs['sequName'], "not found")
        if self.checkSpectralDataFile(args[0], configs['spectralData']):
            configs['spectralData'] = join(path, 'Spectral_data', args[0], configs['spectralData'])
        return configs


    def checkSpectralDataFile(self, mode, fileName):
        #spectralDataPath = join(path, 'Spectral_data',mode, fileName)
        if not isfile(fileName):
            spectralDataPath = join(path, 'Spectral_data', mode, fileName)
            if isfile(spectralDataPath):
                return True
            else:
                raise UnvalidInputException(spectralDataPath, "not found")
        return False


class TDStartDialog(StartDialog):
    def __init__(self, parent):
        super().__init__(parent, "Settings", 30, 180)
        self.configHandler = ConfigurationHandlerFactory.getTD_SettingHandler()
        self.setupUi(self)

    def setupUi(self, startDialog):
        """self.createLabels(("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "Nr. of Modifications:",
                           "Spectral Data:", "Noise Threshold (x10^6):", "Fragment Library:", "Output"),
                          startDialog, 30, 160)"""
        fragPatterns = FragmentIonService().getAllPatternNames()
        modPatterns = ModificationService().getAllPatternNames()
        sequences = SequenceService().getAllSequenceNames()
        labelNames = ("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "Nr. of Modifications:",
         "Spectral Data:", "Noise Threshold (x10^6):", "Fragment Library:")
        widgets = ((self.createComboBox(startDialog,sequences), "sequName", "Name of the sequence"),
               (QtWidgets.QSpinBox(startDialog), "charge","Charge of the precursor ion"),
               (self.createComboBox(startDialog,fragPatterns), "fragmentation", "Name of the fragmentation - pattern"),
               (self.createComboBox(startDialog,modPatterns), "modifications", "Name of the modification/ligand - pattern"),
               (QtWidgets.QSpinBox(startDialog), "nrMod", "How often is the precursor ion modified?"),
               (OpenFileWidget(self,self.widgetWidth, 0, 1, join(path, 'Spectral_data','top-down'),  "Open File",
                               "Plain Text Files (*txt);;Comma Separated Files (*csv);;All Files (*)"),
                "spectralData","Name of the file with spectral peaks (txt or csv format)\n"
                                     "If no file is stated, the program will just calculate the fragment library"),
               (QtWidgets.QDoubleSpinBox(startDialog), 'noiseLimit', "Minimal noise level"),
               (QtWidgets.QLineEdit(startDialog), "fragLib", "Name of csv file in the folder 'Fragment_lists' "
                     "containing the isotope patterns of the fragments\n"
                     "If no file is stated, the program will search for the corresponing file or create a new one"))#,
               #(QtWidgets.QLineEdit(startDialog), "output", "Name of the output Excel file\ndefault: name of spectral pattern file + _out.xlsx")""")
        xPos = self.createLabels(labelNames,widgets, self)
        xPos, yPos = self.createWidgets(widgets, xPos + 40)
        self.widgets['charge'].setMinimum(-99)
        self.buttonBox.setGeometry(QtCore.QRect(210, yPos+20, 164, 32))
        #self.widgets['charge'].setValue(2)
        if self.configHandler.getAll() != None:
            try:
                self.widgets["fragmentation"].setCurrentText(self.configHandler.get('fragmentation'))
                self.widgets["modifications"].setCurrentText(self.configHandler.get('modifications'))
                self.widgets["nrMod"].setValue(self.configHandler.get('nrMod'))
            except KeyError:
                traceback.print_exc()
        self.defaultButton = self.makeDefaultButton()
        self.defaultButton.setGeometry(QtCore.QRect(40, yPos + 20, 113, 32))

    def backToLast(self):
        super(TDStartDialog, self).backToLast()
        self.setValueOfWidget(self.widgets['noiseLimit'], self.configHandler.get('noiseLimit') / 10**6)

    def accept(self):
        newSettings = self.getNewSettings() #self.makeDictToWrite()
        #self.checkValues(newSettings)
        newSettings['noiseLimit']*=10**6
        self.configHandler.write(newSettings)
        #self.newSettings = newSettings
        #self.startProgram(Main.run)
        super(TDStartDialog, self).accept()


    def checkValues(self, configs, *args):
        return super(TDStartDialog, self).checkValues(configs, 'top-down')

    def checkSpectralDataFile(self, mode, fileName):
        if fileName == '':
            print('Just calculating fragment library')
            return False
        else:
            super(TDStartDialog, self).checkSpectralDataFile(mode, fileName)



class OpenDialog(QtWidgets.QDialog):
    def __init__(self, title, options):
        super(OpenDialog, self).__init__()
        self._translate = QtCore.QCoreApplication.translate
        self.setObjectName("dialog")
        self.setWindowTitle(self._translate("dialog", title))
        widgetWidth = 160
        maxWidth, yPos = self.createLabels(["Enter Name:"])
        self.comboBox = self.makeComboBox(["--New--"]+options,widgetWidth, maxWidth, 20)
        dialogWidth = 20+maxWidth+widgetWidth
        yPos = self.makeButtonBox(dialogWidth,yPos+20)
        self.resize(dialogWidth, yPos)
        #QtCore.QMetaObject.connectSlotsByName(self)
        self.show()


    def makeComboBox(self,options,widgetWidth, xPos, yPos):
        comboBox = QtWidgets.QComboBox(self)
        comboBox.setGeometry(QtCore.QRect(xPos, yPos-3, widgetWidth, 26))
        for i,name in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), name))
        return comboBox

    def createLabels(self, labels):
        """

        :param labels: list of Strings
        :param widgets: dict of {name:widget}
        :return:
        """
        maxWidth = 0
        yPos = 20
        for labelName in labels:
            label = QtWidgets.QLabel(self)
            width = len(labelName)*10
            label.setGeometry(QtCore.QRect(20, yPos, width, 16))
            label.setText(self._translate(self.objectName(), labelName))
            if width>maxWidth:
                maxWidth = width
            yPos += 30
        return maxWidth, yPos

    def makeButtonBox(self, dialogSize, yPos):
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(int((dialogSize-164)/2), yPos, 164, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        return yPos+40


class ExportDialog(AbstractDialog):
    def __init__(self, parent):
        super(ExportDialog, self).__init__(parent, 'Export Results', 35, 180)
        widgets = ((self.createComboBox(self,('xlsx','txt')),'format','Format of the output-file(s)'),
                    (OpenFileWidget(self,self.widgetWidth, 0, 0, join(path, 'Spectral_data','top-down'),
                       "Select directory", ""), 'dir', 'Select the directory where the output-file should be saved\n'
                                                       '(default: output'),
                    (QtWidgets.QLineEdit(self), 'name', "Name of the output-file\n"
                                                        "(default: name of spectral input file + _out)"))
        xPos = self.createLabels(('Format:','Directory:','Filename:'), widgets, self)
        xPos,yPos = self.createWidgets(widgets, xPos+20)
        self.buttonBox.move(xPos/2, yPos+20)
        self.show()

    def accept(self):
        dir = self.widgets['dir'].text()
        if (dir != '') and not isdir(dir):
            raise UnvalidInputException(self.widgets['dir'].text(), "not found")
        super(ExportDialog, self).accept()

    def getFormat(self):
        return self.widgets['format'].currentText()

    def getDir(self):
        return self.widgets['dir'].text()

    def getFilename(self):
        return self.widgets['name'].text()