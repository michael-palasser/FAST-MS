import numpy as np

from src.Exceptions import InvalidInputException

#dataDtype = np.dtype([('m/z', float), ('z', np.uint8), ('relAb', float)])


class SpectralDataReader(object):
    def __init__(self):
        self._dict = {'m/z':'m/z', 'z':'z', 'I':'I', 'Intensity':'I', 'S/N': 'S/N', 'Quality Factor': 'qual',
                      'qual': 'qual', 'name':'name'}


    def openFile(self, dataPath, dataDtype):
        '''
        Reads a text file with unassigned ion data
        :param (str) dataPath: path of the file
        :param (dtype) dataDtype: dtype of the returned array
        :return: (ndarray) array
        '''
        """rawData = []
        delimiter = ','
        csv=False
        if dataPath[-4:] == '.csv':
            csv=True
        with open(dataPath) as file:
            for i,line in enumerate(file):
                line = line.rstrip()
                if csv and (i == 0):
                    if (', ' in line):
                        delimiter = ', '
                    elif ('; ' in line):
                        delimiter = '; '
                    elif (';' in line):
                        delimiter = ';'
                try:
                    #print(i,delimiter)
                    if not csv:
                        lineList = line.split('\t')
                    else:
                        lineList = line.split(delimiter)
                    rawData.append(lineList)
                except:
                    raise InvalidInputException("Problem in data file: <br>line " + str(i), line)"""
        rawData = self.getRawData(dataPath)
        indizes = {}
        """skipZ = False
        if len(rawData[0])>len(rawData[1]):
            skipZ = True"""
        #correction = 0
        #counter = 0
        #print(rawData)
        for i, header in enumerate(rawData[0]):
            if header in self._dict.keys():
                """if skipZ and self._dict[header] == 'z':
                    correction = 1"""
                indizes[self._dict[header]] = i#-correction


            '''if header != 'Factor':
                counter+=1'''
        mandatoryHeaders = dataDtype.names
        for header in mandatoryHeaders:
            if header not in indizes.keys():
                missingHeader = {val:key for key,val in self._dict.items()}[header]
                raise InvalidInputException('Problem in file '+dataPath+':<br>', 'Header "' + missingHeader + '" is not included')
        data = []
        if 'z' in mandatoryHeaders:
            for line in rawData[1:]:
                line[indizes['z']] = line[indizes['z']].replace('+', '').replace('-', '')
        #print(path)
        #print(rawData)
        for line in rawData[1:]:
            if len(line)>1:
                data.append(tuple([line[indizes[mandatoryHeader]] for mandatoryHeader in mandatoryHeaders]))
        return np.array(data, dtype=dataDtype)


    def getRawData(self,dataPath, delimiter='\t'):
        rawData = []
        csv = False
        if dataPath[-4:] == '.csv':
            delimiter = ','
            csv = True
        with open(dataPath) as file:
            for i, line in enumerate(file):
                line = line.rstrip()
                if csv and (i == 0):
                    if (', ' in line):
                        delimiter = ', '
                    elif ('; ' in line):
                        delimiter = '; '
                    elif (';' in line):
                        delimiter = ';'
                try:
                    # print(i,delimiter)
                    lineList = line.split(delimiter)
                    rawData.append(lineList)
                except:
                    raise InvalidInputException("Problem in data file: <br>line " + str(i), line)
        return rawData

    def openCsvFile(self, path):
        '''
        Reads a csv file with unassigned ion data
        :param path: path of csv file
        :return: (list[ndarray]) list of spectra: dtype = [('m/z', float), ('z', np.uint8), ('relAb', float)]
        '''
        pass
        #with open(path) as file:
        #    try:
        #        return [np.loadtxt(path, delimiter=',', usecols=[0, 1, 2],dtype=dataDtype)]
        #    except IndexError:
        #        return [np.loadtxt(path, delimiter=';', usecols=[0, 1, 2],dtype=dataDtype)]
        #    except ValueError:
        #        return self.openTxtFile(path, True)"""
                #raise InvalidInputException('Incorrect Format of spectral data', '\nThe format must be "m/z,z,int" or "m/z;z;int"')
    
    def openXYFile(self, dataPath, max_mz):
        """rawData = []
        with open(path) as f:
            for line in f:
                rawData.append(tuple(line.rstrip().split()))"""
        if dataPath[-3:] == ".xy":
            rawData = self.getRawData(dataPath," ")
        else:
            rawData = self.getRawData(dataPath)[1:]
        rawData = np.array([tuple(row) for row in rawData], dtype=[('m/z', float), ('I', float)])
        data = rawData[rawData['m/z']<max_mz]
        return data

    """def writePeaks(peaks, fileName):
        '''
        Writes a calibrated peak list to a file
        :param (ndarray[float,float]) peaks: array with columns m/z, int
        :param (str) fileName: name of the file
        '''
        with open(fileName, 'w') as f:
            f.write('m/z\tI\n')
            for peak in peaks:
                f.write(str(peak['m/z'])+'\t'+str(peak['I'])+'\n')"""


    @staticmethod
    def writeData(data, fileName):
        '''
        Writes a calibrated peak list to a file
        :param (ndarray[float,float]) peaks: array with columns m/z, int
        :param (str) fileName: name of the file
        '''
        with open(fileName, 'w') as f:
            f.write("\t".join(data.dtype.names)+'\n')
            for row in data:
                f.write('\t'.join([str(item) for item in row])+'\n')