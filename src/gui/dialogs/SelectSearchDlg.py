import os
import shutil
from datetime import datetime
from os.path import join

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from src.gui.GUI_functions import createComboBox
from src.gui.dialogs.AbstractDialogs import AbstractDialog
from src.resources import base_path


class SelectSearchDlgNew(AbstractDialog):
    '''
    Dialog to open saved top-down search/analysis
    '''
    def __init__(self, parent):
        super(SelectSearchDlgNew, self).__init__(parent,'Load Analysis')
        #self.root_path = join(path, 'Saved Analyses')
        self.resize(900, 600)

        #formLayout.setWidget(index+1, QtWidgets.QFormLayout.LabelRole, self._delBtn)
        #formLayout.setWidget(index + 2, QtWidgets.QFormLayout.SpanningRole, self._buttonBox)

        self._layout = QtWidgets.QVBoxLayout(self)
        toolbar = QtWidgets.QToolBar(self)
        self._layout.addWidget(toolbar)
        openBtn = QtWidgets.QAction("Open Root…", self)
        openBtn.triggered.connect(self.choose_root)
        toolbar.addAction(openBtn)
        delBtn = QtWidgets.QAction("Delete", self)
        delBtn.triggered.connect(self.delete)
        toolbar.addAction(delBtn)

        # formLayout = self.makeFormLayout(self)
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setColumnCount(1)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.itemDoubleClicked.connect(self.on_double_click)
        self._layout.addWidget(self._tree)
        self._layout.addWidget(self._buttonBox)

        """for option in self._options:
            if type(option) != dict"""
        # self._comboBox = createComboBox(self, self._options, tooltips=[tup[1] for tup in options])
        # index = self.fill(self, formLayout, ("Enter Name:",), {'name':(self._comboBox, '')})

        """self._delBtn = QtWidgets.QPushButton(self)
        self._delBtn.clicked.connect(self.delete)
        self._delBtn.setText(self._translate(self.objectName(), "Delete"))"""

        self.load_folder(join(base_path, 'Saved Analyses'))
        self.show()

    def choose_root(self):
        rootpath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder", self.root_path)
        if rootpath:
            self.load_folder(rootpath)

    def refresh(self):
        if self.root_path:
            self.populate_tree()

    def load_folder(self, rootPath):
        self.root_path = os.path.abspath(rootPath)
        self.populate_tree()

    def populate_tree(self):
        self._tree.clear()
        if not self.root_path:
            return
        root_item = QtWidgets.QTreeWidgetItem([os.path.basename(self.root_path) or self.root_path])
        root_item.setData(0, Qt.UserRole, self.root_path)
        #root_item.setToolTip(0, self.tooltip_provider.tooltip(self.root_path))
        self._tree.addTopLevelItem(root_item)
        self.add_subfolders(root_item, self.root_path)
        self._tree.expandItem(root_item)

    def add_subfolders(self, parent_item, directory):
        try:
            unsorted = [e for e in os.scandir(directory) if e.is_dir()]
            tooltips = {entry:self.getToolTip(entry) for entry in unsorted}
            sortedEntries = sorted([key for key in unsorted], key=lambda key:tooltips[key][0])
        except PermissionError:
            return
        for entry in sortedEntries:
            item = QtWidgets.QTreeWidgetItem([entry.name])
            item.setData(0, Qt.UserRole, entry.path)
            #item.setToolTip(0, self.tooltip_provider.tooltip(entry.path))
            parent_item.addChild(item)
            # Recursively add only if this folder itself has subfolders
            if self.has_subfolders(entry.path):
                self.add_subfolders(item, entry.path)
            elif entry in tooltips.keys():
                item.setToolTip(0, ", ".join(tooltips[entry]))

    def getToolTip(self, entry):
        infoFile = os.path.join(entry.path, entry.name + "_infos.txt")
        if os.path.isfile(infoFile):
            with open(infoFile) as f:
                content = {}
                counter = 0
                for line in f:
                    if counter > 6:
                        break
                    elif counter == 0:
                        time = datetime.strptime(line.rstrip()[10:26], '%d/%m/%Y %H:%M')
                        content["time"] = str(time)
                    elif counter not in (1, 2):
                        lineL = line.rstrip().split()
                        content[lineL[0]] = lineL[1]
                    counter += 1
            return list(content.values())
        return ["" for _ in range(5)]

    def has_subfolders(self, directory):
        try:
            for name in os.listdir(directory):
                if os.path.isdir(os.path.join(directory, name)):
                    return True
        except Exception:
            pass
        return False

    # ----- interactions -----
    def on_double_click(self, item:QtWidgets.QTreeWidgetItem, col):
        path = item.data(0, Qt.UserRole)
        if self.has_subfolders(path):
            # navigate (new root)
            self.load_folder(path)
        else:
            # leaf → select and close
            self.accept()

    def accept(self):
        item = self._tree.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(self, "No selection", "Please select an analysis.")
            return
        itemPath = item.data(0, Qt.UserRole)
        if self.has_subfolders(itemPath):
            QtWidgets.QMessageBox.information(self, "Not an analysis", "This folder has subfolders. Double-click to navigate into it.")
            return
        self.name = itemPath
        super().accept()

    def delete(self):
        item = self._tree.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(self, "No selection", "Please select an analysis.")
            return
        currentPath = item.data(0, Qt.UserRole)
        if self.has_subfolders(currentPath):
            QtWidgets.QMessageBox.information(self, "Not a leaf",
                                              "This folder has subfolders. Double-click to navigate into it.")
            return
        choice = QtWidgets.QMessageBox.question(self, "Deleting", "Do you really want to permanently delete analysis "
                                                +currentPath+'\nWarning: This cannot be undone',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            shutil.rmtree(currentPath)
            self.refresh()
            """shutil.rmtree(self.getFileNames(name)[4])
            self._deleteFun(currentPath, self._service)
            index = self._options.index(currentPath)
            del self._options[index]
            self._comboBox.removeItem(index)"""

    def getName(self):
        if self.accepted:
            return self.name
        else:
            return None


class SelectSearchDlg(AbstractDialog):
    '''
    Dialog to open saved top-down search/analysis
    '''
    def __init__(self, parent, options, deleteFun, service):
        super().__init__(parent,'Load Analysis')
        self._deleteFun = deleteFun
        self._service = service
        formLayout = self.makeFormLayout(self)
        self._options = [tup[0] for tup in options]
        #self._options = ['search1, 23.01.1992, 08:12', 'search2, 28.01.1992, 08:12']
        self._comboBox = createComboBox(self, self._options, tooltips=[tup[1] for tup in options])
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
