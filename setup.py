#!/usr/bin/python3

import pathlib
import os
from subprocess import call 

os.environ["ROOT_PATH"] = os.path.dirname(os.path.abspath(__file__))
call(['sudo', '/usr/bin/pip3','install', '-r', os.environ["ROOT_PATH"] + "/setup/requirements.txt"])
print("###########################################")
print("Root PATH:", os.environ["ROOT_PATH"])
call(['/usr/bin/python3', os.environ["ROOT_PATH"] + "/setup/run_setup.py"])