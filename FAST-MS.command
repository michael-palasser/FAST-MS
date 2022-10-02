#!/usr/bin/env python3
import os

abspath = os.path.abspath(__file__)
directory = os.path.dirname(abspath)
os.chdir(directory)
os.system("python -m src.gui.StartWindow")

#!/Users/eva-maria/.conda/envs/FAST MS/bin/python