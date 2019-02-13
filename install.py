import shutil
from subprocess import run
import os.path
from site import getsitepackages

PIP_ARGS = ['pip', 'install', '-r', 'requirements.txt']
SCRIPT_DIR = r'C:\\Crowbank'

package_dir = getsitepackages()[-1]
pypa_path = os.path.join(package_dir, 'pypa')

if os.path.exists(pypa_path):
    shutil.rmtree(pypa_path)

shutil.copytree('pypa', pypa_path)

files = ('confirm.py', 'scan_vaccinations.py', 'sms.py', 'wsync.sh')

for file in files:
    shutil.copy(file, SCRIPT_DIR)

run(PIP_ARGS)

