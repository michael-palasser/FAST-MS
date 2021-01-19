import csv
import numpy as np


class IsotopePatternReader(object):

    def addIsotopePatternFromFile(self, file, fragmentLibrary):
        '''
        Reads and processes isotope patterns from existing file
        :param file: file with istope patterns (in folder Fragment_lists)
        :return: void
        '''
        isotopePatternDict = dict()
        reader = csv.reader(file)
        next(reader, None)
        isotopePattern = list()
        counter = 0
        for row in reader:
            if counter == 0:
                name = row[0]
                counter = 1
            if row[0] != '':
                isotopePatternDict[name] = np.array(isotopePattern, dtype=[('mass',np.float64),('int', np.float64)])
                name = row[0]
                isotopePattern = list()
            isotopePattern.append((row[1], row[2]))
        isotopePatternDict[name] = np.array(isotopePattern, dtype=[('mass',np.float64),('int', np.float64)])
        for fragment in fragmentLibrary:
            try:
                fragment.isotopePattern = isotopePatternDict[fragment.getName()]
            except KeyError:
                print(fragment.getName(), "not found in file.")
                raise KeyError
        return fragmentLibrary


    def saveIsotopePattern(self, file, fragmentLibrary):
        '''
        Saves calculated isotope patterns to a file
        :param file: csv-file in folder Fragment_lists
        :return: void
        '''
        np.set_printoptions(suppress=True)
        #M_max = 0
        fieldnames = ['ion', 'mass', 'Intensities']
        f_writer = csv.DictWriter(file, fieldnames=fieldnames)
        f_writer.writeheader()
        for fragment in fragmentLibrary:
            counter = 0  # for new rows
            for isotope in fragment.isotopePattern:
                if counter == 0:
                    #if M_max < isotope[0]:
                        #M_max = isotope[0]
                    #print(isotope[0])
                    f_writer.writerow({'ion': fragment.getName(), 'mass': np.around(isotope['mass'], 6), 'Intensities': np.around(isotope['int'], 7)})
                    counter += 1
                else:
                    f_writer.writerow({'ion': '', 'mass': np.around(isotope['mass'], 6), 'Intensities': np.around(isotope['int'], 7)})
