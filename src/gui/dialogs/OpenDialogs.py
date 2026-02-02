from PyQt5 import QtWidgets
from os.path import join

from src.resources import path
from src.gui.dialogs.AbstractDialogs import AbstractDialog
from src.gui.GUI_functions import createComboBox
from src.gui.widgets.Widgets import OpenFileWidget

dataPath = join(path, 'src', 'data')

class OpenDialog(AbstractDialog):
    '''
    Dialog to open stored values (element, fragmentation, etc.)
    '''
    def __init__(self, title, options):
        super(OpenDialog, self).__init__(parent=None,title=title)
        formLayout = self.makeFormLayout(self)
        self._comboBox = createComboBox(self, options)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self._comboBox, '')})
        formLayout.setWidget(index + 1, QtWidgets.QFormLayout.SpanningRole, self._buttonBox)
        self.show()

    def getName(self):
        return self._comboBox.currentText()


defaultFilters = "Supported Files (*txt *csv);;Comma Separated Values (*csv);;Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"

class OpenSpectralDataDlg(AbstractDialog):
    '''
    Dialog to select the correct spectral data file (if an old top-down search/analysis is loaded)
    '''
    def __init__(self, parent):
        super(OpenSpectralDataDlg, self).__init__(parent,'Select File Location')
        formLayout = self.makeFormLayout(self)
        #label = QtWidgets.QLabel(self)
        #label.setText(self._translate(self.objectName(), 'Select the location of the file.'))
        #formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, label)
        self._fileWidget = OpenFileWidget(parent, 1, join(path, 'Spectral_data', 'top-down'), "Open File",
                                          defaultFilters)
        self.fill(self, formLayout, ("File name:",), {'spectralData':(self._fileWidget,
                                  'Name of the file with spectral peaks (txt or csv format)')})
        formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self.show()

    def getValue(self):
        return self._fileWidget.text()


