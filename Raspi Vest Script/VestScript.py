from time import sleep
import pythonosc
from pythonosc import dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import board 
import busio
from adafruit_pca9685 import PCA9685
import ast
import subprocess
import re
#This IP & Port for server
seekIP = None
while seekIP == None:
    command =subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
    print(command)
    cmdIP = command.stdout.read()
    print(cmdIP)
    seekIP = re.search("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", f"{cmdIP}")
    print(seekIP)

ip = seekIP.group()
print(f"Got IP: {ip}")

thisIP = ip
thisPort = 1025

#Motor Index Mapping (index used to send motor data to correct motor)
motorMap = [15,14,1,0,13,12,3,2,11,10,5,4,9,8,7,6,16,17,30,31,18,19,28,29,20,21,26,27,22,23,24,25]

#init i2c bus
i2c = busio.I2C(board.SCL, board.SDA)
#assign i2c addresses to each board & init frequency
front = PCA9685(i2c, address = 64)
back = PCA9685(i2c, address = 65)
front.frequency = 60
back.frequency = 60

#function to convert float values to duty cycle values
def floatToDuty(float):
    answer = int(float*0xffff)
    return answer
    
def handle_values(unused_addr, args):
    valArray = ast.literal_eval(args)
    #print(valArray)
    for i in range(32):
        #print(floatToDuty(valArray[i]))
        #print(i)
        if i < 16:
            front.channels[motorMap[i]].duty_cycle = floatToDuty(valArray[i])
        else:
            back.channels[motorMap[i] - 16].duty_cycle = floatToDuty(valArray[i])

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/h", handle_values)


print('starting server')

#ignore this, its literally just the startup chime
for i in range(16):
    front.channels[i].duty_cycle = floatToDuty(1)
    back.channels[i].duty_cycle = floatToDuty(1)
sleep(0.5)
for i in range(16):
    front.channels[i].duty_cycle = floatToDuty(0)
    back.channels[i].duty_cycle = floatToDuty(0)
sleep(0.05)
for i in range(16):
    front.channels[i].duty_cycle = floatToDuty(0.6)
    back.channels[i].duty_cycle = floatToDuty(0.6)
sleep(0.15)
for i in range(16):
    front.channels[i].duty_cycle = floatToDuty(0)
    back.channels[i].duty_cycle = floatToDuty(0)
#sleep(0.1)
for i in range(16):
    front.channels[i].duty_cycle = floatToDuty(1)
    back.channels[i].duty_cycle = floatToDuty(1)
sleep(0.5)
for i in range(16):
    front.channels[i].duty_cycle = floatToDuty(0)
    back.channels[i].duty_cycle = floatToDuty(0)
    
server = BlockingOSCUDPServer((thisIP, thisPort), dispatcher)
server.serve_forever()
    
