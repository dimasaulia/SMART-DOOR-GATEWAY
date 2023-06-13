import serial
import serial.tools.list_ports
import json
import sys
import platform
import os
from variable import *
from datetime import datetime
from authHandler import cardAuth
from nodeConnectionHandler import updateNodeOnlineTime
from database.scheme import Node, Card, AccessRole, Gateway
from util import get_random_string

gatewayShortId = Gateway.get_by_id(1).shortId

ports = serial.tools.list_ports.comports()
portsList = []
for port in ports:
    portsList.append(str(port))

selectedPort = sys.argv[1]

print(
    f"Mesh Netwrok And Authentication Start On {selectedPort}, Waiting For Request")
serialDebug = serial.Serial(port=f'{selectedPort}', baudrate=115200,
                            bytesize=8, parity="N", stopbits=serial.STOPBITS_TWO, timeout=1)
print(f"{selectedPort} => PID={os.getpid()}")
Variable.setAuthDaemonPID(f"{selectedPort}", os.getpid())
# if platform.system() == "Windows":

# if platform.system() == "Linux":
#     print(
#         f"Mesh Netwrok And Authentication Start On {selectedPort}, Waiting For Request")
#     serialDebug = serial.Serial(port=f'{selectedPort}', baudrate=115200,
#                                 bytesize=8, parity="N", stopbits=serial.STOPBITS_TWO, timeout=1)
#     print(f"{selectedPort}: PID={os.getpid()}")


def setupNetwork():
    # if platform.system() == "Windows":
    # GET NETWORK CREDENTIAL BASE ON PORT
    networkDetail = Variable.getPortNetwrokCredential(f"{selectedPort}")
    allNetworkDetail = Variable.getAllNetworkCredential()
    credentialToSend = {}

    # JIKA BELUM ADA MAKA BUAT
    if networkDetail == False:
        ssid = f"MN-GATEWAY-{gatewayShortId}-{len(allNetworkDetail)+1}"
        password = get_random_string(8)
        gateway = f"GATEWAY-{gatewayShortId}"
        credentialToSend["SSID"] = ssid
        credentialToSend["PASSWORD"] = password
        credentialToSend["GATEWAY"] = gateway
        Variable.setNetwrokCredential(
            f"{selectedPort}", credentialToSend)

    # JIKA SUDAH ADA MAKA TAMPILKAN
    if networkDetail:
        availableData = Variable.getPortNetwrokCredential(
            f"{selectedPort}")
        print(availableData)
        credentialToSend["SSID"] = availableData["SSID"]
        credentialToSend["PASSWORD"] = availableData["PASSWORD"]
        credentialToSend["GATEWAY"] = availableData["GATEWAY"]

    # KIRIMKAN MELALUI KOMUNIKASI SERIAL
    credentialToSend["type"] = "networksetup"
    return str(credentialToSend)


while True:
    try:
        serialString = serialDebug.readline().decode("utf").rstrip("\n")
        if (len(serialString) > 0):
            print(serialString)
            # Jika Data Memerlukan Autentikasi
            if (serialString.startswith("__REQUEST_FOR_AUTH")):
                # first index will be debug info, and the second array will be real payload
                payloadArray = serialString.split(".")
                data = json.loads(payloadArray[1])
                if (data["type"] == "auth"):
                    print("[G]: Waiting For Auth")
                    resp = cardAuth(payload=payloadArray[1])
                    print(f"[G]: {resp}")
                    serialDebug.write(bytes(f"{resp}", 'utf-8'))

            if (serialString.startswith("__CONNECTION_PING")):
                # first index will be debug info, and the second array will be real payload
                payloadArray = serialString.split(".")
                data = json.loads(payloadArray[1])
                if (data["type"] == "connectionping"):
                    print("[G]: Update Online Time")
                    Variable.setResponseTimeLog(data["source"], data["auth"])
                    current_date = datetime.now()
                    Variable.setNodeLastOnlineTime(data["source"], current_date.isoformat())
                    resp = updateNodeOnlineTime(payload=payloadArray[1])
                    print(f"[G]: {resp}")

            if (serialString.startswith("__REQUEST_NETWORK_CREDENTIAL")):
                networkCredential = setupNetwork()
                serialDebug.write(bytes(f"{str(networkCredential)}", 'utf-8'))

            if (serialString.startswith("__CHECK_AUTH_SERVICE")):
                authService = {
                    "type": "service",
                }
                serialDebug.write(bytes(f"{str(authService)}", 'utf-8'))
                print(f"[G]: Auth Service Available")

    except KeyboardInterrupt:
        print("Handling interrupt...")
        break
