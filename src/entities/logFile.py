from datetime import datetime


class LogFile(object):
    def __init__(self, *args):
        if len(args)==2:
            self._logString = 'Analysis: '+ datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'
            self.addConfigurations(args[0], args[1])
        else:
            self._logString = args[0]
            self.load()

    def addConfigurations(self, settings, configurations):
        self._logString += '\n* Settings:\n'
        self._logString += ''.join(['\t%s: %s\n' % (key, val) for (key, val) in settings.items()])
        self._logString += '\n* Configurations:\n'
        self._logString += ''.join(['\t%s: %s\n' % (key, val) for (key, val) in configurations.items()])

    def ionToString(self, ion):
        return ion.getName() + ', ' + str(ion.charge)

    def deleteMonoisotopic(self, ion):
        self._logString += '\n\n* mono '+ self.ionToString(ion)

    def deleteIon(self, ion):
        self._logString += '\n\n* del '+ self.ionToString(ion)

    def restoreIon(self, ion):
        self._logString += '\n\n* restore '+ self.ionToString(ion)

    def changeIon(self, origIon, newIon):
        self._logString += '\n\n* changing ' + self.ionToString(origIon) + \
                '(old Int.: ' + str(origIon.intensity) + ', new: ' + str(newIon.intensity)
        for oldPeak, newPeak in zip(origIon.getPeakValues(), newIon.getPeakValues()):
            self._logString += '\n\told: ' + ', '.join(oldPeak) + '\tnew: ' + ', '.join(newPeak)

    def repeatModelling(self):
        self._logString += '\n\n* Repeat modelling overlaps'

    def export(self):
        self._logString += '\n\n* Export to Excel: '+ datetime.now().strftime("%d/%m/%Y %H:%M")

    def save(self):
        self._logString += '\n\n* Save Analysis: '+ datetime.now().strftime("%d/%m/%Y %H:%M")

    def load(self):
        self._logString += '\n\n* Load Analysis: '+ datetime.now().strftime("%d/%m/%Y %H:%M")

    def getLogString(self):
        return self._logString