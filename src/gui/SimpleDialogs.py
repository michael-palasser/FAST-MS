from PyQt5 import QtWidgets
from os.path import join, isdir

from src import path
from src.Exceptions import UnvalidInputException
from src.gui.AbstractDialogs import AbstractDialog
from src.gui.Widgets import OpenFileWidget

dataPath = join(path, 'src', 'data')

class OpenDialog(AbstractDialog):
    def __init__(self, title, options):
        super(OpenDialog, self).__init__(parent=None,title=title)
        formLayout = self.makeFormLayout(self)
        self.comboBox = self.createComboBox(self, options)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self.comboBox, '')})
        formLayout.setWidget(index+1, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)
        self.show()

class SelectSearchDlg(AbstractDialog):
    def __init__(self, parent, options, deleteFun, service):
        super(SelectSearchDlg, self).__init__(parent,'Load Analysis')
        self.deleteFun = deleteFun
        self._service = service
        formLayout = self.makeFormLayout(self)
        self._options = options
        #self._options = ['search1, 23.01.1992, 08:12', 'search2, 28.01.1992, 08:12']
        self.comboBox = self.createComboBox(self, self._options)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self.comboBox, '')})

        self._delBtn = QtWidgets.QPushButton(self)
        #sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        #sizePolicy.setHeightForWidth(self._delBtn.sizePolicy().hasHeightForWidth())
        #self._delBtn.setSizePolicy(sizePolicy)
        #self._delBtn.setMinimumSize(QtCore.QSize(113, 0))
        self._delBtn.clicked.connect(self.delete)
        self._delBtn.setText(self._translate(self.objectName(), "Delete"))

        formLayout.setWidget(index+1, QtWidgets.QFormLayout.LabelRole, self._delBtn)
        formLayout.setWidget(index+2, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)
        self.show()

    def delete(self):
        name = self.comboBox.currentText()
        choice = QtWidgets.QMessageBox.question(self, "Deleting", "Do you really want to permanently delete analysis "
                                                +name+'\nWarning: This cannot be undone',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.deleteFun(name,self._service)
            index = self._options.index(name)
            del self._options[index]
            self.comboBox.removeItem(index)

    def getName(self):
        if self.accepted:
            return self.comboBox.currentText()
        else:
            return None

class OpenSpectralDataDlg(AbstractDialog):
    def __init__(self, parent):
        super(OpenSpectralDataDlg, self).__init__(parent,'Spectral Data not found!')
        formLayout = self.makeFormLayout(self)
        label = QtWidgets.QLabel(self)
        label.setText(self._translate(self.mainWindow.objectName(), 'File with spectral data could not be found.\n'
                                                                    'Select the location of the file.'))
        formLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, label)
        self.fileWidget = OpenFileWidget(parent, 1, join(path, 'Spectral_data','top-down'), "Open File",
                                           "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)")
        self.fill(self, formLayout, ("File name:",), {'spectralData':(self.fileWidget,
                                  'Name of the file with spectral peaks (txt or csv format)')})
        formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)
        self.show()

    def getValue(self):
        return self.fileWidget.text()

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

    '''def getFormat(self):
        return self.widgets['format'].currentText()'''

    def getDir(self):
        return self.widgets['dir'].text()

    def getFilename(self):
        return self.widgets['name'].text()


