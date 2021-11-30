from datetime import datetime


class Info(object):
    '''
    class which stores informations about user inputs
    '''
    def __init__(self, *args):
        '''
        :param args: new analysis: ((dict) settings, (dict) configurations, (SearchSettings) searchProperty)
                    loaded analysis: ((str) infoString)
        '''
        if len(args)==3:
            self._infoString = 'Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'
            self.start(args[0], args[1], args[2])
        elif len(args) == 4:
            self._infoString = 'Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'
            self.startIntact(args[0], args[1], args[2], args[3])
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

    def startIntact(self, settings, configurations, sequenceList, modification):
        self._infoString += '\n* Settings:\n'
        self._infoString += ''.join(['\t%s:\t%s\n' % (key, val) for (key, val) in settings.items()])
        self._infoString += '* Configurations:\n'
        self._infoString += ''.join(['\t%s:\t%s\n' % (key, val) for (key, val) in configurations.items()])
        self._infoString += '* Sequence:\n\t' + ', '.join(sequenceList)
        self._infoString += '\n* Modification: ' + modification.toString()

    def calibrate(self, values, errors, quality, usedIons):
        self._infoString += '\n* Spectrum calibrated: m/z_cal = a * m/z + b * m/z + c'
        for i, var in enumerate(['a','b','c']):
            self._infoString += '\n\t'+var + ' = {} ± {}'.format(values[i], errors[i])
        self._infoString += '\n\tquality: error std.dev. = {}, av. error = {}'.format(quality[0], quality[1])
        self._infoString += '\n\tused ions: (' + '), ('.join([self.ionToString(ion) for ion in usedIons])+')'

    def spectrumProcessed(self, upperBound, noiseLevel):
        self._infoString += '\n* Max. m/z: ' + str(upperBound)
        self._infoString += '\n* Av. noise: ' + str(noiseLevel)

    def searchFinished(self, mz):
        self._infoString += '\n* Search finished: ' + datetime.now().strftime("%d/%m/%Y %H:%M") + '\n'


    def ionToString(self, ion):
        return ion.getName() + ', ' + str(ion.getCharge())

    def deleteMonoisotopic(self, ion):
        self._infoString += '\n* deleted ' + self.ionToString(ion) +  ' (same mass and charge as another ion)'

    def deleteIon(self, ion):
        self._infoString += '\n* deleted ' + self.ionToString(ion)

    def restoreIon(self, ion):
        self._infoString += '\n* restored ' + self.ionToString(ion)

    def changeIon(self, origIon, newIon):
        '''
        Logs manual changes of intensity
        :param (FragmentIon) origIon: original ion
        :param (FragmentIon) newIon: ion with changed values
        '''
        self._infoString += '\n* changed ' + self.ionToString(origIon) + \
                ';   old Int.: ' + str(round(origIon.getIntensity())) + ', new: ' + str(round(newIon.getIntensity()))
        #count = 1
        self._infoString += '\n\tisotope peaks (columns: m/z,  int.(spectrum),  int. (calc.),  used)\n' \
                            '\n\t\tnew   -->   old\n'
        for oldPeak, newPeak in zip(origIon.getIsotopePattern(), newIon.getIsotopePattern()):
            self._infoString += '\n\t'+ self.formatPeak(oldPeak) + '\t' + self.formatPeak(newPeak)
            #self._infoString += '\n\t' + str(count) + '   old: ' + ',  '.join([str(val) for val in oldPeak]) + \
            #                   '\tnew: ' + ', '.join([str(val) for val in newPeak])
            #count += 1

    @staticmethod
    def formatPeak(peak):
        return ',  '.join([str(val) for val in [round(peak[0],5) + int(peak[1]) + int(peak[2]) + round(peak[3],2) + peak[4]]])

    def addNewIon(self, ion):
        self._infoString += '\n* manually added ' + self.ionToString(ion)

    def repeatModelling(self):
        self._infoString += '\n* Repeated modelling overlaps'

    def resetIon(self, ion):
        self._infoString += '\n* reset ' + self.ionToString(ion)

    def export(self):
        self._infoString += '\n* Exported to Excel: ' + datetime.now().strftime("%d/%m/%Y %H:%M")

    def save(self):
        self._infoString += '\n* Saved Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M")

    def load(self):
        self._infoString += '\n\n* Load Analysis: ' + datetime.now().strftime("%d/%m/%Y %H:%M")

    def toString(self):
        return self._infoString