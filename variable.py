import json


class Variable():
    __VARIABLE_FILE = open("variable.json")
    __VARIABLE_DATA = json.load(__VARIABLE_FILE)
    __VARIABLE_FILE.close()

    def __init__(self):
        pass

    @staticmethod
    def readFile():
        VARIABLE_FILE = open("variable.json")
        VARIABLE_DATA = json.load(VARIABLE_FILE)
        VARIABLE_FILE.close()
        return VARIABLE_DATA

    @staticmethod
    def writeFile(payload):
        jsonObj = json.dumps(payload)
        with open("variable.json", "w") as outfile:
            outfile.write(jsonObj)
        return True

    @staticmethod
    def setSyncPid(pid):
        # print("WRITE NEW PID")
        VARIABLE_DATA = Variable.readFile()
        VARIABLE_DATA["syncpid"] = pid
        Variable.writeFile(VARIABLE_DATA)

    @staticmethod
    def syncPid():
        VARIABLE_DATA = Variable.readFile()
        return VARIABLE_DATA["syncpid"]

    @staticmethod
    def setAuthDaemonPID(port, pid):
        VARIABLE_DATA = Variable.readFile()
        VARIABLE_DATA["authenticationDaemon"][port] = pid
        Variable.writeFile(VARIABLE_DATA)

    @staticmethod
    def getAllAuthDaemonPID():
        VARIABLE_DATA = Variable.readFile()
        return VARIABLE_DATA["authenticationDaemon"]

    @staticmethod
    def getPortAuthDaemonPID(port):
        VARIABLE_DATA = Variable.readFile()
        PORT_PID = None
        try:
            PORT_PID = VARIABLE_DATA["authenticationDaemon"][port]
        except:
            PORT_PID = False
        return PORT_PID

    @staticmethod
    def getAllNetworkCredential():
        VARIABLE_DATA = Variable.readFile()
        return VARIABLE_DATA["networkCredential"]

    @staticmethod
    def getPortNetwrokCredential(port):
        VARIABLE_DATA = Variable.readFile()
        PORT_PID = None
        try:
            PORT_PID = VARIABLE_DATA["networkCredential"][port]
        except:
            PORT_PID = False
        return PORT_PID

    @staticmethod
    def setNetwrokCredential(port, data):
        VARIABLE_DATA = Variable.readFile()
        VARIABLE_DATA["networkCredential"][port] = (data)
        Variable.writeFile(VARIABLE_DATA)
