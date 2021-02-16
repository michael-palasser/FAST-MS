import os
import traceback

from src import path
from src.MolecularFormula import MolecularFormula
from src.Services import *
from src.PeriodicTable import *
from src.entities.GeneralEntities import *
from src.entities.IonTemplates import *
from os import listdir
from os.path import isfile, join

def removeEmptyElements(rawList):
    newList = rawList
    while '' in newList:
        newList.remove('')
    return newList


def writeElements():
    service = PeriodicTableService()
    try:
        for key, val in periodicTable.items():
            print(key)
            isotopeList = []
            for iso in val:
                isotopeList.append([iso[0], iso[2],iso[3]])
                print((iso[0], iso[2],iso[3]))
            print(Element(key,isotopeList, None).getName())
            service.savePattern(Element(key,isotopeList, None))
    except:
        traceback.print_exc()
    finally:
        service.close()


def readMoleculeFile(moleculeFile, molecule):
    '''
    reads and processes file which contains formulas of monomeres and precursor ions
    :param moleculeFile: (RNA.txt, DNA.txt, Protein.txt in Parameters - folder)
    :return: void
    '''
    monomers = []
    mode = 'monomers'
    h2o = {'H':2, 'O':1}
    gpb_nuc_pos={'A':913,'C':916,'G':928,'T':850, 'U':842}
    gpb_nuc_neg={'A':1460,'C':1430,'G':1388,'T':1420, 'U':1418}
    gpb_prot_pos={'P':980,'W':980,'Q':993,'K':1008, 'R':1051, 'H':1024}
    gpbDict_prot_neg={'E':1424,'D':1429,'H':1433,'W':1436,'Y':1439,'C':1460}
    for line in moleculeFile:
        if line.startswith('#precursor ions'):
            mode = 'precIons'
        if line.startswith('#') or line == "\n":
            continue
        lineList = removeEmptyElements(line.rstrip().split('\t'))
        if mode == 'monomers':
            name = lineList[0]
            if molecule == "Protein":
                gbPos = 927
                gbNeg = 1483
                if name in gpb_prot_pos.keys():
                    gbPos = gpb_prot_pos[name]
                if name in gpbDict_prot_neg.keys():
                    gbNeg = gpbDict_prot_neg[name]
                monomers.append([name, lineList[1], gbPos, gbNeg])
            else:
                #gbPos = 927
                #if name in gpb_prot_pos.keys():
                gbPos = gpb_nuc_pos[name]
                #if name in gpbDict_prot_neg.keys():
                gbNeg = gpb_nuc_neg[name]
                monomers.append([name, lineList[1], gbPos, gbNeg])

            #formula = MolecularFormula(AbstractItem2.stringToFormula(lineList[1], dict(),1)).addFormula(h2o).toString()
            #print(lineList[1], formula)
            #self.monomers[lineList[0]] = self.stringToFormula(lineList[1],dict(),1)
    return monomers



def writeMolecules():
    service = MoleculeService()
    try:
        for molecule in ('RNA', 'Protein', 'DNA'):
            moleculePath = os.path.join(path, 'Parameters', molecule + '.txt')
            print(moleculePath)
            with open(moleculePath) as f:
                monomers = readMoleculeFile(f, molecule)
            gain,loss = 'H','O2P1'
            if molecule == 'Protein':
                gain, loss = 'H2O', ''
            service.savePattern(Makromolecule(molecule, gain, loss, monomers,None))
    except:
        traceback.print_exc()
    finally:
        service.close()


def getSequences(file):
    '''
    finds sequenceList
    :param file: file with stored sequences
    :param name: sequenceList name
    :return: molecule, list of sequenceList, respectively None,None if sequenceList was not found
    '''
    sequences = []
    for line in file:
        if line.startswith('#'):
            continue
        line = line.rstrip()
        lineList = line.split()
        sequences.append(Sequence(lineList[0],lineList[2],lineList[1], None))
    return sequences


def writeSequences():
    service = SequenceService()
    sequencePath = os.path.join(path, 'Parameters','sequences.txt')
    try:
        with open(sequencePath) as f:
            service.save(getSequences(f))
    except:
        traceback.print_exc()
    finally:
        service.close()



def readFragmentations(file):
    items = []
    for line in file:
        line = line.rstrip()
        if line.startswith('#modifications'):
            break
        if line.startswith('#ion') or line == "":
            print(line)
            continue
        oldProperties = removeEmptyElements(line.split())
        properties = []
        for i, property in enumerate(oldProperties):
            if property == "-":
                property = ""
                if i == len(oldProperties)-1:
                    property = 0
            properties.append(property)
        name, enabled = properties[0] , True
        if properties[0].startswith('#'):
            name, enabled = properties[0][1:], False

        if name[0] in ['a', 'b', 'c', 'd']:
            items.append([name, properties[2], properties[1], properties[3], int(properties[4]), 1, enabled])
        else:
            items.append([name, properties[2], properties[1], properties[3], int(properties[4]), -1, enabled])
    for item in items:
        print(item)
    return items


def writeFragments(name, fragPath,precFrag):
    service = FragmentIonService()
    try:
        with open(fragPath) as f:
            fragments = readFragmentations(f)
        '''if "RNA" in name:
            gain, loss = 'H1', 'O2P1'
        else:
            gain, loss = 'H2O', '' '''
        print(FragmentationPattern(name, fragments, precFrag, None).getItems2())
        service.savePattern(FragmentationPattern(name, fragments, precFrag, None))
    except:
        traceback.print_exc()
    finally:
        service.close()


def writeModifications():
    service = ModificationService()
    try:
        for mol in ['protein','RNA']:
            fragPath = join(path,'Parameters',mol+'-fragmentation')
            files = [f for f in listdir(fragPath) if isfile(join(fragPath, f))]
            print(files)
            for file in files:
                if file == ".DS_Store":
                    continue
                flag = 0
                print("\n" ,file)
                modifications = []
                excluded = []
                with open(join(fragPath,file)) as f:
                    for line in f:
                        line = line.rstrip()
                        if line.startswith('#modif') or line.startswith('#Modif'):
                            flag = 1
                            continue
                        elif line.startswith('#remove'):
                            flag = 2
                            continue
                        if line == "":
                            continue
                        elif flag == 1:
                            properties = removeEmptyElements(line.split())
                            if line.startswith("#"):
                                modifications.append(
                                    [properties[0][1:], properties[2], properties[1], properties[3], 0, properties[4], True,
                                     False])
                            else:
                                modifications.append([properties[0], properties[2], properties[1], properties[3], 0,properties[4], True, True])
                            print("1", [properties[0], properties[2], properties[1], properties[3], 0,properties[4], True, True])
                        elif flag == 2:
                            if line.startswith("#"):
                                continue
                            excluded.append([removeEmptyElements(line.split())[0][1:]])
                            print("2", [removeEmptyElements(line.split())[0][1:]])
                    if len(modifications)>0:
                        name = file[4:-4]
                        print(name, name, modifications, excluded, None)
                        modif = name
                        if name == '72':
                            modif = "DEPC"
                        elif name == '90':
                            modif = "DEPC+H2O"
                        elif name == '62':
                            modif = "DEPC+H2O-CO"
                        elif name == '134':
                            modif = "2DEPC+H2O-CO"
                        service.savePattern(ModificationPattern(name, modif, modifications, excluded, None))
    except:
        traceback.print_exc()
    finally:
        service.close()


def readIntactModifs():
    with open(join(path,'Parameters','intact_modifications.txt')) as f:
        modifications = dict()
        for line in f:
            if line.startswith('#'):
                continue
            line = line.rstrip()
            lineList = removeEmptyElements(line.split())
            if len(lineList) < 5:
                continue
            if lineList[0] not in modifications.keys():
                modifications[lineList[0]] = [[lineList[1], lineList[3], lineList[2], lineList[4], True]]
            else:
                modifications[lineList[0]].append([lineList[1], lineList[3], lineList[2], lineList[4], True])
    for key,val in modifications.items():
        print(key, val)
    return modifications

def writeIntactModifs():
    service= IntactIonService()
    modifications = readIntactModifs()
    try:
        for key,val in modifications.items():
            service.savePattern(IntactPattern(key, "H1", "O2P1", val, None))
    except:
        traceback.print_exc()
    finally:
        service.close()


writeElements()
writeMolecules()
writeSequences()
"""with open(os.path.join(path, 'Parameters', 'Protein' + '.txt')) as f:
    for line in f:
        if line.startswith('#') or line == "":
            continue
        lineList = removeEmptyElements(line.rstrip().split('\t'))
        print(lineList,",")
#['start', 'H1', 'O2P1', '', 0,True]
prcFrags = [
    ['-H2O', '', 'H2O', '', 0,True] ,
    ['-G', '', 'C5H5N5O', 'G', 0,True] ,
    ['-A', '', 'C5H5N5', 'A', 0,True] ,
    ['-C', '', 'C4H5N3O', 'C', 0,True] ,
    ['-G-H2O', '', 'C5H5N5OH2O', 'G', 0,True] ,
    ['-A-H2O', '', 'C5H5N5H2O', 'A', 0,True] ,
    ['-C-H2O', '', 'C4H5N3OH2O', 'C', 0,False]]

fragPath = join(path, 'Parameters', 'RNA-fragmentation','CAD.txt')
writeFragments("RNA_CAD",fragPath, prcFrags)

#['start', 'H2O', '', '', 0,True]
prcFrags = [
    ['-H2O', '', 'H2O', '', 0,True] ,
    ['-NH3', '', 'NH3', '', 0,True]]
fragPath = join(path, 'Parameters', 'protein-fragmentation','CAD.txt')
writeFragments("Protein_CAD",fragPath, prcFrags)

#['start', 'H2O', '', '', 0,True]
prcFrags = [
    ['-H2O', '', 'H2O', '', 0,True] ,
    ['-NH3', '', 'NH3', '', 0,True],
    ['+e', '', '', '', 1,True],
    ['+2e', '', '', '', 2,True]]
fragPath = join(path, 'Parameters', 'protein-fragmentation','ECD.txt')

#writeFragments("Protein_ECD",fragPath, prcFrags)

#writeModifications()"""

#writeIntactModifs()
