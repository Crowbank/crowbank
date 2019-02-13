import shutil
from subprocess import run

PIP_ARGS = ['pip', 'install', '-r', 'requirements.txt']
SCRIPT_DIR = r'C:\\Crowbank'

files = ('confirm.py', 'scan_vaccinations.py', 'sms.py', 'wsync.sh')

for file in files:
    shutil.copy(file, SCRIPT_DIR)

run(PIP_ARGS)
