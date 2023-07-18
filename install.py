
import os
import platform
import subprocess
import time
import sys
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

subprocess.call('pip install virtualenv pyinstaller', shell=True)

# ACTIVATE THE venv
if OS == "WINDOWS":
    # Install packages from requirements.txt
    if(isDirectoryExist("./.venv") == False):
        print("INFO: Creating New Virtual Enivironment")
        subprocess.run('virtualenv venv', shell=True)
        print("INFO: Installing All Required Library")
        venv_pip = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'pip.exe')
        requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        venv_python = sys.executable
        command = [venv_python, venv_pip, 'install', '-r', requirements_file]
        subprocess.run(command, shell=True)

if OS == "LINUX":
    # Install packages from requirements.txt
    if(isDirectoryExist("./.venv") == False):
        print("INFO: Creating New Virtual Enivironment")
        subprocess.call('virtualenv venv', shell=True)
        subprocess.call('source ./venv/bin/activate', shell=True)
        print("INFO: Installing All Required Library")
        subprocess.call('./venv/bin/pip install -r rpi.txt', shell=True)

# CHECK DATABASE
print("INFO: Checking Database")
if(isFileExist("./database/gateway.db") == True):
    print("INFO: Database Already Exist")

# IF EMPTY MIGRATE
if(isFileExist("./database/gateway.db") == False):
    print("INFO: Migrating Dataabse")
    if OS == "WINDOWS":
        subprocess.run('/venv/Scripts/python ./database/migrate.py', shell=True)
    if OS == "LINUX":
        subprocess.call('./venv/bin/python ./database/migrate.py', shell=True)

# CREATE EXECUTEABLE APP
import PyInstaller.__main__

# Specify the path to your Python script
print("INFO: Creating Executable App")
script_path = './run.py'

# Set PyInstaller options
options = ['--onefile', '--distpath', './', '--name', 'Gateway']

# Build the executable
PyInstaller.__main__.run([*options, script_path])
print("INFO: All Proccess Done!")


