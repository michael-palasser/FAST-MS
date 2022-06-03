import sys
from copy import deepcopy

from PyQt5.QtWidgets import QApplication

from src.entities.Ions import FragmentIon
from src.gui.widgets.SequCovWidget import SequCovWidget
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