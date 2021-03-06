import asyncio
import re
import json
import socket
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
from pythonosc import udp_client


"""VRCHAT & AVATAR CONFIG--------------------------------------------------------------------------------------------"""
with open('server_config.json', 'r') as config:       #Reads Config Json and puts string into value
    config_str = config.read()

AviData = json.loads(config_str)['AviConfig']
VestData = json.loads(config_str)['VestConfig']

Haptics_Avi_ID = AviData[0]['HapticAviID']  #ID of the avatar with haptics!
print(f"Haptics_Avi_ID = {AviData[0]['HapticAviID']}")
OSC_json = AviData[1]['OSCJson']            #Full filepath of your avatar OSC json
print(f"OSC_json = {AviData[1]['OSCJson']}")
OSC_json_ref = AviData[2]['OSCJsonRef']     #Filename of reference OSC json to be written placed in script folder
print(f"OSC_json_ref = {AviData[2]['OSCJsonRef']}")

"""VEST CONFIG-------------------------------------------------------------------------------------------------------"""
VestIP = VestData[0]['VestHostname']              #Vest server IP
print(f"VestIP = {VestData[0]['VestHostname']}")
VestPort = int(VestData[1]['VestPort'])     #Vest server port
print(f"VestPort = {int(VestData[1]['VestPort'])}")
buffer_length = float(int(VestData[2]['BufferLength']) / 1000)  #how long motor values are buffered for before beiong released in seconds
print(f"Buffer Length = {int(VestData[2]['BufferLength'])}ms")

MotorLimits = json.loads(VestData[3]['MotorLimits'])
print("Setting Motor Limits...")
MotorMin = float(MotorLimits[0])
print(f"Min = {100 * MotorMin}%")
MotorMax = float(MotorLimits[1])
print(f"Max = {100 * MotorMax}%")

TotalMotors = 32      #Total number of motors!




"""------------------------------------------------------------------------------------------------------------------"""

#Vest connection manager
try:
    vest = udp_client.SimpleUDPClient(VestIP, VestPort)
    print(f'Client established on: {VestIP}, {VestPort}')
except Exception as e:
    print(e)




#AviDynams to OSC Json workaround
def osc_jogger(address, *args):    #jogs OSC json for it to work w/ AviDynams
    print(f"Checking: {args}")
    if Haptics_Avi_ID in args:     #checks for Haptics avatar ID on connected Avatar
        print("Haptics Detected!")
        with open(OSC_json_ref, 'r') as DupeR:      #reads reference Json
            with open(OSC_json, 'w') as DupeW:      #writes reference to active Json
                DupeW.write(DupeR.read())
        print("Json rewritten!")
    else:
        print("Boring... No Haptics Found!")

#Handler receives & buffers incoming motor values into 1 list
toPrint = False
buffered_array = [float(0)] * TotalMotors      #creates array of empty floats w/ specified amount of motor slots
def motor_handler(address, *args):
    global buffered_array
    #global toPrint
    #toPrint = True
    motor_index = int(re.search(r'\d+', address).group())
    motor_val = float(re.search("\d+\.\d+", f"{args}").group())
    if "Front" in address and motor_val > 0.0:
        ScaledVal = max(MotorMin + (MotorMax - MotorMin) * motor_val, 1.0)    #Gets motor limit range, mults by value, adds to minimum for scaled clamp
        #print(f"Front {motor_index}, {ClampedVal}")
        buffered_array[motor_index] = round(ScaledVal, 3)
    if "Back" in address and motor_val > 0.0:
        ScaledVal = max(MotorMin + (MotorMax - MotorMin) * motor_val, 1.0)
        #print(f"Back {motor_index + 16}, {ClampedVal}")
        buffered_array[motor_index + 16] = round(ScaledVal, 3)
    Motor_array = [float(0)] * TotalMotors
    for i in range(TotalMotors):
        if buffered_array[i] < Motor_array[i]:
            buffered_array[i] = Motor_array[i]

#Async loop sends motor values after allowing them to be buffered for buffer_length
async def buffer():
    while True:
        global buffered_array
        #global toPrint
        #if toPrint == True:
        #    print(f"Buffer{buffered_array}")
        #    toPrint = False
        vest.send_message("/h", f"{buffered_array}")  # Sends buffered values
        buffered_array = [float(0)] * TotalMotors # resets buffer for next pass
        await asyncio.sleep(buffer_length)



dispatcher = Dispatcher()
dispatcher.map("/avatar/change*", osc_jogger)           #checks for avatar change & jogs OSC if is Greenlit
dispatcher.map("/avatar/Haptics*", motor_handler)       #handles haptic data after json is jogged
#dispatcher.set_default_handler(default_handler)         #any other messages

ip = "127.0.0.1"
port = 9001

async def init_main():
    server = osc_server.AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await buffer()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())