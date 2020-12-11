'''
Created on 31 Aug 2020

@author: michael
'''


class ParameterHandler(object):
    '''
    classdocs
    '''
    def __init__(self):
        self.parameters = dict()

    @staticmethod
    def lineToList(line):
        lineItems = line.rstrip().split('\t')
        while ("" in lineItems):
            lineItems.remove("")
        return lineItems


    #ToDo: Parameters to py-file, Verknuepfung in parameter-folder
    def readParameters(self,file):
        for line in file:
            if line.startswith('#'):
                continue
            lineItems = self.lineToList(line)
            if (len(lineItems)<2):
                continue
            if lineItems[1] == '-':
                lineItems[1] = ''
            self.parameters[lineItems[0]]=lineItems[1]


    def getNumber(self, parameter):
        try:
            return float(self.parameters[parameter])
        except:
            raise Exception('Bad formating in parameter-file:',parameter, self.parameters[parameter])


    def getString(self, parameter):
        try:
            return self.parameters[parameter]
        except KeyError:
            raise Exception('Bad formating in parameter-file:',parameter, self.parameters[parameter])


    def getMode(self):
        if self.parameters['spray_mode'] == 'negative':
            return -1
        elif self.parameters['spray_mode'] == 'positive':
            return 1
        else:
            raise Exception('Bad formating in parameter-file (spray_mode): ',self.parameters['spray_mode'])

    def getList(self, parameter):
        listOfParameter = self.parameters[parameter].split(',')
        while (" " in listOfParameter):
            listOfParameter.remove(" ")
        return listOfParameter

    def getNoiseLimit(self):
        return self.getNumber('noiseLimit') * 10**6

