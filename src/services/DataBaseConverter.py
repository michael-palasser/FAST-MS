import os

from src.entities.Ions import FragmentIon, FragmentIonRed
from src.entities.SearchSettings import SearchSettings
from src.services.SearchService import SearchService
from src.services.StoredAnalysesService import StoredAnalysesService


class DataBaseConverter(object):
    def __init__(self):
        oldService = SearchService()
        oldPath = oldService.getDatabasePath()
        print("**Converting",oldPath)
        newService = StoredAnalysesService()
        newNames = newService.getAllSearchNames()[0]
        oldNames = oldService.getAllSearchNames()
        #configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        """for name in newNames:
            print(name)
            fileNames = newService.getFileNames(name)
            log = ""
            with open(fileNames[-2]) as f:
                for line in f:
                    log += line
            ConfigHandler(fileNames[2], []).write(newService.getSettingsAndConfigs(log))"""

        for i,name in enumerate(oldNames):
            print(name, i,"/",len(oldNames))
            if name in newNames:
                print("Already converted")
                continue
            configs = newService.getSettingsAndConfigs(info)
            constr = FragmentIon
            if "subtract noise" in configs.keys() and configs["subtract noise"]:
                constr = FragmentIonRed
            settings, noiseLevel, ions, deletedIons, remIons, searchedZStates, info = oldService.getSearch(name, constr)
            props = SearchSettings(settings['sequName'], settings['fragmentation'], settings['modifications'])
            newService.saveSearch(name, noiseLevel, settings, configs, ions, deletedIons, searchedZStates, info, props)

        oldService.close()
        os.rename(oldPath, oldPath[:-3]+"_old.db")
        print("done",oldPath)


"""def checkConfigs():
    newService = StoredAnalysesService()
    newService.checkConfigs()


if __name__ == '__main__':
    #DataBaseConverter()
    checkConfigs()"""