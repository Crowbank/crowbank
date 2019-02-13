import shutil
from subprocess import run
import os.path
from site import getsitepackages

def install_package(package_name):
    package_dir = getsitepackages()[-1]
    package_path = os.path.join(package_dir, package_name)

    if os.path.exists(package_path):
        shutil.rmtree(package_path)

    shutil.copytree(package_name, package_path)


PIP_ARGS = ['pip', 'install', '-r', 'requirements.txt']
SCRIPT_DIR = r'C:\\Crowbank'
FILE_LIST = ('confirm.py', 'scan_vaccinations.py', 'sms.py', 'wsync.sh')
PACKAGE_LIST = ('pypa', 'cloud')

for package in PACKAGE_LIST:
    install_package(package)

for file in FILE_LIST:
    shutil.copy(file, SCRIPT_DIR)

run(PIP_ARGS)

