import numpy as np
import sympy as sym
import subprocess
import os
from src import path


def main():
    inputFile = os.path.join(path, 'Spectral_data','model_input.txt')
    subprocess.call(['openAgain', inputFile])
    input('Press any key to start')
    # get pattern
    with open(inputFile, 'r') as input_file:
        ion_dict = dict()
        raw_list = list()
        count_mz = 0  # necessary because spectral peaks should not be included twice
        for line in input_file:
            line = line.rstrip()
            line_list = line.split('\t')
            if len(line_list) < 2:
                continue
            # ToDo
            # elif len(line_list) == 1:
            # print(line)
            # raise Exception("Element missing")
            elif line_list[1] == 'm/z':
                count_mz += 1
                continue
            elif not (line_list[0].isdigit()) and (not line_list[0] == ''):
                if count_mz == 0:
                    current_ion = (line_list[0], line_list[1])
                else:
                    ion_dict[current_ion] = np.array(raw_list)
                    current_ion = (line_list[0], line_list[1])
                    raw_list = list()
                    count_mz = 0
            elif count_mz > 1:
                continue
            else:
                if line_list[0] == '':
                    line_list[0] = 0
                raw_list.append(np.array((line_list[0], line_list[1], line_list[3]),
                                         dtype=[('spectr_int', np.float64), ('m/z', np.float64), ('theo_int', np.float64)]))
    ion_dict[(current_ion[0], current_ion[1])] = np.array(raw_list)

    # modelling
    output_list = list()
    peak_list = list()
    for key, val in ion_dict.items():
        x = sym.Symbol('x')
        x_solved = float(sym.solve(sym.diff((np.sum((val['spectr_int'] - val['theo_int'] * x) ** 2))), x)[0])
        val['theo_int'] *= x_solved
        for line in val:
            peak_list.append((line['m/z'], key[1], int(round(line['theo_int'])), key[0]))
        intensity = np.sum(val['theo_int'])
        std_dev = ((np.sum((val['spectr_int'] - val['theo_int']) ** 2)) ** (1 / 2)) / intensity
        output_list.append((np.min(val['m/z']), key[1], int(round(intensity, 0)), key[0], '', '', round(std_dev, 2)))

    # output
    outputFile = os.path.join(path, 'Spectral_data','model_output.txt')
    with open(outputFile, 'w') as output_file:
        output_file.write('m/z_theo \tz \tI \tfragment \terror_/ppm \tS/N\tquality\n')
        for row in output_list:
            for elem in row:
                output_file.write(str(elem) + '\t')
            output_file.write('\n')
        output_file.write('\n\n\n')
        output_file.write('m/z_theo \tz \tI \tfragment\n')
        for row in peak_list:
            for elem in row:
                output_file.write(str(elem) + '\t')
            output_file.write('\n')

    subprocess.call(['openAgain', outputFile])

if __name__ == '__main__':
    main()