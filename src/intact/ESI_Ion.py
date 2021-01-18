'''
Created on 2 Oct 2020

@author: michael
'''



class Ion(object):
    def __init__(self, name, modification, mz,theoMz, charge, intensity, nrOfModifications):
        '''

        '''
        self.name = name
        self.modification = modification
        self.mz = mz
        self.theoMz = theoMz
        self.charge = charge
        self.intensity = intensity
        self.nrOfModifications = nrOfModifications

    def calculateError(self):
        return (self.mz - self.theoMz) / self.theoMz * 10 ** 6

    def getName(self):
        return self.name + self.modification

    def toList(self):
        return [self.mz, self.charge, self.intensity, self.getName(), round(self.calculateError(), 2)]