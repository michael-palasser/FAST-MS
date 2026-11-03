import os

from PySide6 import QtWidgets

from src.Exceptions import InvalidInputException
from src.gui.dialogs.AbstractDialogs import AbstractDialog
from src.gui.widgets.ExportTable import ExportTable
from src.gui.widgets.Widgets import OpenFileWidget
from src.resources import base_path


class SaveDlg(AbstractDialog):
    '''
    Dialog to export/save results of a top-down or intact analysis
    '''
    def __init__(self, parent, title, storedOptions, defaultDir):
        super().__init__(parent, title)
        """if storedOptions is None:
            storedOptions = {'columns':[], 'analysis':[], 'dir':[]}"""
        self._formLayout = self.makeFormLayout(self)
        """if isdir(storedOptions['dir']):
            startPath = storedOptions['dir']
        else:
            startPath = join(path, 'Spectral_data', default)"""
        #except KeyError:
        #    startPath = join(path, 'Spectral_data', 'top-down')
        if os.path.isdir(storedOptions['dir']):
            startDir = storedOptions['dir']
        else:
            startDir = defaultDir
        self.fill(self, self._formLayout,('Directory:','Filename:'),
                  {'dir': (OpenFileWidget(self, 0, startDir, "Select directory", ""),
                              'Select the directory where the output-file should be saved\n(default: output'),
                   'name': (QtWidgets.QLineEdit(self), "Name of the output-file\n"
                                                       "(default: name of spectral input file + _out)")})
        self._widgets['dir'].setText(startDir)
        fileName = storedOptions['file']
        if fileName[-4]==".":
            fileName = fileName[:-4]
        self._widgets['name'].setText(fileName)

    def accept(self):
        dir = self._widgets['dir'].text()
        if (dir != '') and not os.path.isdir(dir):
            raise InvalidInputException(self._widgets['dir'].text(), "not found")
        super().accept()

    def getDir(self):
        return self._widgets['dir'].text()


class ExportDialog(SaveDlg):
    '''
    Dialog to export the results of a top-down or intact analysis
    '''
    def __init__(self, parent, analysisOptions, storedOptions, default = 'top-down'):
        if storedOptions is None:
            storedOptions = {'columns':[], 'analysis':[], 'dir':[]}
        super(ExportDialog, self).__init__(parent, 'Export Results', storedOptions, os.path.join(base_path, 'Spectral_data', default))
        self._formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        index =3
        self._boxes = []
        if len(analysisOptions)>0:
            label = QtWidgets.QLabel(self)
            label.setText(self._translate(self.objectName(), 'Analysis:'))
            self._formLayout.setWidget(index, QtWidgets.QFormLayout.ItemRole.LabelRole, label)
            for i, name in enumerate(analysisOptions):#('occupancies','charges','reduced charges', 'sequence coverage')):
                box = QtWidgets.QCheckBox(name, self)
                if name in storedOptions['analysis']:
                    box.setChecked(True)
                self._formLayout.setWidget(index,QtWidgets.QFormLayout.ItemRole.FieldRole, box)
                self._boxes.append(box)
                index +=1
        options = ('m/z', 'z','intensity', 'int./z', 'name', 'error /ppm', 'S/N', 'quality', 'formula', 'score', 'comment',
                   'molecular mass', 'average mass', 'noise')
        label = QtWidgets.QLabel(self)
        label.setText(self._translate(self.objectName(), 'Attributes:'))
        self._formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.ItemRole.SpanningRole, label)
        self._table = ExportTable(self, options, storedOptions['columns'])
        self._formLayout.setWidget(index + 2, QtWidgets.QFormLayout.ItemRole.SpanningRole, self._table)
        self._formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        self._formLayout.setWidget(index + 4, QtWidgets.QFormLayout.ItemRole.FieldRole, self._buttonBox)
        self.show()

    def getOptions(self):
        ticked = [box.text() for box in self._boxes if box.isChecked()]
        return {'columns':self._table.readTable(), 'analysis':ticked, 'dir':self._widgets['dir'].text()}

    def getFilename(self):
        name = self._widgets['name'].text()
        if not name.endswith(".xlsx"):
            name += ".xlsx"
        return name


class SaveSearchDialog(SaveDlg):
    '''
    Dialog to save the results of a top-down search/analysis
    '''
    def __init__(self, filePath):
        filePath = os.path.normpath(filePath)
        super().__init__(None,'Save Analysis', {"dir":os.path.dirname(filePath), "file":os.path.basename(filePath)}, base_path)
        self._formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self._buttonBox)
        self.show()

    def getFilename(self):
        return os.path.join(self._widgets['dir'].text(), self._widgets['name'].text())

class SaveSearchDialogOld(AbstractDialog):
    '''
    Dialog to save the results of a top-down search/analysis
    '''
    def __init__(self, text):
        super(SaveSearchDialogOld, self).__init__(None,title='Save Analysis')
        formLayout = self.makeFormLayout(self)
        self._lineEdit = QtWidgets.QLineEdit(self)
        self._lineEdit.setText(text)
        index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self._lineEdit, 'Enter the name')})
        formLayout.setWidget(index + 1, QtWidgets.QFormLayout.ItemRole.SpanningRole, self._buttonBox)
        self.show()

    def getText(self):
        return self._lineEdit.text()
