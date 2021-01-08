from abc import ABC

from src.FragmentHunter.Repository.FragmProperties import *
from src.FragmentHunter.Repository.ModificationProperties import ModificationRepository
from src.Intact_Ion_Search.Repository.ESI_Repository import *


class AbstractService(ABC):
    def __init__(self, repository):
        self.repository = repository

    def makeNew(self):
        pass

    def getAll(self):
        return self.repository.getAll()

    def getAllPatternNames(self):
        return self.repository.getAllPatternNames()

    def getPattern(self, name):
        return self.repository.getPattern(name)

    """def updatePattern(self, *args, **kwargs):
        pass"""

    def savePattern(self, pattern):
        if pattern.getId() == None:
            if pattern.getName() in self.repository.getAllPatternNames():
                raise Exception("Name must be unique!")
            self.repository.createPattern(pattern)
        else:
            self.repository.updatePattern(pattern)

    def getHeaders(self,*args):
        return self.repository.getItemColumns(*args)

    def delete(self, name):
        self.repository.delete(name)





    def close(self):
        self.repository.close()

class IntactIonService(AbstractService):
    def __init__(self):
        super(IntactIonService, self).__init__(ESI_Repository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return IntactPattern("", [["", "", "", "", False]], None)




class FragmentIonService(AbstractService):
    def __init__(self):
        super(FragmentIonService, self).__init__(FragmentationRepository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return FragmentationPattern("", [["", "", "", "", "", "", False]], [["", "", "", "", "", "", False]], None)


class ModificationService(AbstractService):
    def __init__(self):
        super(ModificationService, self).__init__(ModificationRepository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return FragmentationPattern("", [["", "", "", "", "", "", "", False]],
                                    [["", "", "", "", "", "", "", False]], None)

