from PyQt5 import QtWidgets, QtCore



class SimpleMainWindow(QtWidgets.QMainWindow):
    '''
    Used as by TD_searchController, EditorControllers; parent class of StartWindow, IsotopePatternView
    '''
    def __init__(self, parent, title):
        super(SimpleMainWindow, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

    def updateComboBox(self, comboBox, newOptions):
        toAdjust = comboBox.count() - len(newOptions)
        if toAdjust > 0:
            [comboBox.removeItem(i) for i in range(len(newOptions), len(newOptions) + toAdjust)]
        elif toAdjust < 0:
            [comboBox.addItem("") for i in range(-1 * toAdjust)]
        for i, option in enumerate(newOptions):
            comboBox.setItemText(i, self._translate(self.objectName(), option))

    '''def makePushBtn(self, parent, name, fun, geom):
        button = QtWidgets.QPushButton(parent)
        #sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        #sizePolicy.setHeightForWidth(self._defaultButton.sizePolicy().hasHeightForWidth())
        #button.setSizePolicy(sizePolicy)
        #self._defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        button.setText(self._translate(self.objectName(), name))
        button.clicked.connect(fun)
        button.setGeometry(geom)'''

    def createMenuBar(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        #self.fileMenu, self.fileMenuActions = self.createMenu("File", options, 3)


    def createMenu(self, name, options, separatorPosition):
        menu = QtWidgets.QMenu(self.menubar)
        menu.setTitle(self._translate(self.objectName(), name))
        menu.setToolTipsVisible(True)
        menuActions = dict()
        pos = len(options)
        for option, vals in options.items():
            function, tooltip, shortcut = vals
            if separatorPosition != None and pos == separatorPosition:
                menu.addSeparator()
            action = QtWidgets.QAction(self)
            action.setText(self._translate(self.objectName(),option))
            if tooltip != None:
                action.setToolTip(tooltip)
            if shortcut != None:
                action.setShortcut(shortcut)
            action.triggered.connect(function)
            menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        self.menubar.addAction(menu.menuAction())
        return menu, menuActions

