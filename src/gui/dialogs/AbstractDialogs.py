import traceback
import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMessageBox

from src.resources import path
from src.Exceptions import InvalidInputException
from src.services.DataServices import SequenceService
from src.gui.GUI_functions import makeFormLayout, setIcon, translate
from src.gui.widgets.Widgets import OpenFileWidget


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
        #self.sizePolicy = self.makeSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self._widgetSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._widgetSizePolicy.setHorizontalStretch(0)
        self._widgetSizePolicy.setVerticalStretch(0)
        self.makeButtonBox(self)
        self._newSettings = None
        self.move(300,100)
        self._canceled = False
        if parent is not None:
            setIcon(self)

    def canceled(self):
        return self._canceled

    @staticmethod
    def makeSizePolicy(horizontal, vertical):
        sizePolicy = QtWidgets.QSizePolicy(horizontal, vertical)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        return sizePolicy

    def makeFormLayout(self, parent):
        formLayout = makeFormLayout(parent)
        formLayout.setHorizontalSpacing(12)
        return formLayout

    def fill(self, parent, formLayout, labelNames, widgets, *args):
        '''
        Fills a QFormLayout with labels and corresponding widgets
        :param parent:
        :param (QFormLayout) formLayout:
        :param (list[str] | tuple[str]) labelNames:
        :param (dict[str, tuple[QWidget, str]]) widgets: dict of name (widget, tooltip)
        :param args: tuple of minimum and maximum width
        :return:
        '''
        index = 0
        for labelName, key in zip(labelNames, widgets.keys()):
            self.makeLine(parent, formLayout, index, labelName, key, widgets[key], args)
            index += 1
        return index

    def makeLine(self, parent, formLayout, yPos, labelName, widgetName, widgetTuple, *args):
        '''
        Sets a label and the corresponding widget into a QFormlayout
        :param parent:
        :param (QFormLayout) formLayout:
        :param (int) yPos: row index
        :param (str) labelName:
        :param (str) widgetName:
        :param (tuple[QWidget, str]) widgetTuple: (widget, tooltip)
        :param (tuple(tuple[int,int])) args: tuple of minimum and maximum width
        '''
        label = QtWidgets.QLabel(parent)
        label.setText(self._translate(self.objectName(), labelName))
        widget = widgetTuple[0]
        if args and args[0]:
            label.setMinimumWidth(args[0][0])
            widget.setMaximumWidth(args[0][1])
        formLayout.setWidget(yPos, QtWidgets.QFormLayout.LabelRole, label)
        widget.setParent(parent)
        #widget.setObjectName(widgetName)
        widget.setToolTip(self._translate(self.objectName(), widgetTuple[1]))
        self._widgetSizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        widget.setSizePolicy(self._widgetSizePolicy)
        self._widgets[widgetName] = widget
        formLayout.setWidget(yPos, QtWidgets.QFormLayout.FieldRole, widget)



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
        elif isinstance(widget, QtWidgets.QCheckBox):
            return widget.isChecked()
        else:
            raise Exception('Unknown type of widget')

    @staticmethod
    def setValueOfWidget(widget, value):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QLineEdit) or isinstance(widget, OpenFileWidget):
            if isinstance(value, int):
                value = os.path.join(path, 'Spectral_data','top-down')
            widget.setText(value)
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(value)
        else:
            raise Exception('Unknown type of widget')


    def backToLast(self):
        '''
        Resets the values of the widgets to the last used ones
        '''
        if self._configHandler.getAll()!=None:
            for name, item in self._widgets.items():
                self.setValueOfWidget(item, self._configHandler.get(name))

    
    def getDefaultDirectory(self, widgetName):
        last = self._configHandler.get(widgetName)
        if isinstance(last, str):
            default = os.path.split(last)[:-1][0]
            if os.path.isdir(default):
                return default
        return os.path.join(path, 'Spectral_data','top-down')

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
        super(AbstractDialog, self).accept()


    def checkSpectralDataFile(self, mode, fileName):
        if fileName == '':
            raise InvalidInputException('Empty Filename', "Name must not be empty")
        if not os.path.isfile(fileName):
            spectralDataPath = os.path.join(path, 'Spectral_data', mode, fileName)
            if os.path.isfile(spectralDataPath):
                return spectralDataPath
            else:
                #message = QtWidgets.QMessageBox.warning(None, "Problem occured", spectralDataPath+ " not found", QtWidgets.QMessageBox.Ok)
                raise InvalidInputException(spectralDataPath, "not found")
        return fileName


class StartDialog(AbstractDialog):
    '''
    Parent dialog for IntactStartDialog, TDStartDialog
    '''
    def __init__(self, parent, title):
        super(StartDialog, self).__init__(parent, title)
        self._formLayout = self.makeFormLayout(self)

    def setupUi(self, *args):
        widgets = self.getWidgets(args)
        # (QtWidgets.QLineEdit(startDialog), "output",
        # "Name of the output Excel file\ndefault: name of spectral pattern file + _out.xlsx"))
        index = self.fill(self, self._formLayout, self.getLabels(), widgets)
        self._formLayout.addItem(QtWidgets.QSpacerItem(0, 1))
        self._defaultButton = self.makeDefaultButton(self)
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.LabelRole, self._defaultButton)
        self.backToLast()
        #return index

    def makeDefaultButton(self, parent):
        self._defaultButton = QtWidgets.QPushButton(parent)
        sizePolicy = self.makeSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self._defaultButton.sizePolicy().hasHeightForWidth())
        self._defaultButton.setSizePolicy(sizePolicy)
        self._defaultButton.setMinimumSize(QSize(113, 0))
        self._defaultButton.clicked.connect(self.backToLast)
        self._defaultButton.setText(self._translate(self.objectName(), "Last Settings"))
        return self._defaultButton

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
            return newSettings
        except InvalidInputException as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", e.__str__(), QMessageBox.Ok)

    def newSettings(self):
        return self._newSettings

    def checkValues(self, configs, *args):
        configs['spectralData'] = self.checkSpectralDataFile(args[0], configs['spectralData'])
        if configs['profile'] != "":
            configs['profile'] = self.checkSpectralDataFile(args[0], configs['profile'])
        if configs['sequName'] not in SequenceService().getAllSequenceNames():
            raise InvalidInputException(configs['sequName'], "not found")
        return configs


    def updateCal(self, cal):
        if cal:
            self._widgets['calIons'].setEnabled(True)
        else:
            self._widgets['calIons'].setEnabled(False)


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
        tabSizePolicy = self.makeSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        tabSizePolicy.setHeightForWidth(self._tabWidget.sizePolicy().hasHeightForWidth())
        self._tabWidget.setSizePolicy(tabSizePolicy)
        self._verticalLayout.addWidget(self._tabWidget)


    def createTab(self,name):
        tab = QtWidgets.QWidget(self)
        self._tabWidget.addTab(tab, "")
        self._tabWidget.setTabText(self._tabWidget.indexOf(tab), self._translate(self.objectName(), name))
        return tab


