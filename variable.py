import json

class Variable():
    __VARIABLE_FILE = open("variable.json")
    __VARIABLE_DATA = json.load(__VARIABLE_FILE)
    __VARIABLE_FILE.close()
    __SYNC_PID = None

    def __init__(self):
        pass

    @staticmethod
    def setSyncPid(pid):
        # print("WRITE NEW PID")
        Variable.__VARIABLE_DATA["syncpid"] = pid
        jsonObj = json.dumps(Variable.__VARIABLE_DATA)
        with open("variable.json", "w") as outfile:
            outfile.write(jsonObj)
    
    @staticmethod
    def syncPid():
        # print("READ JSON")
        VARIABLE_FILE = open("variable.json")
        VARIABLE_DATA = json.load(VARIABLE_FILE)
        VARIABLE_FILE.close()
        return VARIABLE_DATA["syncpid"]