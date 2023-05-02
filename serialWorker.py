import serial
import serial.tools.list_ports
from datetime import datetime
import json
from authHandler import cardAuth
ports = serial.tools.list_ports.comports()
portsList = []
for port in ports:
    portsList.append(str(port))
    print(str(port))

selectedPort = input("Plase select available port. COM:")
serialDebug = serial.Serial(port=f'COM{selectedPort}', baudrate=115200,
                            bytesize=8, parity="N", stopbits=serial.STOPBITS_TWO, timeout=1)
while True:
    try:
        serialString = serialDebug.readline().decode("utf").rstrip("\n")
        if (len(serialString) > 0):
            print(serialString)
            # Jika Data Memerlukan Autentikasi
            if (serialString.startswith("__REQUEST_FOR_AUTH")):
                # first index will be debug info, and the second array will be real payload
                payloadArray = serialString.split(".")
                request = json.loads(payloadArray[1])
                if (request["type"] == "auth"):
                    print("[G]: Waiting For Auth")
                    resp = cardAuth(payload=payloadArray[1])
                    print(f"[G]: {resp}")
                    serialDebug.write(bytes(f"{resp}", 'utf-8'))

    except KeyboardInterrupt:
        print("Handling interrupt...")
        break
