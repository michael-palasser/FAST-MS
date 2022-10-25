import re
from abc import ABC

from src.Exceptions import InvalidInputException
from src.entities.GeneralEntities import Macromolecule, Element, BuildingBlock, Sequence
from src.resources import processTemplateName
from src.repositories.sql.TD_Repositories import *
from src.repositories.sql.MoleculeRepository import MoleculeRepository
from src.repositories.sql.PeriodicTableRepository import PeriodicTableRepository
from src.repositories.sql.SequenceRepository import SequenceRepository
from src.repositories.sql.IntactRepository import *
from src.entities.IonTemplates import *


class AbstractService(ABC):
    '''
    Abstract service class for simple entities. Parent class of SequenceService and AbstractServiceForPatterns
    '''
    def __init__(self, repository, necassaryVals):
        '''
        :param (AbstractRepository) repository: _repository
        :param (list[int] | tuple[int]) necassaryVals: specifies (by indices) which columns have to be filled to save/update a table
        '''
        self._repository = repository
        self._necessaryValues = necassaryVals

    def getHeaders(self):
        return self._repository.getItemColumns()

    def get(self, name):
        pass

    def getBoolVals(self):
        return self._repository.getBoolVals()

    def delete(self, name):
        self._repository.delete(name)

    def close(self):
        self._repository.close()


    def checkFormatOfItem(self, item, *args):
        '''
        Checks if the format of an item is correct
        :param (tuple[Any]) item: item with stored values
        :param (tuple[int] | False) args: indices which should be numerical
        :raises InvalidInputException: if necessary value is empty or a numerical value is not numerical
        '''
        #print(item, self._repository.getIntegers())
        numericals=args[0]
        for i,val in enumerate(item):
            if (val == "" or val == '-') and i in self._necessaryValues:
                print(i, item[i])
                raise InvalidInputException(item[0], "No empty values allowed")
            if i in numericals:
                if val == '':
                    val = 0
                try:
                    float(val)
                except ValueError:
                    raise InvalidInputException(item[0], "Number required, Column: " + str(i) + ", " + val)


class AbstractServiceForPatterns(AbstractService, ABC):
    '''
    Abstract service class for entities which contain other entities. Parent class of FragmentationService,
    IntactIonService, ModificationService, MoleculeService and PeriodicTableService
    '''

    def makeNew(self):
        pass

    def get(self, name):
        return self._repository.getPattern(name)

    def getAllPatternNames(self):
        return self._repository.getAllPatternNames()

    """def updatePattern(self, *args, **kwargs):
        pass"""

    def save(self, pattern):
        '''
        Saves a pattern
        :param (PatternWithItems) pattern: pattern which should be saved
        :return: (PatternWithItems) saved pattern
        '''
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        self.checkFormatOfItems(pattern.getItems(), elements, self._repository.getIntegers())
        self.checkIfUnique(pattern)
        if pattern.getId() == None:
            self._repository.createPattern(pattern)
        else:
            self._repository.updatePattern(pattern)
        return self.get(pattern.getName())

    def checkIfUnique(self, pattern):
        '''
        Checks if name of a pattern is unique (not already stored in the database)
        :param (PatternWithItems) pattern: pattern
        :raises InvalidInputException: if name not unique
        '''
        if pattern.getName() in self._repository.getAllPatternNames():
            if pattern.getId() != self._repository.getPattern(pattern.getName()).getId():
                raise InvalidInputException(pattern.getName(), "Name must be unique!")

    def checkFormatOfItems(self, items, *args):
        '''
        Checks the format of the items of a pattern
        :param (list[tuple[Any]] | list[list[Any]]) items: list of tuples (=items) with values to check
        :param (args[0] = (list[str] | None), args[1] = (list[int])) args: list of stored elements, list of value
            indices which should have a numeric format
        :raises InvalidInputException: if format incorrect (empty values, unknown elements or incorrect format of
            numeric values)
        '''
        if len(items)<1:
            raise InvalidInputException('', "Values empty")
        elements = args[0]
        numericals = args[1]
        names = []
        for item in items:
            name = item[0]
            if name in names:
                raise InvalidInputException(name, "No duplicates allowed")
            names.append(name)
            formula = self.getFormula(item)
            if formula != None:
                #if (len(formula) < 1 and (item[]:
                #    raise InvalidInputException(item[0], "molecular formula unvalid")
                for key in formula.keys():
                    if key not in elements:
                        print(item, ", Element: "+ key + " unknown")
                        raise InvalidInputException(name, "Element: " + key + " unknown")
            self.checkFormatOfItem(item,numericals)

    def getFormula(self, item):
        return {}

    def getPatternWithObjects(self, name, *args):
        '''
        Returns a pattern with items as generated objects (not tuples)
        :param (str) name: name of the pattern
        :param (callable) args: constructor of the object
        :return: (PatternWithItems) pattern
        '''
        pattern = self.get(name)
        items = []
        for item in pattern.getItems():
            items.append(args[0](item))
        pattern.setItems(items)
        return pattern

    def checkName(self, name):
        '''
        Checks the format of a name.
        The name must start with an uppercase letter and must not contain any additional uppercase letters.
        :param (str) name: name to be checked
        :raises InvalidInputException: if format is incorrect
        '''
        if (name == '') or (name[0].islower()) or (len(name) > 1 and any(x.isupper() for x in name[1:])):
            raise InvalidInputException(name, "First Letter must be uppercase, all other letters must be lowercase!")
        specialChars = [char for char in re.findall('[@_!#$%^&*()<>?/|}{~:]', name) if char!='']
        if len(specialChars) >0 :
            raise InvalidInputException(name, "Character(s): " + ', '.join(specialChars) + ' are not allowed')


    def restart(self):
        '''
        Restarts a database if a database should be altered:
        Reads all entries
        Deletes all entries and all tables
        Creates new tables from the read values with the updated createPattern function
        '''
        patterns = [self.get(name) for name in self.getAllPatternNames()]
        self._repository.deleteTables()
        self._repository.makeTables()
        for pattern in patterns:
            self._repository.createPattern(pattern)


class PeriodicTableService(AbstractServiceForPatterns):
    '''
    Service handling a PeriodicTableRepository and Element entities.
    '''
    def __init__(self):
        super(PeriodicTableService, self).__init__(PeriodicTableRepository(), (0,1,2))

    def makeNew(self):
        return Element("", 2*[["", "", ""]], None)

    def save(self, pattern):
        '''
        Saves an element
        :param (Element) pattern: element which should be saved
        :return: (Element) saved element
        '''
        #print('id', pattern.getId())
        self.checkName(pattern.getName())
        formatedItems = []
        for item in pattern.getItems():
            formatedItems.append(float(val) for val in item)
        self.checkFormatOfItems(pattern.getItems(), None, self._repository.getIntegers())
        self.checkIfUnique(pattern)
        if pattern.getId() == None:
            self._repository.createPattern(pattern)
        else:
            self._repository.updatePattern(pattern)
        return self.get(pattern.getName())

    def checkFormatOfItems(self, items, *args):
        super(PeriodicTableService, self).checkFormatOfItems(items, *args)
        sumAbundances = 0
        nucNums = []
        for item in items:
            sumAbundances+=item[2]
            if item[0] in nucNums:
                raise InvalidInputException(item[0], "one nucleon number must not occur more than once")
            if isinstance(item[0], float):
                raise InvalidInputException(item[0], "nucleon number must be an integer")
            nucNums.append(item[0])
        if sumAbundances > 1 or sumAbundances <0.98:
            message = '+'.join([str(item[2]) for item in items]) + " = " + str(sumAbundances)
            raise InvalidInputException(message, "Relative abundances do not sum up to 1")

    def checkName(self, name):
        '''
        Checks the format of a name.
        The name must start with an uppercase letter, must not contain any additional uppercase letters or numbers.
        :param (str) name: name to be checked
        :raises InvalidInputException: if format is incorrect
        '''
        super(PeriodicTableService, self).checkName(name)
        if any(char.isdigit() for char in name):
            raise InvalidInputException(name, "Element name must not contain numbers!")

    def getFormula(self, item):
        return {}

    def checkFormatOfItem(self, item, *args):
        super(PeriodicTableService, self).checkFormatOfItem(item, *args)
        for val in item:
            if float(val)<0:
                raise InvalidInputException(val, 'No negative values allowed')

    '''def checkFormatOfItem(self, item, *args):
        for val in item:
            try:
                if val in self._repository.getIntegers():
                    float(val)
            except ValueError:
                raise InvalidInputException(item[0], "Number required: " + val)'''

    def getElements(self, elements):
        '''
        Returns elements from the database
        :param (list[str]) elements: list of element names
        :return: (dict[str,Element]) dictionary of elements {element name: element}
        '''
        """elementDict = dict()
        for elem in elements:
            isotopeTable = np.array(sorted(self._repository.getPattern(elem), key=lambda tup: tup[1], reverse=True)
                                    , dtype=[('index', np.float64), ('nr', np.float64), ('nrIso', np.float64),
                                             ('relAb', np.float64), ('mass', np.float64), ('M+', np.float64)])
            self._repository.getPattern(elem)
            elementDict[elem] = """
        return {elem:self._repository.getPattern(elem).getItems() for elem in elements}

    def getAllElements(self):
        return {elem:self._repository.getPattern(elem).getItems() for elem in self.getAllPatternNames()}


class MoleculeService(AbstractServiceForPatterns):
    '''
    Service handling a MoleculeRepository and Macromolecule entities.
    '''
    def __init__(self):
        super(MoleculeService, self).__init__(MoleculeRepository(), (0,1))

    def makeNew(self):
        return Macromolecule("", "", "", 10 * [["", "", 0., 0.]], None)

    def getFormula(self, item):
        '''
        Returns the molecular formula of a building block
        :param (tuple[str, str, float, float]) item: corresponding building block
        :return: (MolecularFormula) formula
        '''
        return BuildingBlock(item).getFormula()

    def save(self, pattern):
        '''
        Saves a molecule
        :param (Macromolecule) pattern: molecule which should be saved
        :return: (Macromolecule) saved molecule
        '''
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        for key in pattern.getFormula().keys():
            if key not in elements:
                raise InvalidInputException(pattern.getName(), "Element: " + key + " unknown")
        [self.checkName(bb[0]) for bb in pattern.getItems()]
        self.checkFormatOfItems(pattern.getItems(), elements, self._repository.getIntegers())
        pattern = super(MoleculeService, self).save(pattern)
        elementRep.close()
        return pattern

    def checkName(self, name):
        super(MoleculeService, self).checkName(name)
        if any(char.isdigit() for char in name):
            raise InvalidInputException(name, "Building block name must not contain numbers!")
        '''if (name[0].islower() or (len(name) > 1 and any(x.isupper() for x in name[1:]))):
            raise InvalidInputException(name, "First Letter must be uppercase, all other letters must be lowercase!")'''

    """def getItemDict(self, name):
        itemDict = dict()
        items = self.get(name).getItems()
        for item in items:
            itemDict[item[0]] = BuildingBlock(item[0],item[1], item[2])
        return itemDict"""


class SequenceService(AbstractService):
    '''
    Service handling a SequenceRepository and Sequence entities.
    '''
    def __init__(self):
        super(SequenceService, self).__init__(SequenceRepository(),(0,1,2))

    def makeNew(self):
        return ("", "", "")

    def get(self,name):
        return self._repository.getSequence(name)

    def getSequences(self):
        return self._repository.getAllSequences()

    def getAllSequenceNames(self):
        return self._repository.getAllSequenceNames()

    def save(self, sequTuples):
        '''
        Saves the sequences
        :param (list[tuple[str,str,str]]) sequTuples: tuples (name,sequence,molecule name) with sequence information
            which should be saved/updated
        '''
        #newNames = [sequence[0] for sequence in sequTuples]
        newNames=[]
        for sequTup in sequTuples:
            if sequTup[0] in newNames:
                raise InvalidInputException(sequTup[0], "No duplicates allowed")
            newNames.append(sequTup[0])
        savedNames = self._repository.getAllSequenceNames()
        [self._repository.delete(savedName) for savedName in savedNames if savedName not in newNames]
        moleculeRepository = MoleculeRepository()
        molecules = moleculeRepository.getAllPatternNames()
        bbs = {}
        for molecule in molecules:
            bbs[molecule] = [bb[0] for bb in moleculeRepository.getPattern(molecule).getItems()]
        for sequTup in sequTuples:
            """if sequenceList.getMolecule() not in molecules:
                raise InvalidInputException(sequenceList.getName(),sequenceList.getMolecule()+" unknown")
            monomereNames = [item[0] for item in moleculeRepository.getPattern(sequenceList.getMolecule()).getItems()]
            for link in sequenceList.getSequenceList():
                if link not in monomereNames:
                    raise InvalidInputException(sequenceList.getName(),"Problem in Sequence: "+ link + " unknown")"""
            '''sequName,sequString,moleculeName = sequTup[0],sequTup[1],sequTup[2]
            if sequString[0].islower():
                raise InvalidInputException(sequString,
                                            "Incorrect format of sequence, first letter must not be lowercase")'''
            #sequence = Sequence(sequName,sequString,moleculeName, None)
            sequence = self.checkFormatOfItem(sequTup, bbs)
            if sequence.getName() in savedNames:
                self._repository.updateSequence(sequence)
            else:
                self._repository.createSequence(sequence)
        moleculeRepository.close()

    def checkFormatOfItem(self, item, *args):
        '''
        Checks the values of a sequence
        :param (tuple[str,str,str]) item: tuple (name,sequence,molecule name) with sequence information
        :param (dict[str,list[str])) args: dict of molecule names (keys) and names of stored building blocks
        :raises InvalidInputException: if format incorrect (empty values, molecule unknown or sequence contains an
            unknown building block)
        :return (Sequence): sequence
        '''
        sequName, sequString, moleculeName = item[0], item[1], item[2]
        molecules  = args[0].keys()
        if sequName == '' or sequName == '-':
            raise InvalidInputException(sequName,"Name incorrect")
        if len(sequString)<1:
            raise InvalidInputException(sequName, "Empty sequence")
        if sequString[0].islower():
            raise InvalidInputException(sequString,
                                        "Incorrect format of sequence, first letter must not be lowercase")
        if moleculeName not in molecules:
            raise InvalidInputException(sequName, "Molecule " + moleculeName + ' unknown')
        monomereNames = args[0][moleculeName]
        sequence = Sequence(sequName,sequString,moleculeName, None)
        sequList = sequence.getSequenceList()
        if len(sequList)<1:
            raise InvalidInputException(sequName, "Problem with Sequence: Format incorrect")
        for link in sequList:
            if link not in monomereNames:
                raise InvalidInputException(sequName, "Problem in Sequence: " + link + " unknown")
        if ('+' in sequName) or ('-' in sequName):
            raise InvalidInputException(sequName, 'Sequence name must not contain "+" or "-"')
        return sequence



class FragmentationService(AbstractServiceForPatterns):
    '''
    Service handling a FragmentationRepository and FragmentationPattern entities.
    '''
    def __init__(self):
        super(FragmentationService, self).__init__(FragmentationRepository(), (0, 5, 6))

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return FragmentationPattern("", '', 10*[["", "", "", "", "", +1, False]],
                                    10*[["", "", "", "", "", False]], None)

    def save(self, pattern):
        '''
        Saves a fragmentation pattern
        :param (FragmentationPattern) pattern: fragmentation pattern that should be saved
        :return: (FragmentationPattern) saved fragmentation pattern
        '''
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        self.checkFormatOfItems(pattern.getItems(), elements, self._repository.getIntegers()[0])
        for item in pattern.getItems():
            if processTemplateName(item[0])[-1].isnumeric():
                raise InvalidInputException(item[0], "\nThe last character of a fragment's name must not be numeric!")
            if int(item[5]) not in [1,-1]:
                raise InvalidInputException(item[0], "\nDirection must be 1 or -1 and not " + str(item[5]))
        self.checkFormatOfItems(pattern.getItems2(), elements, self._repository.getIntegers()[1])
        if pattern.getPrecursor() not in [item[0] for item in pattern.getItems2() if item[5]==1]:
            raise InvalidInputException(pattern.getPrecursor(), 'Precursor not found or not enabled')
        """for key in pattern.getFormula().keys():
            if key not in elements:
                raise InvalidInputException(pattern.getName(), "Element: "+ key + " unknown")"""
        pattern = super(FragmentationService, self).save(pattern)
        elementRep.close()
        return pattern

    def getFormula(self, item):
        '''
        Returns the molecular formula of a fragment template (FragItem or PrecursorItem)
        :param (tuple[str,str,str,str,int|str,int]) item: corresponding fragment template
        :return: (MolecularFormula) formula
        '''
        return PrecursorItem(item).getFormula() #Not necessary to differentiate between Precursor- and FragItems

    def getPatternWithObjects(self, name, *args):
        '''
        Returns a fragmentation pattern with lists of FragItem and PrecursorItem objects
        :param (str) name: name of the fragmentation pattern
        :param (callable) args: not used
        :return: (FragmentationPattern) fragmentation pattern
        '''
        pattern = super(FragmentationService, self).getPatternWithObjects(name, FragItem)
        #precItems = [PrecursorItem(("", "", "", "", 0, True))]
        precItems = []
        for item in pattern.getItems2():
            precItems.append(PrecursorItem(item))
        pattern.setItems2(precItems)
        return pattern


class ModificationService(AbstractServiceForPatterns):
    '''
    Service handling a ModificationRepository and ModificationPattern entities.
    '''
    def __init__(self):
        super(ModificationService, self).__init__(ModificationRepository(), (0,6,7))

    def makeNew(self):
        #return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return ModificationPattern("", "", 10*[["", "", "", "", "", "", True, False]],
                                    5*[[""]], None)

    def save(self, pattern):
        '''
        Saves a modification pattern
        :param (ModificationPattern) pattern: modification pattern that should be saved
        :return: (ModificationPattern) saved modification pattern
        '''
        elementRep = PeriodicTableRepository()
        elements = elementRep.getAllPatternNames()
        self.checkFormatOfItems(pattern.getItems(), elements, self._repository.getIntegers()[0])
        checkedItems = []
        mod = pattern.getModification()
        if mod[0] not in ['+', '-']:
            pattern.setModification('+'+mod)
        for item in pattern.getItems():
            checkedItem = item
            if item[0][0] not in ['+','-']:
                checkedItem = ['+' + item[0]] + [elem for elem in item[1:]]
            checkedItems.append(checkedItem)

        pattern.setItems(checkedItems)
        modification = pattern.getModification()
        if modification[0] not in ['+','-']:
            pattern.setModification('+'+modification)
        if modification not in [item[0] for item in pattern.getItems()]:
            raise InvalidInputException(modification,'Precursor modification must be included in the modification templates')
        pattern = super(ModificationService, self).save(pattern)
        elementRep.close()
        return pattern


    def getFormula(self, item):
        '''
        Returns the molecular formula of a modification (ModificationItem)
        :param (tuple[str,str,str,str,int|str,int|str, int, int]) item: corresponding modification
        :return: (MolecularFormula) formula
        '''
        #return ModificationItem(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]).getFormula()
        return ModificationItem(item).getFormula()

    def getAllPatternNames(self):
        return ["-"] + super(ModificationService, self).getAllPatternNames()

    def getPatternWithObjects(self, name, *args):
        '''
        Returns a modification pattern with ModificationItem objects
        :param (str) name: name of the fragmentation pattern
        :param (callable) args: not used
        :return: (ModificationPattern) modification pattern
        '''
        if name == '-':
            return ModificationPattern("", "", [],[], None)
        else:
            return super(ModificationService, self).getPatternWithObjects(name, ModificationItem)



class IntactIonService(AbstractServiceForPatterns):
    '''
    Service handling a IntactRepository and IntactPattern entities.
    '''
    def __init__(self):
        super(IntactIonService, self).__init__(IntactRepository(),(0,4,5))

    def makeNew(self):
        # return PatternWithItems("", [{"Name": "", "Gain": "", "Loss": "", "NrOfMod": 0, "enabled": False}], None)
        return IntactPattern("", 10 * [["", "", "", "", '', False]], None)

    def getFormula(self, item):
        '''
        Returns the molecular formula of an intact modification (IntactModification)
        :param (tuple[str,str,str,int,int,int]) item: corresponding intact modification
        :return: (MolecularFormula) formula
        '''
        return IntactModification(item).getFormula()

    """def getPatternWithObjects(self, name, constructor):"""


    """def getPatternWithObjects(self, name):
        pattern = self._repository.getPattern(name)
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
                raise InvalidInputException(pattern.getName(), "Element: " + key + " unknown")
        pattern = super(IntactIonService, self).save(pattern)
        elementRep.close()
        return pattern'''
