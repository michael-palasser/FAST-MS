import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QFileDialog, QLabel, QApplication

from src.gui.GUI_functions import createComboBox, translate


class OpenFileWidget(QtWidgets.QWidget):
    '''
    QWidget to select (a) file path(s). Used by ExportDialog, OpenSpectralDataDlg, IntactStartDialog,
    SpectrumComparatorStartDialog, and TDStartDialog
    '''
    def __init__(self, parent, mode,startPath, title, formats):
        super(OpenFileWidget, self).__init__(parent)
        #self.setGeometry(QtCore.QRect(20, yPos, width, 36))
        self._horizontalLayout = QtWidgets.QHBoxLayout(self)
        self._horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self._lineEdit = QtWidgets.QLineEdit(self)

        #self._lineEdit.setGeometry(QtCore.QRect(0, 5, width-32, 21))

        self._horizontalLayout.addWidget(self._lineEdit)
        self._pushButton = QtWidgets.QPushButton(self)
        #self._pushButton.setGeometry(QtCore.QRect(width-32, 0, 36, 30))
        self._pushButton.setIcon(QtGui.QIcon('open.png'))
        self._pushButton.setIconSize(QtCore.QSize(32, 32))
        self._pushButton.setMaximumSize(32, 32)
        #self._pushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        #self._pushButton.setGeometry(QtCore.QRect(250, yPos, 26, 26))
        #_translate = QtCore.QCoreApplication.translate
        #self._pushButton.setText(_translate(self.objectName(), "O"))
        self._horizontalLayout.addWidget(self._pushButton)
        self.__startPath = startPath
        self.__title = title
        self.__formats = formats

        """sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._pushButton.sizePolicy().hasHeightForWidth())
        self._pushButton.setSizePolicy(sizePolicy)"""
        #_lineEdit.setObjectName(name)
        #self.widgets[self._lineEdit.objectName()] = self._lineEdit
        #_pushButton.setObjectName(name)
        self._pushButton.clicked.connect(lambda: self.getFileNames(mode))
        #self.buttons[_pushButton.objectName()] = _pushButton

    def getFileNames(self, mode):
        #_files = self.openFileNamesDialog(self.__title, self.__formats)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if mode == 2:
            files, _ = QFileDialog.getOpenFileNames(self, self.__title, self.__startPath, self.__formats, options=options)
            self._lineEdit.setText(',  '.join(files))
        elif mode == 1:
            file, _ = QFileDialog.getOpenFileName(self, self.__title, self.__startPath, self.__formats, options=options)
            self._lineEdit.setText(file)
        else:
            dir = QFileDialog.getExistingDirectory(self, self.__title, self.__startPath)
            if dir:
                dir = QtCore.QDir.toNativeSeparators(dir)
            self._lineEdit.setText(dir)
        #self.__files = _files

    #ToDo different Versions:File/Files, title, file formats

    def setText(self, text):
        if isinstance(text, list):
            text = ',  '.join(text)
        self._lineEdit.setText(text)

    def text(self):
        return self._lineEdit.text()

    def getFiles(self):
        return self._lineEdit.text().split(',  ')


"""class BoxUpdateWidget(QtWidgets.QWidget):
    '''
    QWidget which is used by FragmentEditorController to select the correct precursor template from a (up-to-date) list
    of templates
    '''
    def __init__(self, parent, options):
        super(BoxUpdateWidget, self).__init__(parent)
        self.setContentsMargins(0,0,0,0)
        self._translate = QtCore.QCoreApplication.translate
        self._horizontalLayout = QtWidgets.QHBoxLayout(self)
        self._horizontalLayout.setContentsMargins(0,0,0,0)
        self._comboBox = createComboBox(self,options)
        '''self._comboBox = QtWidgets.QComboBox(self)
        for i, option in enumerate(options):
            self._comboBox.addItem('')
            self._comboBox.setItemText(i, self._translate(self.objectName(), option))'''
        self._horizontalLayout.addWidget(self._comboBox)

        self._button = QtWidgets.QPushButton(self)
        #sizePolicy = self.makeSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        #sizePolicy.setHeightForWidth(self._defaultButton.sizePolicy().hasHeightForWidth())
        #self._button.setSizePolicy(sizePolicy)
        # self._defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        self._button.setText(self._translate(self.objectName(), 'Update'))
        #self._button.clicked.connect(fun)
        self._horizontalLayout.addWidget(self._button)

    def connectBtn(self, fun):
        self._button.clicked.connect(fun)

    def currentText(self):
        return self._comboBox.currentText()

    def setText(self, text):
        self._comboBox.setCurrentText(text)

    def updateBox(self, newOptions):
        toAdjust = self._comboBox.count() - len(newOptions)
        if toAdjust > 0:
            [self._comboBox.removeItem(i) for i in range(len(newOptions), len(newOptions) + toAdjust)]
        elif toAdjust < 0:
            [self._comboBox.addItem("") for i in range(-1 * toAdjust)]
        for i, option in enumerate(newOptions):
            self._comboBox.setItemText(i, self._translate(self.objectName(), option))"""


class LoadingWidget(QtWidgets.QWidget):
    '''
    QWidget which shows a gif to illustrate an ongoing process.
    '''
    def __init__(self, size, stop=False):
        super(LoadingWidget, self).__init__(None)
        self._size = size
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self._progress = QtWidgets.QProgressBar(self)
        self._progress.setGeometry(200, 80, 250, 20)
        verticalLayout.addWidget(self._progress)
        self._progress.setValue(0)
        self._completed = 0
        if stop:
            stopBtn = QtWidgets.QPushButton(self)
            verticalLayout.addWidget(stopBtn)
            stopBtn.setText('Cancel')
            stopBtn.clicked.connect(self.cancel)
        self.show()
        '''self._loading_lbl = QLabel(self)
        loading_movie = QMovie("loading.gif")  # some gif in here
        self._loading_lbl.setMovie(loading_movie)
        loading_movie.start()

        self.setGeometry(50, 50, 100, 100)
        self.setMinimumSize(10, 10)
        self.show()'''

    def progress(self):
        self._completed += 1/ self._size
        self._progress.setValue(self._completed)
        self.show()
        if self._progress == 1:
            self.close()

    def cancel(self):
        choice = QtWidgets.QMessageBox.question(self, "",'Do you really want to cancel?',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.close()

class CheckableComboBox(QtWidgets.QComboBox):
    def __init__(self, parent, options, checkedIndizes):
        super(CheckableComboBox, self).__init__(parent)
        self._options = options
        createComboBox(parent, options, self)
        for i in range(len(self._options)):
            self.setChecked(i, i in checkedIndizes)
        self.view().pressed.connect(self.changeState)

    def setChecked(self, index, checked):
        item = self.model().item(index, self.modelColumn())
        if checked:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)

    def changeState(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState()==QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

    def setCurrentText(self, textList):
        try:
            super(CheckableComboBox, self).setCurrentText(textList[0])
            for i, option in enumerate(self._options):
                if option in textList:
                    self.setChecked(i, True)
        except IndexError:
            pass

    def currentText(self):
        values = []
        for i in range(self.count()):
            item = self.model().item(i, self.modelColumn())
            if item.checkState() == QtCore.Qt.Checked:
                values.append(self._options[i])
        return values

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui =LoadingWidget(100, True)
    sys.exit(app.exec_())