
import os
import platform
import subprocess
import time
OS = str(platform.system()).upper()

def isFileExist (path):
    if os.path.isfile(path):
        return True
    else:
        return False

def isDirectoryExist (path):
    if os.path.isdir(path):
        return True
    else:
        return False

subprocess.call('pip install pyinstaller', shell=True)
# ACTIVATE THE venv
if OS == "WINDOWS":
    # Install packages from requirements.txt
    subprocess.call('pip install -r requirements.txt', shell=True)

if OS == "LINUX":
    # Install packages from requirements.txt
    if(isDirectoryExist("./.venv") == False):
        subprocess.call('virtualenv venv', shell=True)
        subprocess.call('source ./venv/bin/activate', shell=True)
        subprocess.call('./venv/bin/pip install -r rpi.txt', shell=True)

# CHECK DATABASE
if(isFileExist("./database/gateway.db") == True):
    print("DATABASE ALREADY EXIST")

# IF EMPTY MIGRATE
if(isFileExist("./database/gateway.db") == False):
    subprocess.call('./venv/bin/python ./database/migrate.py', shell=True)

# CREATE EXECUTEABLE APP
import PyInstaller.__main__

# Specify the path to your Python script
script_path = './run.py'

# Set PyInstaller options
options = ['--onefile', '--distpath', './', '--name', 'gateway']

# Build the executable
PyInstaller.__main__.run([*options, script_path])

