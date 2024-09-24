import sys
from copy import deepcopy

import numpy as np
from PyQt5.QtWidgets import QApplication

from src.entities.Ions import FragmentIon
from src.gui.widgets.SequCovWidget import SequCovWidget, SequenceCoveragePlot
from src.services.analyser_services.Analyser import Analyser
from tests.top_down.test_IntensityModeller import initTestSpectrumHandler

if __name__ == '__main__':
    configs, settings, props, builder, spectrumHandler = initTestSpectrumHandler()
    fragments = builder.getFragmentLibrary()
    # self.spectrumHandler.setNormalisationFactor(self.spectrumHandler.getNormalizationFactor())
    ions = {}
    for fragment in fragments:
        zRange = spectrumHandler.getChargeRange(fragment)
        for z in zRange:
            ion = FragmentIon(fragment, 1., z, fragment.getIsotopePattern(), 10e5)
            ions[ion.getHash()] = ion
    analyser = Analyser([], props.getSequenceList(), settings['charge'],
                        props.getModifPattern().getModification())

    ions2 = deepcopy(ions)
    for hash in ions.keys():
        if ('c02' in hash[0]) or ('a02' in hash[0]) or ('w03' in hash[0]) or ('y03' in hash[0]):
            del ions2[hash]
    analyser.setIons(ions2.values())
    coverages, calcCoverages, overall = analyser.getSequenceCoverage(['a', 'c'])
    calcData = [(key, val * 100) for key, val in calcCoverages.items()]
    app = QApplication(sys.argv)
    gui = SequCovWidget(calcData, props.getSequenceList(), coverages[0], coverages[1], overall)
    sys.exit(app.exec_())


def test_make_plot():
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    """app = QApplication(sys.argv)
    overall = [(key,val*100) for key,val in
               {'a': 0.7692307692307693, 'c': 0.9230769230769231, 'w': 0.7692307692307693, 'y': 0.9230769230769231, 'allForward': 0.9615384615384616, 'allBackward': 0.9230769230769231, 'all': 0.9259259259259259}.items()]
    gui = SequCovWidget( overall,
                         sequ, {'a': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]), 'c': np.array([0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 0., 1., 1., 1.,np.nan])}, {'w': np.array([np.nan,1., 1., 0., 0., 1., 1., 0., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       0., 1., 1., 1., 1., 1., 1., 1., 0.]), 'y': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 0.])},np.array([(val1,val2) for val1,val2 in zip(np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]),np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 0.]))]))"""

    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    calcData = [('a', 73.07692307692307), ('c', 100.0), ('w', 88.46153846153845), ('y', 96.15384615384616),
                ('forward', 100.0), ('backward', 96.15384615384616), ('total', 100.0)]

    coverages0 = [[0.0, 1.0], [0.0, 1.0], [1.0, 1.0], [0.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                  [1.0, 1.0],
                  [0.0, 1.0], [1.0, 1.0], [1.0, 1.0], [0.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                  [0.0, 1.0],
                  [1.0, 1.0], [1.0, 1.0], [0.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]]
    coverages1 = [[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                  [0.0, 1.0],
                  [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [0.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                  [1.0, 1.0],
                  [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [0.0, 0.0]]
    print("\u23CB", len(coverages0))
    sequLength = len(sequ)
    sequPlot = SequenceCoveragePlot(sequ, np.ones((sequLength - 1, 1)),
                                    np.ones((sequLength - 1, 1)), 10)
    sequPlot.makePlot(coverages0, coverages1, 10, coloursF=['purple', 'orange'], coloursB=['purple', 'orange'])
    """sequPlot = SequenceCoveragePlot(sequ, np.ones((sequLength-1,1)),
                                          np.ones((sequLength-1,1)), 10)
    sequPlot.makePlot(np.ones((sequLength-1,4)), np.ones((sequLength-1,4)), 10, coloursF=['red',"green","blue", "brown"],coloursB=['red',"green", "blue","brown"])"""

    sequPlot.show()
    # sys.exit(app.exec_())
    """star = matplotlib.markers.TICKLEFT
    print(star)
    circle = mpath.Path.unit_circle()"""
    # concatenate the circle with an internal cutout of the star
    '''verts = np.concatenate([circle.vertices, star])
    codes = np.concatenate([circle.codes, star])
    cut_star = mpath.Path(verts, codes)
    plt.plot(np.arange(10) ** 2, '--r', marker=cut_star, markersize=15)

    plt.show()
    #sys.exit(app.exec_())'''
