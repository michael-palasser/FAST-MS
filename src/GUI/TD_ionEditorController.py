from PyQt5 import QtWidgets

from src.FragmentAndModifService import FragmentIonService
from src.GUI.FragmentsAndModifs import AbstractIonEditorController


class FragmentEditorController(AbstractIonEditorController):
    def __init__(self):
        super(FragmentEditorController, self).__init__(FragmentIonService(),"Edit Fragments")
        self.setUpMenuBar({"New Fragment-Pattern": self.createModification,
                      "Open Fragment-Pattern": self.openModification,
                      "Delete a Fragment-Pattern": self.deleteModification,
                      "Save": self.save, "Save As": self.saveNew, "Close": self.close},
                          {"New Row": self.insertRow}) #"Copy Row":self.copyRow
        yPos = self.createNames(["Name:"], {"name":QtWidgets.QLineEdit(self.centralwidget)}, 20, 150,
                                [self.pattern.getName()])

        #self.table = self.createTableWidget(yPos+50)
        self.mainWindow.show()