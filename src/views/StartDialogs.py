import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog
from src import path
from os.path import join

class AbstractStartDialog1(QtWidgets.QDialog):
    def __init__(self, parent, title, lineSpacing):
        super().__init__(parent)
        self.setObjectName('dialog')
        self.widgets = []
        self.lineSpacing = lineSpacing
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.move(300,100)



class SpectrumComparatorStartDialog(AbstractStartDialog1):
    def __init__(self, parent):
        super().__init__(parent, "Compare Spectra", 40)
        self.width = 500

        lblHight = 70
        label = QtWidgets.QLabel(self)
        label.setGeometry(QtCore.QRect(35, 30, self.width-70, lblHight))
        label.setText(self._translate(self.objectName(),
                                      'Enter the file name containing the ions which you want to compare:\n\n'
                     'The format in the files must be:\t"m/z   z   int.   name"\n'
                                                         '\t-with tab stops between each value'))
        self.yPos = lblHight
        self.startPath = join(path, 'Spectral_data', 'comparison')
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(self.width-79, self.yPos, 52, 32))
        self.pushButton.setText(self._translate(self.objectName(), "+"))
        self.pushButton.clicked.connect(self.createNew)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.yPos += self.lineSpacing +10
        #self.runningNr = 0
        #self.buttons = dict()
        self.files = []
        for i in range(3):
            self.createInputWidget()
        print(self.startPath)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.move(int(self.width/3),self.yPos+self.lineSpacing)
        self.resize(self.width, self.yPos+50+self.lineSpacing)
        self.show()

    def createInputWidget(self):
        """widget = QtWidgets.QWidget(self)
        widget.setGeometry(QtCore.QRect(20, self.yPos, self.width-40, 50))
        horizontalLayout = QtWidgets.QHBoxLayout(widget)
        lineEdit = QtWidgets.QLineEdit(widget)
        horizontalLayout.addWidget(lineEdit)
        pushButton = QtWidgets.QPushButton(widget)
        pushButton.setText(self._translate(self.objectName(), "O"))
        horizontalLayout.addWidget(pushButton)"""
        widget = OpenFileWidget(self,self.width-40,self.yPos, 2, self.startPath, "Open File to Compare",
                                "Plain Text Files (*txt);;All Files (*)")
        widget.setToolTip("Names of text files containing ion data")
        self.verticalLayout.addWidget(widget)
        self.widgets.append(widget)
        #lineEdit.setObjectName(str(self.runningNr))
        #pushButton.setObjectName(str(self.runningNr))
        #pushButton.clicked.connect(lambda: self.getFileNames(pushButton.objectName()))
        #self.buttons[pushButton.objectName()] = pushButton
        self.yPos += self.lineSpacing
        #self.runningNr += 1
        widget.show()

    def createNew(self):
        self.createInputWidget()
        self.buttonBox.move(int(self.width/3),self.yPos+self.lineSpacing)
        self.resize(self.width, self.yPos+50+self.lineSpacing)

    def accept(self):
        for widget in self.widgets:
            if widget.getFiles()!= ['']:
                self.files += widget.getFiles()
        super(SpectrumComparatorStartDialog, self).accept()

    """def getFileNames(self, btnName):
        files = self.openFileNamesDialog()
        self.files += files
        self.widgets[btnName].setText(',  '.join(files))

    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Open File to Compare", self.startPath,
                                                "Plain Text Files (*txt);;All Files (*)", options=options)
        if files:
            return files"""


class OpenFileWidget(QtWidgets.QWidget):
    def __init__(self, parrent, width, yPos, mode,startPath, title, formats):
        super(OpenFileWidget, self).__init__(parrent)
        self.setGeometry(QtCore.QRect(20, yPos, width, 36))
        #self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setGeometry(QtCore.QRect(0, 5, width-32, 21))

        #self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(width-32, 0, 36, 30))
        self.pushButton.setIcon(QtGui.QIcon('open.png'))
        self.pushButton.setIconSize(QtCore.QSize(24,24))
        #self.pushButton.setGeometry(QtCore.QRect(250, yPos, 26, 26))
        _translate = QtCore.QCoreApplication.translate
        #self.pushButton.setText(_translate(self.objectName(), "O"))
        #self.horizontalLayout.addWidget(self.pushButton)
        self.__startPath = startPath
        self.__title = title
        self.__formats = formats

        """sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)"""
        #lineEdit.setObjectName(name)
        #self.widgets[self.lineEdit.objectName()] = self.lineEdit
        #pushButton.setObjectName(name)
        self.pushButton.clicked.connect(lambda: self.getFileNames(mode))
        #self.buttons[pushButton.objectName()] = pushButton

    def getFileNames(self, mode):
        #files = self.openFileNamesDialog(self.__title, self.__formats)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.__mode = 2
        if mode != 1:
            files, _ = QFileDialog.getOpenFileNames(self, self.__title, self.__startPath, self.__formats, options=options)
            self.lineEdit.setText(',  '.join(files))
        else:
            file, _ = QFileDialog.getOpenFileName(self, self.__title, self.__startPath, self.__formats, options=options)
            self.lineEdit.setText(file)
        #self.__files = files

    #ToDo different Versions:File/Files, title, file formats

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text()

    def getFiles(self):
        return self.lineEdit.text().split(',  ')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gui = SpectrumComparatorStartDialog(None)
    gui.exec_()
    sys.exit(app.exec_())