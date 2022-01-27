import os

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from src.resources import autoStart, path


class SimpleMainWindow(QtWidgets.QMainWindow):
    '''
    Used by TD_searchController, EditorControllers; parent class of StartWindow, IsotopePatternView
    '''
    def __init__(self, parent, title):
        super(SimpleMainWindow, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self._centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self._centralwidget)
        self.setWindowIcon(QIcon(os.path.join(path, 'icon.ico')))

    def updateComboBox(self, comboBox, newOptions):
        toAdjust = comboBox.count() - len(newOptions)
        if toAdjust > 0:
            [comboBox.removeItem(i) for i in range(len(newOptions), len(newOptions) + toAdjust)]
        elif toAdjust < 0:
            [comboBox.addItem("") for i in range(-1 * toAdjust)]
        for i, option in enumerate(newOptions):
            comboBox.setItemText(i, self._translate(self.objectName(), option))

    def createMenuBar(self):
        self._menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self._menubar)
        self._menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))

    def createMenu(self, name, options, separatorPosition):
        '''
        Makes a QMenu
        :param name: name of the menu
        :param dict[str,tuple[Callable,str,str]] options: options of the menu (dict of name : (function, tooltip, shortcut))
        :param (int | None) separatorPosition: position of a separator
        '''
        menu = QtWidgets.QMenu(self._menubar)
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
        self._menubar.addAction(menu.menuAction())
        return menu, menuActions

    def makeHelpMenu(self):
        manual = os.path.join(path, 'FAST MS Manual.pdf')
        self.createMenu('Help',{'Manual':(lambda: autoStart(manual),'Open the Manual',None)},None)

