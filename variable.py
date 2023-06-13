import json


class Variable():
    __VARIABLE_FILE = open("variable.json")
    __VARIABLE_DATA = json.load(__VARIABLE_FILE)
    __VARIABLE_FILE.close()

    def __init__(self):
        pass

    @staticmethod
    def readFile(file="variable.json"):
        VARIABLE_FILE = open(file)
        VARIABLE_DATA = json.load(VARIABLE_FILE)
        VARIABLE_FILE.close()
        return VARIABLE_DATA

    @staticmethod
    def writeFile(payload, file="variable.json"):
        jsonObj = json.dumps(payload)
        with open(file, "w") as outfile:
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

    @staticmethod
    def setResponseTimeLog(deviceId, responseTime):
        finalDeviceId = str(deviceId).replace("NODE-", "")
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            VARIABLE_DATA[finalDeviceId]["responseTime"] = VARIABLE_DATA[finalDeviceId]["responseTime"] + responseTime
        except:
            # IF EMPTY
            if(not VARIABLE_DATA):
                VARIABLE_DATA[finalDeviceId] = {}
                
            VARIABLE_DATA[finalDeviceId]["responseTime"] = responseTime
        Variable.writeFile(VARIABLE_DATA, "log.json")

    @staticmethod
    def reSetResponseTimeLog(deviceId):
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            VARIABLE_DATA[deviceId]["responseTime"] = ""
        except:
            # IF EMPTY
            if(not VARIABLE_DATA):
                VARIABLE_DATA[deviceId] = {}
                VARIABLE_DATA[deviceId]["responseTime"] = ""

            VARIABLE_DATA[deviceId]["responseTime"] = ""
        Variable.writeFile(VARIABLE_DATA, "log.json")

    @staticmethod
    def getResponseTimeLog(deviceId):
        finalDeviceId = str(deviceId).replace("NODE-", "")
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            return VARIABLE_DATA[finalDeviceId]["responseTime"]
        except:
            return None
        
    @staticmethod
    def setNodeLastOnlineTime(deviceId, time):
        finalDeviceId = str(deviceId).replace("NODE-", "")
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            VARIABLE_DATA[finalDeviceId]["lastOnline"] = time
        except:
            # IF EMPTY
            if(not VARIABLE_DATA):
                VARIABLE_DATA[finalDeviceId] = {}

            VARIABLE_DATA[finalDeviceId]["lastOnline"] = time
        Variable.writeFile(VARIABLE_DATA, "log.json")

    @staticmethod  
    def getNodeLastOnlineTime(deviceId):
        finalDeviceId = str(deviceId).replace("NODE-", "")
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            return VARIABLE_DATA[finalDeviceId]["lastOnline"]
        except:
            return None
    
    @staticmethod
    def setAuthenticationResponseLog(deviceId, authenticationData):
        finalDeviceId = str(deviceId).replace("NODE-", "")
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            VARIABLE_DATA[finalDeviceId]["authenticationData"] = VARIABLE_DATA[finalDeviceId]["authenticationData"] + authenticationData
        except:
            # IF EMPTY
            if(not VARIABLE_DATA):
                VARIABLE_DATA[finalDeviceId] = {}
                
            VARIABLE_DATA[finalDeviceId]["authenticationData"] = authenticationData
        Variable.writeFile(VARIABLE_DATA, "log.json")
    
    @staticmethod
    def reSetAuthenticationResponseLog(deviceId):
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            VARIABLE_DATA[deviceId]["authenticationData"] = ""
        except:
            # IF EMPTY
            if(not VARIABLE_DATA):
                VARIABLE_DATA[deviceId] = {}
                VARIABLE_DATA[deviceId]["authenticationData"] = ""
            VARIABLE_DATA[deviceId]["authenticationData"] = ""
        Variable.writeFile(VARIABLE_DATA, "log.json")
    
    @staticmethod
    def getAuthenticationResponseLog(deviceId):
        finalDeviceId = str(deviceId).replace("NODE-", "")
        VARIABLE_DATA = Variable.readFile("log.json")
        try:
            return VARIABLE_DATA[finalDeviceId]["authenticationData"]
        except:
            return None