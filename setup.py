from setuptools import setup#, find_packages

setup(
    name='FAST MS',
    version='1.0dev',
    packages=['src', 'src.gui', 'src.gui.dialogs', 'src.gui.widgets', 'src.gui.controller', 'src.gui.tableviews',
              'src.intact', 'src.entities', 'src.services', 'src.services.assign_services',
              'src.services.export_services', 'src.services.library_services', 'src.services.analyser_services',
              'src.top_down', 'src.repositories', 'tests', 'tests.intact', 'tests.top_down', 'tests.test_files'],
    url='https://git.uibk.ac.at/c7261075/fast_ms',
    license='GNU General Public License v3.0',
    author='eva-maria',
    author_email='michael.palasser@uibk.ac.at',
    description='Free Analysis Software for Top-Down Mass Spectrometry',
    classifiers = [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 1.0dev - Beta',
        'License :: OSI Approved :: GNU General Public License v3.0',
        'Operating System :: OS :: Independent',
        'Topic :: Mass Spectrometry :: Data Analysis :: Top-Down MS',
    ],
    long_description=open('README.txt').read()
)

#packages=find_packages(where="src"),
#package_dir={"": "src"},