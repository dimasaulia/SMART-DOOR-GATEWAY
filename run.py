import subprocess
import platform
OS = str(platform.system()).upper()

if __name__ == '__main__':
    if OS == "WINDOWS":
        subprocess.run(['venv/Scripts/python', 'main.py'])
    if OS == "LINUX":
        subprocess.run(['venv/bin/python', 'main.py'])
