import binascii
from py532lib.i2c import *
from py532lib.frame import *
from py532lib.constants import *
from py532lib.mifare import *
 
'''
pn532 = Pn532_i2c()
pn532.SAMconfigure()
 
card_data = pn532.read_mifare().get_data()
hex_string = binascii.hexlify(card_data).decode()
print(card_data)
print("HEX", hex_string[14:][:14])
'''

mifare = Mifare()

while True:
	id = mifare.scan_field()
	print(id)
	hex_string = binascii.hexlify(id).decode()
	print("HEX", hex_string)

