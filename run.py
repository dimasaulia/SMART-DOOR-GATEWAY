import subprocess
import platform
OS = str(platform.system()).upper()

if __name__ == '__main__':
    if OS == "WINDOWS":
        import os
        import sys
        venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'python.exe')
        venv_python = sys.executable
        subprocess.run(f"{venv_python} main.py")
    if OS == "LINUX":
        subprocess.run(['venv/bin/python', 'main.py'])
