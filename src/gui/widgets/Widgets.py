import os
import sys

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt

from src.gui.GUI_functions import createComboBox, setIcon


class OpenFileWidget(QtWidgets.QWidget):
    '''
    QWidget to select (a) file path(s). Used by ExportDialog, OpenSpectralDataDlg, IntactStartDialog,
    SpectrumComparatorStartDialog, and TDStartDialog
    '''
    def __init__(self, parent, mode,startPath, title, formats):
        super(OpenFileWidget, self).__init__(parent)
        self._horizontalLayout = QtWidgets.QHBoxLayout(self)
        self._horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self._lineEdit = DropTextEdit(self, mode)
        self._horizontalLayout.addWidget(self._lineEdit)
        self._pushButton = QtWidgets.QPushButton(self)
        setIcon(self._pushButton, 'open.png')
        self._pushButton.setIconSize(QtCore.QSize(32, 32))
        self._pushButton.setMaximumSize(32, 32)
        self._horizontalLayout.addWidget(self._pushButton)
        self.__startPath = startPath
        self.__title = title
        self.__formats = formats
        self._pushButton.clicked.connect(lambda: self.getFileNames(mode))
        self._accepted = False

    def getFileNames(self, mode):
        startPath = os.path.split(self.text())[:-1][0]
        if not os.path.isdir(startPath):
            startPath = self.__startPath
        if mode == 2:
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, self.__title, startPath, self.__formats)#, options=options)
            self._lineEdit.setText(',  '.join(files))
        elif mode == 1:
            file, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.__title, startPath, self.__formats)#, options=options)
            self._lineEdit.setText(file)
        else:
            dir = QtWidgets.QFileDialog.getExistingDirectory(self, self.__title, startPath)
            if dir:
                dir = QtCore.QDir.toNativeSeparators(dir)
            self._lineEdit.setText(dir)
        self._accepted=True
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

    def accepted(self):
        return self._accepted

class DropTextEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None, mode=1):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._mode = mode

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        event.acceptProposedAction() if event.mimeData().hasUrls() else super().dragEnterEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if not paths:
            return super().dropEvent(event)
        #current = self.toPlainText().strip()
        #self.setPlainText((current + "\n" if current else "") + "\n".join(paths))
        current = self.text().strip()
        if self._mode==2:
            self.setText((current + ",  " if current else "") + ",  ".join(paths))
        else:
            self.setText(paths[0])
        event.acceptProposedAction()

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
                                                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if choice == QtWidgets.QMessageBox.StandardButton.Yes:
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
            item.setCheckState(QtCore.Qt.CheckState.Checked)
        else:
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def changeState(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState()==QtCore.Qt.CheckState.Checked:
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.CheckState.Checked)

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
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                values.append(self._options[i])
        return values



class ShowFormulaWidget(QtWidgets.QWidget):
    '''
    Widget which shows the molecular formula of an ion
    '''
    def __init__(self, ion):
        super(ShowFormulaWidget, self).__init__(None)
        self.setWindowTitle(ion.getName())
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(ion.getFormula().toString())
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label)
        self.show()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui =LoadingWidget(100, True)
    sys.exit(app.exec())