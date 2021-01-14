from abc import ABC

from src.Entities.GeneralEntities import Makromolecule, Element, Monomere
from src.Exceptions import InvalidInputException
from src.Repositories.TD_Repositories import *
from src.Repositories.MoleculeRepository import MoleculeRepository
from src.Repositories.PeriodicTableRepository import PeriodicTableRepository
from src.Repositories.SequenceRepository import SequenceRepository, Sequence
from src.Repositories.IntactRepository import *


class AbstractService(ABC):
    def __init__(self, repository):
        self.repository = repository

    def getHeaders(self):
        return self.repository.getItemColumns()

    def get(self, name):
        pass

    def getBoolVals(self):
        return self.repository.getBoolVals()

    def delete(self, name):
        self.repository.delete(name)

    def close(self):
        self.repository.close()


    def checkFormatOfItem(self, item, *args):
        for val in item:
            try:
                if val in self.repository.getIntegers():
                    float(val)
                """elif val in self._boolVals:
                    if not (0 <= val <= 1):
                        raise ValueError"""
            except ValueError:
                raise InvalidInputException(item[0],"Number required: " +val)



class AbstractServiceForPatterns(AbstractService, ABC):

    def makeNew(self):
        pass

    def get(self, name):
        return self.repository.getPattern(name)

    def getAllPatternNames(self):
        return self.repository.getAllPatternNames()

    """def updatePattern(self, *args, **kwargs):
        pass"""

    def savePattern(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        for item in pattern.getItems():
            self.checkFormatOfItem(item, elements)
        if pattern.getId() == None:
            if pattern.getName() in self.repository.getAllPatternNames():
                raise InvalidInputException(pattern.getName(), "Name must be unique!")
            self.repository.createPattern(pattern)
        else:
            self.repository.updatePattern(pattern)

    def checkFormatOfItem(self, item, *args):
        print("e",item)
        elements = args[0]
        for key in self.getFormula(item).keys():
            if key not in elements:
                raise InvalidInputException(item.getName(), "Element: "+ key + " unknown")
        super(AbstractServiceForPatterns, self).checkFormatOfItem(item)

    def getFormula(self, item):
        pass


class PeriodicTableService(AbstractServiceForPatterns):
    def __init__(self):
        super(PeriodicTableService, self).__init__(PeriodicTableRepository())

    def makeNew(self):
        return Element("", 2*[["", "", ""]], None)

    def savePattern(self, pattern):
        self.checkName(pattern.getName())
        super(PeriodicTableService, self).savePattern(pattern)

    def checkName(self, name):
        if (name[0].islower() or (len(name) > 1 and any(x.isupper() for x in name[1:]))):
            raise InvalidInputException(name,"First Letter must be uppercase, all other letters must be lowercase!")


    def checkFormatOfItem(self, item, *args):
        for val in item:
            try:
                if val in self.repository.getIntegers():
                    float(val)
            except ValueError:
                raise InvalidInputException(item[0],"Number required: " +val)


class MoleculeService(AbstractServiceForPatterns):
    def __init__(self):
        super(MoleculeService, self).__init__(MoleculeRepository())

    def makeNew(self):
        return Makromolecule("", 10*[["", ""]], None)

    def getFormula(self, item):
        return Monomere(item[0], item[1]).getFormula()


    def savePattern(self, pattern):
        for monomere in pattern.getItems():
            print(monomere)
            self.checkName(monomere[0])
        super(MoleculeService, self).savePattern(pattern)

    def checkName(self, name):
        if (name[0].islower() or (len(name) > 1 and any(x.isupper() for x in name[1:]))):
            raise InvalidInputException(name,"First Letter must be uppercase, all other letters must be lowercase!")


class SequenceService(AbstractService):
    def __init__(self):
        super(SequenceService, self).__init__(SequenceRepository())

    def makeNew(self):
        return ("", "", "")

    def get(self,name):
        return self.repository.getSequence(name)

    def getSequences(self):
        return self.repository.getAllSequences()

    def getAllSequenceNames(self):
        return self.getAllSequenceNames()

    def save(self, sequences):
        newNames = [sequence.getName() for sequence in sequences]
        savedNames = self.repository.getAllSequenceNames()
        [self.repository.delete(savedName) for savedName in savedNames if savedName not in newNames]
        moleculeRepository = MoleculeRepository()
        molecules = moleculeRepository.getAllPatternNames()
        print(molecules)
        for sequence in sequences:
            """if sequence.getMolecule() not in molecules:
                raise InvalidInputException(sequence.getName(),sequence.getMolecule()+" unknown")
            monomereNames = [item[0] for item in moleculeRepository.getPattern(sequence.getMolecule()).getItems()]
            for link in sequence.getSequence():
                if link not in monomereNames:
                    raise InvalidInputException(sequence.getName(),"Problem in Sequence: "+ link + " unknown")"""
            print(sequence.getMolecule())#, moleculeRepository.getPattern(sequence.getMolecule()),moleculeRepository.getPattern(sequence.getMolecule()).getItems())
            self.checkFormatOfItem(sequence, molecules,
                            [mon[0] for mon in moleculeRepository.getPattern(sequence.getMolecule()).getItems()])
            if sequence.getName() in savedNames:
                self.repository.updateSequence(sequence)
            else:
                self.repository.createSequence(sequence)

    def checkFormatOfItem(self, item, *args):
        molecules, monomereNames = args[0], args[1]
        if item.getMolecule() not in molecules:
            raise InvalidInputException(item.getName(), item.getMolecule() + " unknown")
        for link in item.getSequence():
            if link not in monomereNames:
                raise InvalidInputException(item.getName(),"Problem in Sequence: "+ link + " unknown")


class IntactIonService(AbstractServiceForPatterns):
    def __init__(self):
        super(IntactIonService, self).__init__(ESI_Repository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return IntactPattern("", 10*[["", "", "", "", False]], None)


    def getFormula(self, item):
        return IntactModification(item[0], item[1], item[2], item[3], item[4]).getFormula()

class FragmentIonService(AbstractServiceForPatterns):
    def __init__(self):
        super(FragmentIonService, self).__init__(FragmentationRepository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return FragmentationPattern("", 10*[["", "", "", "", "", False]],
                                    [["start", "", "", "", "", True]]+9*[["", "", "", "", "", False]], None)

    def savePattern(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        for item in pattern.getItems2():
            self.checkFormatOfItem(item, elements)
        elementRep.close()
        super(FragmentIonService, self).savePattern(pattern)

    def getFormula(self, item):
        #return FragItem(item[0], item[1], item[2], item[3], item[4], item[5]).getFormula()
        return FragItem(item).getFormula()

class ModificationService(AbstractServiceForPatterns):
    def __init__(self):
        super(ModificationService, self).__init__(ModificationRepository())

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return ModificationPattern("", "", 10*[["", "", "", "", "", "", True, False]],
                                    5*[[""]], None)

    def savePattern(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        for item in pattern.getItems2():
            self.checkFormatOfItem(item, elements)
        elementRep.close()
        super(ModificationService, self).savePattern(pattern)

    def getFormula(self, item):
        return ModifiedItem(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]).getFormula()