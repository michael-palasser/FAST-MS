import os

from src.services.SearchService import SearchService
from src.services.StoredAnalysesService import StoredAnalysesService


class DataBaseConverter(object):
    def __init__(self):
        oldService = SearchService()
        oldPath = oldService.getDatabasePath()
        print("**Converting",oldPath)
        newService = StoredAnalysesService()
        newNames = newService.getAllSearchNames()
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
            settings, noiseLevel, ions, deletedIons, remIons, searchedZStates, info = oldService.getSearch(name)
            configs = newService.getSettingsAndConfigs(info)
            newService.saveSearch(name, noiseLevel, settings, configs, ions, deletedIons, searchedZStates, info)

        oldService.close()
        os.rename(oldPath, oldPath[:-3]+"_old.db")
        print("done",oldPath)


#DataBaseConverter()