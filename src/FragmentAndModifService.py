from abc import ABC

from src.GeneralRepository.AbstractProperties import PatternWithItems
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

    def savePattern(self, *args, **kwargs):
        pass
    def getHeaders(self,*args):
        return self.repository.getItemColumns(*args)

    def close(self):
        self.repository.close()

class IntactIonService(AbstractService):
    def __init__(self):
        super(IntactIonService, self).__init__(ESI_Repository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return IntactPattern("", [["", "", "", "", False]], None)

    def savePattern(self, pattern):
        if pattern.getId() == None:
            if pattern.getName() in self.repository.getAllPatternNames():
                raise Exception("Name must be unique!")
            self.repository.createPattern(pattern)
        else:
            self.repository.updateFragPattern(pattern)

