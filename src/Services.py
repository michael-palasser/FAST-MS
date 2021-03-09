from abc import ABC

from src.Exceptions import UnvalidInputException
from src.entities.GeneralEntities import Makromolecule, Element, BuildingBlock
from src.repositories.TD_Repositories import *
from src.repositories.MoleculeRepository import MoleculeRepository
from src.repositories.PeriodicTableRepository import PeriodicTableRepository
from src.repositories.SequenceRepository import SequenceRepository
from src.repositories.IntactRepository import *
from src.entities.IonTemplates import *


class AbstractService(ABC):
    def __init__(self, repository, necassaryVals):
        self.repository = repository
        self.necessaryValues = necassaryVals

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
        print(item, self.repository.getIntegers())
        integers=args[0]
        for i,val in enumerate(item):
            if val == "" and i in self.necessaryValues:
                print(i, item[i])
                raise UnvalidInputException(item[0], "No empty values allowed")
            if i in integers:
                if val == '':
                    val = 0
                try:
                    float(val)
                except ValueError:
                    raise UnvalidInputException(item[0], "Number required, Column: " + str(i) + ", " +val)


class AbstractServiceForPatterns(AbstractService, ABC):

    def makeNew(self):
        pass

    def get(self, name):
        return self.repository.getPattern(name)

    def getAllPatternNames(self):
        return self.repository.getAllPatternNames()

    """def updatePattern(self, *args, **kwargs):
        pass"""

    def save(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        self.checkFormatOfItems(pattern.getItems(), elements, self.repository.getIntegers())
        if pattern.getId() == None:
            self.checkIfUnique(pattern)
            self.repository.createPattern(pattern)
        else:
            self.repository.updatePattern(pattern)
        return self.get(pattern.getName())

    def checkIfUnique(self, pattern):
        if pattern.getName() in self.repository.getAllPatternNames():
            raise UnvalidInputException(pattern.getName(), "Name must be unique!")

    def checkFormatOfItems(self, items, *args):
        if len(items)<1:
            raise UnvalidInputException('',"Values empty")
        elements = args[0]
        integers = args[1]
        for item in items:
            formula = self.getFormula(item)
            if formula != None:
                #if (len(formula) < 1 and (item[]:
                #    raise UnvalidInputException(item[0], "molecular formula unvalid")
                for key in formula.keys():
                    if key not in elements:
                        print(item, ", Element: "+ key + " unknown")
                        raise UnvalidInputException(item[0], "Element: " + key + " unknown")
            self.checkFormatOfItem(item,integers)

    def getFormula(self, item):
        pass

    def getPatternWithObjects(self, name, *args):
        '''

        :param name: name of the pattern
        :param args: constructors
        :return:
        '''
        pattern = self.get(name)
        items = []
        for item in pattern.getItems():
            print(item)
            items.append(args[0](item))
        pattern.setItems(items)
        return pattern

    def checkName(self, name):
        if (name == '') or (name[0].islower()) or (len(name) > 1 and any(x.isupper() for x in name[1:])):
            raise UnvalidInputException(name, "First Letter must be uppercase, all other letters must be lowercase!")


    def restart(self):
        patterns = [self.get(name) for name in self.getAllPatternNames()]
        self.repository.deleteTables()
        self.repository.makeTables()
        for pattern in patterns:
            self.repository.createPattern(pattern)


class PeriodicTableService(AbstractServiceForPatterns):
    def __init__(self):
        super(PeriodicTableService, self).__init__(PeriodicTableRepository(), (0,1,2))

    def makeNew(self):
        return Element("", 2*[["", "", ""]], None)

    def save(self, pattern):
        self.checkName(pattern.getName())
        self.checkFormatOfItems(pattern.getItems(),None, self.repository.getIntegers())
        if pattern.getId() == None:
            self.checkIfUnique(pattern)
            self.repository.createPattern(pattern)
        else:
            self.repository.updatePattern(pattern)
        return self.get(pattern.getName())

    def checkName(self, name):
        super(PeriodicTableService, self).checkName(name)
        if any(char.isdigit() for char in name):
            raise UnvalidInputException(name, "Element name must not contain numbers!")

    def getFormula(self, item):
        return None

    '''def checkFormatOfItem(self, item, *args):
        for val in item:
            try:
                if val in self.repository.getIntegers():
                    float(val)
            except ValueError:
                raise UnvalidInputException(item[0], "Number required: " + val)'''

    def getElements(self, elements):
        """elementDict = dict()
        for elem in elements:
            isotopeTable = np.array(sorted(self.repository.getPattern(elem), key=lambda tup: tup[1], reverse=True)
                                    , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                             ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])
            self.repository.getPattern(elem)
            elementDict[elem] = """
        return {elem:self.repository.getPattern(elem).getItems() for elem in elements}

class MoleculeService(AbstractServiceForPatterns):
    def __init__(self):
        super(MoleculeService, self).__init__(MoleculeRepository(), (0,1))

    def makeNew(self):
        return Makromolecule("", "", "", 10*[["", "", 0.,0.]], None)

    def getFormula(self, item):
        return BuildingBlock(item).getFormula()

    def save(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        for key in pattern.getFormula().keys():
            if key not in elements:
                raise UnvalidInputException(pattern.getName(), "Element: " + key + " unknown")
        [self.checkName(bb[0]) for bb in pattern.getItems()]
        self.checkFormatOfItems(pattern.getItems(),elements, self.repository.getIntegers())
        pattern = super(MoleculeService, self).save(pattern)
        elementRep.close()
        return pattern

    '''def checkName(self, name):
        if (name[0].islower() or (len(name) > 1 and any(x.isupper() for x in name[1:]))):
            raise UnvalidInputException(name, "First Letter must be uppercase, all other letters must be lowercase!")'''

    """def getItemDict(self, name):
        itemDict = dict()
        items = self.get(name).getItems()
        for item in items:
            itemDict[item[0]] = BuildingBlock(item[0],item[1], item[2])
        return itemDict"""


class SequenceService(AbstractService):
    def __init__(self):
        super(SequenceService, self).__init__(SequenceRepository(),(0,1,2))

    def makeNew(self):
        return ("", "", "")

    def get(self,name):
        return self.repository.getSequence(name)

    def getSequences(self):
        return self.repository.getAllSequences()

    def getAllSequenceNames(self):
        return self.repository.getAllSequenceNames()

    def save(self, sequences):
        newNames = [sequence.getName() for sequence in sequences]
        savedNames = self.repository.getAllSequenceNames()
        [self.repository.delete(savedName) for savedName in savedNames if savedName not in newNames]
        moleculeRepository = MoleculeRepository()
        molecules = moleculeRepository.getAllPatternNames()
        for sequence in sequences:
            """if sequenceList.getMolecule() not in molecules:
                raise UnvalidInputException(sequenceList.getName(),sequenceList.getMolecule()+" unknown")
            monomereNames = [item[0] for item in moleculeRepository.getPattern(sequenceList.getMolecule()).getItems()]
            for link in sequenceList.getSequenceList():
                if link not in monomereNames:
                    raise UnvalidInputException(sequenceList.getName(),"Problem in Sequence: "+ link + " unknown")"""
            if sequence.getMolecule() not in moleculeRepository.getAllPatternNames():
                raise UnvalidInputException(sequence.getName(), "Molecule " + sequence.getMolecule()+' unknown')
            self.checkFormatOfItem(sequence, molecules,
                            [mon[0] for mon in moleculeRepository.getPattern(sequence.getMolecule()).getItems()])
            if sequence.getName() in savedNames:
                self.repository.updateSequence(sequence)
            else:
                self.repository.createSequence(sequence)
        moleculeRepository.close()

    def checkFormatOfItem(self, item, *args):
        molecules, monomereNames = args[0], args[1]
        if item.getMolecule() not in molecules:
            raise UnvalidInputException(item.getName(), item.getMolecule() + " unknown")
        sequList = item.getSequenceList()
        if len(sequList)<1:
            raise UnvalidInputException(item.getName(), "Problem with Sequence: Format incorrect")
        for link in item.getSequenceList():
            if link not in monomereNames:
                raise UnvalidInputException(item.getName(), "Problem in Sequence: " + link + " unknown")


class FragmentIonService(AbstractServiceForPatterns):
    def __init__(self):
        super(FragmentIonService, self).__init__(FragmentationRepository(),(0,5,6))

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return FragmentationPattern("", '', 10*[["", "", "", "", "", +1, False]],
                                    10*[["", "", "", "", "", False]], None)

    def save(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        self.checkFormatOfItems(pattern.getItems(), elements, self.repository.getIntegers()[0])
        for item in pattern.getItems():
            print(item[5])
            if int(item[5]) not in [1,-1]:
                raise UnvalidInputException(item, "Direction must be 1 or -1 and not " + str(item[5]))
        self.checkFormatOfItems(pattern.getItems2(), elements, self.repository.getIntegers()[1])
        if pattern.getPrecursor() not in [item[0] for item in pattern.getItems2() if item[5]]==1:
            raise UnvalidInputException(pattern.getPrecursor(), 'Precursor not found or not enabled')
        """for key in pattern.getFormula().keys():
            if key not in elements:
                raise UnvalidInputException(pattern.getName(), "Element: "+ key + " unknown")"""
        pattern = super(FragmentIonService, self).save(pattern)
        elementRep.close()
        return pattern

    def getFormula(self, item):
        return PrecursorItem(item).getFormula() #Not necessary to differentiate between Precursor- and FragItems

    def getPatternWithObjects(self, name, *args):
        pattern = super(FragmentIonService, self).getPatternWithObjects(name, FragItem)
        #precItems = [PrecursorItem(("", "", "", "", 0, True))]
        precItems = []
        for item in pattern.getItems2():
            precItems.append(PrecursorItem(item))
        pattern.setItems2(precItems)
        return pattern


class ModificationService(AbstractServiceForPatterns):
    def __init__(self):
        super(ModificationService, self).__init__(ModificationRepository(), (0,6,7))

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return ModificationPattern("", "", 10*[["", "", "", "", "", "", True, False]],
                                    5*[[""]], None)

    def save(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        self.checkFormatOfItems(pattern.getItems(), elements, self.repository.getIntegers()[0])
        pattern = super(ModificationService, self).save(pattern)
        elementRep.close()
        return pattern

    def getFormula(self, item):
        #return ModifiedItem(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]).getFormula()
        return ModifiedItem(item).getFormula()

    def getAllPatternNames(self):
        return ["-"] + super(ModificationService, self).getAllPatternNames()

    def getPatternWithObjects(self, name, *args):
        if name == '-':
            return ModificationPattern("", "", [],[], None)
        else:
            return super(ModificationService, self).getPatternWithObjects(name, ModifiedItem)



class IntactIonService(AbstractServiceForPatterns):
    def __init__(self):
        super(IntactIonService, self).__init__(IntactRepository(),(0,4))

    def makeNew(self):
        # return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return IntactPattern("", 10 * [["", "", "", "", False]], None)

    def getFormula(self, item):
        return IntactModification(item).getFormula()

    """def getPatternWithObjects(self, name, constructor):"""


    """def getPatternWithObjects(self, name):
        pattern = self.repository.getPattern(name)
        pattern = self.get('name', name)
        return IntactPattern(pattern[1], pattern[2], pattern[3], self.getItemsAsObjects(pattern[0]), pattern[0])

    def getItemsAsObjects(self, patternId):
        listOfItems = list()
        for item in super(IntactRepository, self).getItems(patternId, [key for key in self._itemDict.keys()][0]):
            listOfItems.append(IntactModification(item[1], item[2], item[3], item[4], item[5]))
        return listOfItems"""

    '''def save(self, pattern):
        elementRep = PeriodicTableRepository()
        elements = PeriodicTableRepository().getAllPatternNames()
        for key in pattern.getFormula().keys():
            if key not in elements:
                raise UnvalidInputException(pattern.getName(), "Element: " + key + " unknown")
        pattern = super(IntactIonService, self).save(pattern)
        elementRep.close()
        return pattern'''
