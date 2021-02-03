import os
try:
    os.system("python3 -m venv venv")
except:
    os.system("pip install virtualenv")
os.system("python -m src.views.StartWindow")