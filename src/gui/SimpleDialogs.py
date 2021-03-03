from PyQt5 import QtWidgets
from os.path import join, isdir

from src import path
from src.Exceptions import UnvalidInputException
from src.gui.AbstractDialogs import AbstractDialog, OpenFileWidget

dataPath = join(path, 'src', 'data')

class OpenDialog(AbstractDialog):
    def __init__(self, title, options):
        super(OpenDialog, self).__init__(parent=None,title=title)
        formLayout = self.makeFormLayout(self)
        self.comboBox = self.createComboBox(self, options)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self.comboBox, '')})
        formLayout.setWidget(index+1, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)
        self.show()


class ExportDialog(AbstractDialog):
    def __init__(self, parent):
        super(ExportDialog, self).__init__(parent, 'Export Results')
        formLayout = self.makeFormLayout(self)
        index=self.fill(self, formLayout,('Directory:','Filename:'),
                  {'dir': (OpenFileWidget(self, 0, join(path, 'Spectral_data', 'top-down'), "Select directory", ""),
                              'Select the directory where the output-file should be saved\n(default: output'),
                   'name': (QtWidgets.QLineEdit(self), "Name of the output-file\n"
                                                       "(default: name of spectral input file + _out)")})
        formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        formLayout.setWidget(index+1, QtWidgets.QFormLayout.FieldRole, self.buttonBox)
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


