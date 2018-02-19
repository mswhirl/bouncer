# bouncer.py (c) Mark Smith (Whirlpool). GPLv3.
# Raspberry Pi serial port sniffer for power control via a relay connected to the Pi's GPIO4
#
# If this script runs for 60s without a match message then there is some difference with your modem
# so you will have to tweak the script.  Add a print(d) at the appropriate point(s) to get spammed.
#
# This program could auto tune itself (i.e. start with low timeout, then fail to get a switch message,
# then increase the timeout until a working value for the current modem is found, etc.) but considering the
# expert audience (if you can solder bridge SMT pads, add pins and get the relay circuit going) you will probably
# consider tweaking the 250ms black-out period a good challenge :)  Start low and increase it until you get the
# "attempt" bit in the text, then you are good to go.
# File based GPIO control was used as it doesn't require any extra library and we don't care about inconsequential errors

# Circuit notes: The modem in the pictures required a large DC barrel - an old netbook power supply cable was suitable.
# I used a 12VDC relay and a BC549 transistor.

import serial, time, os, re, sys, traceback

# The following two commands may give harmless errors after the first run of the program
os.system("""echo "4" > /sys/class/gpio/export""")
os.system("""echo "out" > /sys/class/gpio/gpio4/direction""")

def setModemPower(state):
    os.system("""echo "%i" > /sys/class/gpio/gpio4/value""" % state)	

port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1)

reBankMessage = re.compile("""(?:Booting +: )([^\n\r]+)""")
reKernelMessage = re.compile("""(Starting the Linux kernel)""")
reBankSwitchedMessage = re.compile("""(?:Booting +: Bank . \(bank . failed 3 times\))""")

setModemPower(0)
time.sleep(0.5)
port.reset_input_buffer()
setModemPower(1)
d = b''
try:
    while True:
        d += port.read(1)
        bank = reBankMessage.search(d.decode('utf-8','ignore'))
        kernel = reKernelMessage.search(d.decode('utf-8','ignore'))
        switched = reBankSwitchedMessage.search(d.decode('utf-8','ignore'))
        if bank is not None and kernel is not None and switched is None:
            print("Got a match: " + bank.group(1))
            setModemPower(0)
            port.reset_input_buffer()
            d = b''
            time.sleep(0.250)
            setModemPower(1)
        if switched is not None:
            print("You have now booted off the alternate bank: " + bank.group(1))
            break
except:
    print("Unhandled exception:" + str(sys.exc_info()[0]))
    traceback.print_exc()
    print("At this time the serial data buffer contained: ")
    print(d)
