from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog


class OpenFileWidget(QtWidgets.QWidget):
    def __init__(self, parent, mode,startPath, title, formats):
        super(OpenFileWidget, self).__init__(parent)
        #self.setGeometry(QtCore.QRect(20, yPos, width, 36))
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0,0,0,0)
        self.lineEdit = QtWidgets.QLineEdit(self)

        #self.lineEdit.setGeometry(QtCore.QRect(0, 5, width-32, 21))

        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton = QtWidgets.QPushButton(self)
        #self.pushButton.setGeometry(QtCore.QRect(width-32, 0, 36, 30))
        self.pushButton.setIcon(QtGui.QIcon('open.png'))
        self.pushButton.setIconSize(QtCore.QSize(26,26))
        self.pushButton.setMaximumSize(26,26)
        #self.pushButton.setGeometry(QtCore.QRect(250, yPos, 26, 26))
        #_translate = QtCore.QCoreApplication.translate
        #self.pushButton.setText(_translate(self.objectName(), "O"))
        self.horizontalLayout.addWidget(self.pushButton)
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
        if mode == 2:
            files, _ = QFileDialog.getOpenFileNames(self, self.__title, self.__startPath, self.__formats, options=options)
            self.lineEdit.setText(',  '.join(files))
        elif mode == 1:
            file, _ = QFileDialog.getOpenFileName(self, self.__title, self.__startPath, self.__formats, options=options)
            self.lineEdit.setText(file)
        else:
            dir = QFileDialog.getExistingDirectory(self, self.__title, self.__startPath)
            print(dir)
            if dir:
                dir = QtCore.QDir.toNativeSeparators(dir)
                print(dir)
            self.lineEdit.setText(dir)
        #self.__files = files

    #ToDo different Versions:File/Files, title, file formats

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text()

    def getFiles(self):
        return self.lineEdit.text().split(',  ')


class BoxUpdateWidget(QtWidgets.QWidget):
    def __init__(self, parent, options):
        super(BoxUpdateWidget, self).__init__(parent)
        self.setContentsMargins(0,0,0,0)
        self._translate = QtCore.QCoreApplication.translate
        self._horizontalLayout = QtWidgets.QHBoxLayout(self)
        self._horizontalLayout.setContentsMargins(0,0,0,0)
        self._comboBox = QtWidgets.QComboBox(self)
        for i, option in enumerate(options):
            self._comboBox.addItem('')
            self._comboBox.setItemText(i, self._translate(self.objectName(), option))
        self._horizontalLayout.addWidget(self._comboBox)

        self._button = QtWidgets.QPushButton(self)
        #sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
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
            self._comboBox.setItemText(i, self._translate(self.objectName(), option))