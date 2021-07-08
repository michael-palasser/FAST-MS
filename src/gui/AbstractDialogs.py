import traceback
from os.path import join, isfile

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from src import path
from src.Exceptions import InvalidInputException
from src.Services import SequenceService
from src.gui.Widgets import OpenFileWidget


class AbstractDialog(QtWidgets.QDialog):
    '''
    Parent class for DialogWithTabs, StartDialog, ExportDialog, OpenDialog, OpenSpectralDataDlg,
    SaveSearchDialog, SelectSearchDlg, OccupancyRecalcStartDialog, SpectrumComparatorDialog
    '''
    def __init__(self, parent, title):
        super().__init__(parent)
        #self.setObjectName(dialogName)
        #self.lineSpacing = lineSpacing
        self._widgets = dict()
        #self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))


        self._widgetSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._widgetSizePolicy.setHorizontalStretch(0)
        self._widgetSizePolicy.setVerticalStretch(0)
        self.makeButtonBox(self)
        self._newSettings = None
        self.move(300,100)
        self._canceled = False

    def canceled(self):
        return self._canceled

    @staticmethod
    def setNewSizePolicy(horizontal, vertical):
        sizePolicy = QtWidgets.QSizePolicy(horizontal, vertical)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        return sizePolicy

    def makeFormLayout(self, parent):
        formLayout = QtWidgets.QFormLayout(parent)
        formLayout.setHorizontalSpacing(12)
        #formLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        formLayout.setLabelAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        return formLayout

    def fill(self, parent, formLayout, labelNames, widgets, *args):
        index = 0
        for labelName, key in zip(labelNames, widgets.keys()):
            self.makeLine(parent, formLayout, index, labelName, key, widgets[key], args)
            index += 1
        return index

    def makeLine(self, parent, formLayout, yPos, labelName, widgetName, widgetTuple, *args):
        label = QtWidgets.QLabel(parent)
        label.setText(self._translate(self.objectName(), labelName))
        widget = widgetTuple[0]
        if args and args[0]:
            label.setMinimumWidth(args[0][0])
            widget.setMaximumWidth(args[0][1])
        formLayout.setWidget(yPos, QtWidgets.QFormLayout.LabelRole, label)
        widget.setParent(parent)
        widget.setObjectName(widgetName)
        widget.setToolTip(self._translate(self.objectName(), widgetTuple[1]))
        self._widgetSizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        widget.setSizePolicy(self._widgetSizePolicy)
        self._widgets[widgetName] = widget
        formLayout.setWidget(yPos, QtWidgets.QFormLayout.FieldRole, widget)

    def createComboBox(self, parent, options):
        comboBox = QtWidgets.QComboBox(parent)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), option))
        return comboBox

    def makeButtonBox(self, parent):
        self._buttonBox = QtWidgets.QDialogButtonBox(parent)
        self._buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        return self._buttonBox


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
        if self._configHandler.getAll()!=None:
            for name, item in self._widgets.items():
                self.setValueOfWidget(item, self._configHandler.get(name))

    def reject(self):
        self._canceled = True
        super(AbstractDialog, self).reject()

    def makeDictToWrite(self):
        newSettings = dict()
        for name, item in self._widgets.items():
            newSettings[name] = self.getValueOfWidget(item)
        return newSettings


    def accept(self):
        self.ok = True
        print(self._newSettings)
        super(AbstractDialog, self).accept()

    def checkValues(self, configs):
        pass


class StartDialog(AbstractDialog):
    '''
    Parent dialog for IntactStartDialog, TDStartDialog
    '''
    def __init__(self, parent, title):
        super(StartDialog, self).__init__(parent, title)

    """def startProgram(self, mainMethod):
        self.makeDictToWrite()
        #try:
        mainMethod()"""
        #    super(StartDialog, self).accept()
        #except:
        #    traceback.print_exc()
         #   QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)

    '''def makeButtonWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontLayout = QtWidgets.QHBoxLayout(widget)
        self.makeButtonBox(widget)
        self._defaultButton = self.makeDefaultButton(widget)
        horizontLayout.addWidget(self._defaultButton)
        horizontLayout.addSpacing(50)
        horizontLayout.addWidget(self._buttonBox)
        return widget'''

    def makeDefaultButton(self, parent):
        self._defaultButton = QtWidgets.QPushButton(parent)
        sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self._defaultButton.sizePolicy().hasHeightForWidth())
        self._defaultButton.setSizePolicy(sizePolicy)
        self._defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        self._defaultButton.clicked.connect(self.backToLast)
        self._defaultButton.setText(self._translate(self.objectName(), "last settings"))
        return self._defaultButton

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
        except InvalidInputException as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", e.__str__(), QMessageBox.Ok)
        return newSettings

    def newSettings(self):
        return self._newSettings

    def checkValues(self, configs, *args):
        if configs['sequName'] not in SequenceService().getAllSequenceNames():
            raise InvalidInputException(configs['sequName'], "not found")
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
                message = QtWidgets.QMessageBox.warning(None, "Problem occured", spectralDataPath+ " not found", QtWidgets.QMessageBox.Ok)
                #raise InvalidInputException(spectralDataPath, "not found")
        return False


class DialogWithTabs(AbstractDialog):
    '''
    Parent class for IntactStartDialog
    '''
    def __init__(self, parent, title):
        super().__init__(parent, title)
        self._verticalLayout = QtWidgets.QVBoxLayout(self)
        self._verticalLayout.setContentsMargins(0, 12, 0, 12)
        #self._verticalLayout.setObjectName("_verticalLayout")
        self._tabWidget = QtWidgets.QTabWidget(self)
        self._tabWidget.setEnabled(True)
        tabSizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        tabSizePolicy.setHeightForWidth(self._tabWidget.sizePolicy().hasHeightForWidth())
        self._tabWidget.setSizePolicy(tabSizePolicy)
        self._verticalLayout.addWidget(self._tabWidget)


        #self.sizePolicy.setHeightForWidth(self._buttonBox.sizePolicy().hasHeightForWidth())
        #self._buttonBox.setSizePolicy(self.sizePolicy)
        #self._buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)


    def createTab(self,name):
        tab = QtWidgets.QWidget(self)
        self._tabWidget.addTab(tab, "")
        self._tabWidget.setTabText(self._tabWidget.indexOf(tab), self._translate(self.objectName(), name))
        return tab


