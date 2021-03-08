from datetime import datetime


class LogFile(object):
    def __init__(self, *args):
        if len(args)==3:
            self._logString = 'Analysis: '+ datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'
            self.start(args[0], args[1], args[2])
        else:
            self._logString = args[0]
            self.load()

    def start(self, settings, configurations, searchProperties):
        self._logString += '\n* Settings:\n'
        self._logString += ''.join(['\t%s: %s\n' % (key, val) for (key, val) in settings.items()])
        self._logString += '* Configurations:\n'
        self._logString += ''.join(['\t%s: %s\n' % (key, val) for (key, val) in configurations.items()])
        self._logString += '* Sequence:\n\t' + ', '.join(searchProperties.getSequenceList())
        self._logString += '\n* Fragmentation:' + searchProperties.getFragmentation().toString()
        self._logString += '\n* Modification: ' + searchProperties.getModification().toString()

    def ionToString(self, ion):
        return ion.getName() + ', ' + str(ion.charge)

    def deleteMonoisotopic(self, ion):
        self._logString += '\n* del (mono) '+ self.ionToString(ion)

    def deleteIon(self, ion):
        self._logString += '\n* del '+ self.ionToString(ion)

    def restoreIon(self, ion):
        self._logString += '\n* restore '+ self.ionToString(ion)

    def changeIon(self, origIon, newIon):
        self._logString += '\n* changing ' + self.ionToString(origIon) + \
                ';   old Int.: ' + str(round(origIon.intensity)) + ', new: ' + str(round(newIon.intensity))
        count = 1
        for oldPeak, newPeak in zip(origIon.getPeakValues(), newIon.getPeakValues()):
            self._logString += '\n\t' + str(count) + '   old: ' + ', '.join([str(val) for val in oldPeak]) + \
                               '\tnew: ' + ', '.join([str(val) for val in newPeak])
            count += 1

    def repeatModelling(self):
        self._logString += '\n* Repeat modelling overlaps'

    def export(self):
        self._logString += '\n* Export to Excel: '+ datetime.now().strftime("%d/%m/%Y %H:%M")

    def save(self):
        self._logString += '\n* Save Analysis: '+ datetime.now().strftime("%d/%m/%Y %H:%M")

    def load(self):
        self._logString += '\n* Load Analysis: '+ datetime.now().strftime("%d/%m/%Y %H:%M")

    def toString(self):
        return self._logString