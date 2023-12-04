from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.SearchService import SearchService
from src.services.StoredAnalysesService import StoredAnalysesService


class DataBaseConverter(object):
    def __init__(self):
        oldService = SearchService()
        newService = StoredAnalysesService()
        configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        for name in oldService.getAllSearchNames():
            print(name)
            settings, noiseLevel, ions, deletedIons, remIons, searchedZStates, info = oldService.getSearch(name)
            newService.saveSearch(name, noiseLevel, settings, configs, ions, deletedIons, searchedZStates, info)

DataBaseConverter()