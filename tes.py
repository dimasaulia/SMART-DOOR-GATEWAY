import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
portsList = []
for port in ports:
    portsList.append(port)
    print(str(port).split("-"))