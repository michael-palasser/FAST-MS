from setuptools import setup#, find_packages
#from Cython.Build import cythonize

setup(
    name='FAST MS',
    version='1.0',
    packages=['src', 'src.gui', 'src.gui.dialogs', 'src.gui.widgets', 'src.gui.controller', 'src.gui.tableviews',
              'src.intact', 'src.entities', 'src.test_services', 'src.test_services.assign_services',
              'src.test_services.export', 'src.test_services.library_services', 'src.test_services.analyser_services',
              'src.top_down', 'src.repositories', 'tests', 'tests.intact', 'tests.test_services', 'tests.test_other', 'tests.test_files'],
    install_requires=['numpy', 'scipy', 'matplotlib', 'pandas', 'PyQt5', 'pyqtgraph', 'xlsxwriter', 'numba','tqdm'],
    url='https://git.uibk.ac.at/c7261075/fast_ms',
    license='GNU General Public License v3.0',
    author='Michael Palasser',
    author_email='michael.palasser@uibk.ac.at',
    description='Free Analysis Software for Top-Down Mass Spectrometry',
    classifiers = [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 1.0 - Beta',
        'License :: OSI Approved :: GNU General Public License v3.0',
        'Operating System :: OS :: Independent',
        'Topic :: Mass Spectrometry :: Data Analysis :: Top-Down MS',
    ],
    zip_safe=False,
    long_description=open('README.txt').read(),
    #ext_modules = cythonize("Start.py", language_level = "3")
)

#packages=find_packages(where="src"),
#package_dir={"": "src"},