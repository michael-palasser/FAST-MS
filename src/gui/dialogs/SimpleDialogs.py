from PyQt5 import QtWidgets
from os.path import join, isdir

from src import path
from src.Exceptions import InvalidInputException
from src.gui.dialogs.AbstractDialogs import AbstractDialog
from src.gui.GUI_functions import createComboBox
from src.gui.widgets.ExportTable import ExportTable
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

class SelectSearchDlg(AbstractDialog):
    '''
    Dialog to open saved top-down search/analysis
    '''
    def __init__(self, parent, options, deleteFun, service):
        super(SelectSearchDlg, self).__init__(parent,'Load Analysis')
        self._deleteFun = deleteFun
        self._service = service
        formLayout = self.makeFormLayout(self)
        self._options = options
        #self._options = ['search1, 23.01.1992, 08:12', 'search2, 28.01.1992, 08:12']
        self._comboBox = createComboBox(self, self._options)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self._comboBox, '')})

        self._delBtn = QtWidgets.QPushButton(self)
        #sizePolicy = self.makeSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        #sizePolicy.setHeightForWidth(self._delBtn.sizePolicy().hasHeightForWidth())
        #self._delBtn.setSizePolicy(sizePolicy)
        #self._delBtn.setMinimumSize(QtCore.QSize(113, 0))
        self._delBtn.clicked.connect(self.delete)
        self._delBtn.setText(self._translate(self.objectName(), "Delete"))

        formLayout.setWidget(index+1, QtWidgets.QFormLayout.LabelRole, self._delBtn)
        formLayout.setWidget(index + 2, QtWidgets.QFormLayout.SpanningRole, self._buttonBox)
        self.show()

    def delete(self):
        name = self._comboBox.currentText()
        choice = QtWidgets.QMessageBox.question(self, "Deleting", "Do you really want to permanently delete analysis "
                                                +name+'\nWarning: This cannot be undone',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self._deleteFun(name, self._service)
            index = self._options.index(name)
            del self._options[index]
            self._comboBox.removeItem(index)

    def getName(self):
        if self.accepted:
            return self._comboBox.currentText()
        else:
            return None


class OpenSpectralDataDlg(AbstractDialog):
    '''
    Dialog to select the correct spectral data file (if an old top-down search/analysis is loaded)
    '''
    def __init__(self, parent):
        super(OpenSpectralDataDlg, self).__init__(parent,'Spectral Data not found!')
        formLayout = self.makeFormLayout(self)
        label = QtWidgets.QLabel(self)
        label.setText(self._translate(self.objectName(), 'Select the location of the file.'))
        formLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, label)
        self._fileWidget = OpenFileWidget(parent, 1, join(path, 'Spectral_data', 'top-down'), "Open File",
                                           "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)")
        self.fill(self, formLayout, ("File name:",), {'spectralData':(self._fileWidget,
                                  'Name of the file with spectral peaks (txt or csv format)')})
        formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self._buttonBox)
        self.show()

    def getValue(self):
        return self._fileWidget.text()


class ExportDialog(AbstractDialog):
    '''
    Dialog to export the results of a top-down analysis
    '''
    def __init__(self, parent, analysisOptions, storedOptions):
        super(ExportDialog, self).__init__(parent, 'Export Results')
        if storedOptions is None:
            storedOptions = {'columns':[], 'analysis':[]}
        formLayout = self.makeFormLayout(self)
        index=self.fill(self, formLayout,('Directory:','Filename:'),
                  {'dir': (OpenFileWidget(self, 0, join(path, 'Spectral_data', 'top-down'), "Select directory", ""),
                              'Select the directory where the output-file should be saved\n(default: output'),
                   'name': (QtWidgets.QLineEdit(self), "Name of the output-file\n"
                                                       "(default: name of spectral input file + _out)")})
        formLayout.addItem(QtWidgets.QSpacerItem(0,1))

        index +=1
        self._boxes = []
        if len(analysisOptions)>0:
            label = QtWidgets.QLabel(self)
            label.setText(self._translate(self.objectName(), 'Analysis:'))
            formLayout.setWidget(index, QtWidgets.QFormLayout.LabelRole, label)
            for i, name in enumerate(analysisOptions):#('occupancies','charges','reduced charges', 'sequence coverage')):
                box = QtWidgets.QCheckBox(name, self)
                if name in storedOptions['analysis']:
                    box.setChecked(True)
                formLayout.setWidget(index,QtWidgets.QFormLayout.FieldRole, box)
                self._boxes.append(box)
                index +=1

        options = ('m/z', 'z','intensity', 'int./z', 'fragment', 'error /ppm', 'S/N', 'quality', 'formula', 'score', 'comment',
                   'molecular mass', 'average mass', 'noise')
        label = QtWidgets.QLabel(self)
        label.setText(self._translate(self.objectName(), 'Ion Values:'))
        formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        formLayout.setWidget(index + 1, QtWidgets.QFormLayout.SpanningRole, label)
        #for i in ('analysis','ions','peaks', 'deleted ions', 'ions before remodelling')
        self._table = ExportTable(self, options, storedOptions['columns'])
        formLayout.setWidget(index + 2, QtWidgets.QFormLayout.SpanningRole, self._table)
        formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        formLayout.setWidget(index + 4, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self.show()

    def accept(self):
        dir = self._widgets['dir'].text()
        if (dir != '') and not isdir(dir):
            raise InvalidInputException(self._widgets['dir'].text(), "not found")
        super(ExportDialog, self).accept()

    '''def getFormat(self):
        return self._widgets['format'].currentText()'''

    def getDir(self):
        return self._widgets['dir'].text()

    def getFilename(self):
        return self._widgets['name'].text()

    def getOptions(self):
        ticked = [box.text() for box in self._boxes if box.isChecked()]
        print(ticked)
        return {'columns':self._table.readTable(), 'analysis':ticked}

class SaveSearchDialog(AbstractDialog):
    '''
    Dialog to save the results of a top-down search/analysis
    '''
    def __init__(self, text):
        super(SaveSearchDialog, self).__init__(parent=None,title='Save Analysis')
        formLayout = self.makeFormLayout(self)
        self._lineEdit = QtWidgets.QLineEdit(self)
        self._lineEdit.setText(text)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self._lineEdit, 'Enter the name')})
        formLayout.setWidget(index + 1, QtWidgets.QFormLayout.SpanningRole, self._buttonBox)
        self.show()

    def getText(self):
        return self._lineEdit.text()
