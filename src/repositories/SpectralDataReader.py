import numpy as np

from src.Exceptions import InvalidInputException

#dataDtype = np.dtype([('m/z', float), ('z', np.uint8), ('relAb', float)])


class SpectralDataReader(object):
    def __init__(self):
        self._dict = {'m/z':'m/z', 'z':'z', 'I':'I', 'Intensity':'I', 'S/N': 'S/N', 'Quality Factor': 'qual'}


    def openTxtFile(self, path, dataDtype, csv=False):
        '''
        Reads a text file with unassigned ion data
        :param (str) path: path of the file
        :return: (list[ndarray]) list of spectra: dtype = [('m/z', float), ('z', np.uint8), ('relAb', float)]
        '''
        rawData = []
        delimiter = ','
        with open(path) as file:
            for i,line in enumerate(file):
                line = line.rstrip()
                if (i == 0) and (';' in line):
                    delimiter = ';'
                try:
                    if not csv:
                        lineList = line.split('\t')
                    else:
                        lineList = line.split(delimiter)
                    rawData.append(lineList)
                except:
                    raise InvalidInputException("Problem in data file: <br>line " + str(i), line)
        indizes = {}
        """skipZ = False
        if len(rawData[0])>len(rawData[1]):
            skipZ = True"""
        #correction = 0
        #counter = 0
        for i, header in enumerate(rawData[0]):
            #print(header)
            if header in self._dict.keys():
                """if skipZ and self._dict[header] == 'z':
                    correction = 1"""
                indizes[self._dict[header]] = i#-correction


            '''if header != 'Factor':
                counter+=1'''
        mandatoryHeaders = dataDtype.names
        for header in mandatoryHeaders:
            if header not in indizes.keys():
                print(header, indizes.keys())
                missingHeader = {val:key for key,val in self._dict.items()}[header]
                raise InvalidInputException('Problem in file '+path+':<br>', 'Header "' + missingHeader + '" is not included')
        data = []
        if 'z' in mandatoryHeaders:
            for line in rawData[1:]:
                line[indizes['z']] = line[indizes['z']].replace('+', '').replace('-', '')
        #print(path)
        #print(rawData)
        for line in rawData[1:]:
            print(line)
            if len(line)>1:
                data.append(tuple([line[indizes[mandatoryHeader]] for mandatoryHeader in mandatoryHeaders]))
        #print(data)
        return np.array(data, dtype=dataDtype)


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
    
    @staticmethod
    def openXYFile(path, max_mz):
        rawData = []
        with open(path) as f:
            for line in f:
                rawData.append(tuple(line.rstrip().split()))
        rawData = np.array(rawData, dtype=[('m/z', float), ('I', float)])
        data = rawData[rawData['m/z']<max_mz]
        return data
        
