import os
import platform
import shutil
from copy import deepcopy

from src.repositories.ConfigurationHandler import ConfigHandler
from src.repositories.sql.AnalysisRepository import AnalysisRepository
from src.resources import path
from src.services.MolecularFormula import MolecularFormula
from src.services.FormulaFunctions import stringToFormula2
from src.services.IntensityModeller import calcScore


class StoredAnalysesService(object):
    '''
    Service handling a SearchRepository and Search entities.
    '''
    def __init__(self):
        self._dir = os.path.join(path, "Saved Analyses")
        self._search = None

    def getAllSearchNames(self):
        allAnalyses = []
        for savedDir in os.listdir(self._dir):
            if savedDir == "Archive":
                continue
            fullPath = os.path.join(self._dir, savedDir)
            if platform.system() == 'Windows':
                time = os.path.getctime(fullPath)
            else:
                stat = os.stat(fullPath)
                try:
                    time = stat.st_birthtime
                except AttributeError:
                    # We're probably on Linux. No easy way to get creation dates here,
                    # so we'll settle for when its content was last modified.
                    time = stat.st_mtime
            allAnalyses.append((savedDir,time))
        return [tup[0] for tup in sorted(allAnalyses, key=lambda tup:tup[1])]

    #ToDo
    def getSearch(self, name):
        '''
        Returns the values of a stored analysis
        :param (str) name: name of the analysis/search
        :return: (tuple[dict[str,Any], list[FragmentIon], list[FragmentIon], list[FragmentIon], dict[str, list[int]],
            str) settings {name:value}, observed ions, deleted ions, remodelled ions, calculated charge states per
            fragment {fragment name: charge states}, information log
        '''
        print("*** Loading Analysis", name)
        filePaths = self.getFileNames(name)
        rep = AnalysisRepository(filePaths[0])
        ions, delIons, searchedZStates, log = rep.getSearch()
        settings = ConfigHandler(filePaths[1], []).getAll()
        configurations = ConfigHandler(filePaths[2], []).getAll()
        noiseLevel = settings['noiseLevel']
        if noiseLevel == 0:
            noiseLevel = settings['noiseLimit']
        ions = [self.ionFromDB(ion, noiseLevel) for ion in ions]
        deletedIons = [self.ionFromDB(ion, noiseLevel) for ion in delIons]
        searchedZStates = {frag: zsString.split(',') for frag, zsString in searchedZStates.items()}
        return settings, configurations, noiseLevel, ions, deletedIons, searchedZStates, log

    """def getSettingsAndConfigs(self, log):
        limits = ("Settings:\n", "* Configurations:\n", "* Sequence:\n",
                  "* Fragmentation:	Name	Gain	Loss	BB	Rad.	Dir.	Enabled\n",
                  "Modification: \n	Name	Gain	Loss	BB	Rad.	z-Eff.	Calc.occ.	Enabled",
                  "\n\t\n")
        allConfigs = []
        remaining = log
        for i in range(len(limits) - 1):
            # print(remaining[remaining.find(limits[i])+len(limits[i]): remaining.find(limits[i+1])])
            allConfigs.append(remaining[remaining.find(limits[i]) + len(limits[i]): remaining.find(limits[i + 1])])
            remaining = remaining[remaining.find(limits[i + 1]):]
        return allConfigs"""


    def saveSearch(self, name, noiseLevel, settings, configurations, ions, deletedIons, searchedZStates, info):
        '''
        Saves or updates a search/analysis
        :param (str) name: name of the search/analysis
        :param (dict[str,Any]) settings: settings
        :param (list[FragmentIon]) ions: observed ions
        :param (list[FragmentIon]) deletedIons: deleted ions
        :param (dict[str, list[int]]) searchedZStates: calculated charge states per fragment
        :param (Info) info: information log
        '''
        print("*** Saving Analysis", name)
        if name in self.getAllSearchNames():
            filePaths = self.getFileNames(name)
            if os.path.isfile(filePaths[0]):
                newName = os.path.join(filePaths[4], "temp.db")
                if os.path.isfile(newName):
                    os.remove(newName)
                os.rename(filePaths[0], newName)
        else:
            filePaths = self.getFileNames(name)
        rep = AnalysisRepository(filePaths[0])
        ions = [self.ionToDB(ion) for ion in ions]
        deletedIons = [self.ionToDB(ion) for ion in deletedIons]
        searchedZStates = {frag: ','.join([str(z) for z in zs]) for frag,zs in searchedZStates.items()}
        settings['noiseLevel']=noiseLevel
        #logs = [line for line in info]
        rep.createSearch(ions, deletedIons, searchedZStates, info)
        ConfigHandler(filePaths[1], []).write(settings)
        ConfigHandler(filePaths[2], []).write(configurations)
        with open(filePaths[3], "w") as f:
            f.write(info)

    def getFileNames(self, name):
        parentDir = os.path.join(self._dir,name)
        if not os.path.isdir(parentDir):
            os.mkdir(parentDir)
        return [os.path.join(parentDir, name+fileType) for fileType in (".db", "_settings.json", "_configs.json",
                                                                        "_infos.txt")] +[parentDir]

    def ionFromDB(self, ion, noiseLevel):
        '''
        Processes the sequence and the formula of an ion which was read from the database
        :param (FragmentIon) ion: ion with strings as sequence and formula
        :return: (FragmentIon) ion with list[str] as sequence and MolecularFormula as formula
        '''
        #ion.setSequence(ion.getSequence().split(','))
        ion.setFormula(MolecularFormula(stringToFormula2(ion.getFormula(), {}, 1)))
        ion.setScore(calcScore(ion.getIntensity(), ion.getQuality(), noiseLevel))
        return ion

    def ionToDB(self, ion):
        '''
        Processes the sequence and the formula of an ion to save it in the database
        :param (FragmentIon) ion: ion with list[str] as sequence and MolecularFormula as formula
        :return: (FragmentIon) ion with strings as sequence and formula
        '''
        #print(ion.getName(), ion.formula)
        processedIon = deepcopy(ion)
        #processedIon.setSequence(','.join(ion.getSequence()))
        processedIon.setFormula(ion.getFormula().toString())
        return processedIon

    def deleteSearch(self, name):
        shutil.rmtree(self.getFileNames(name)[4])

    @staticmethod
    def getAllAssignedPeaks(ions):
        peaks = set()
        for ion in ions:
            peaks.update({(peak['m/z'],peak['I']) for peak in ion.getIsotopePattern() if peak['I']!=0})
        return peaks


