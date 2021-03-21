from datetime import datetime


class Info(object):
    def __init__(self, *args):
        if len(args)==3:
            self._infoString = 'Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'
            self.start(args[0], args[1], args[2])
        else:
            self._infoString = args[0]
            self.load()

    def start(self, settings, configurations, searchProperties):
        self._infoString += '\n* Settings:\n'
        self._infoString += ''.join(['\t%s:\t%s\n' % (key, val) for (key, val) in settings.items()])
        self._infoString += '* Configurations:\n'
        self._infoString += ''.join(['\t%s:\t%s\n' % (key, val) for (key, val) in configurations.items()])
        self._infoString += '* Sequence:\n\t' + ', '.join(searchProperties.getSequenceList())
        self._infoString += '\n* Fragmentation:' + searchProperties.getFragmentation().toString()
        self._infoString += '\n* Modification: ' + searchProperties.getModification().toString()

    def searchFinished(self):
        self._infoString += '\n* Search finished: ' + datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'


    def ionToString(self, ion):
        return ion.getName() + ', ' + str(ion.charge)

    def deleteMonoisotopic(self, ion):
        self._infoString += '\n* del (mono) ' + self.ionToString(ion)

    def deleteIon(self, ion):
        self._infoString += '\n* del ' + self.ionToString(ion)

    def restoreIon(self, ion):
        self._infoString += '\n* restore ' + self.ionToString(ion)

    def changeIon(self, origIon, newIon):
        self._infoString += '\n* changing ' + self.ionToString(origIon) + \
                ';   old Int.: ' + str(round(origIon.intensity)) + ', new: ' + str(round(newIon.intensity))
        count = 1
        for oldPeak, newPeak in zip(origIon.getPeakValues(), newIon.getPeakValues()):
            self._infoString += '\n\t' + str(count) + '   old: ' + ', '.join([str(val) for val in oldPeak]) + \
                               '\tnew: ' + ', '.join([str(val) for val in newPeak])
            count += 1

    def repeatModelling(self):
        self._infoString += '\n* Repeat modelling overlaps'

    def export(self):
        self._infoString += '\n* Export to Excel: ' + datetime.now().strftime("%d/%m/%Y %H:%M")

    def save(self):
        self._infoString += '\n* Save Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M")

    def load(self):
        self._infoString += '\n\n* Load Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M")

    def toString(self):
        return self._infoString