import time, random, datetime, json
import serial, threading
# from mqtt_spb_wrapper import*
from MyClasses.Broker.SparkPlugB.mqtt_spb_wrapper import*
import ast
import requests, os, asyncio
import subprocess

_DEBUG = True  # Enable debug messages
payload_device = None
payload_node = None

addr_ref = [b'\x01\x90\x00', b'\x02\x58\x00', b'\x02\x0c\x00', b'\x02\x08\x00', b'\x00\x01\x06', b'\x00\x02\x04', b'\x00\x02\x0A']

'''
Real name of value from PLC:
    %Name Variable%	    %Address%
    temperature_SP	    b'\x01\x90\x00'
    temperature	        b'\x02\x58\x00'
    pressure_SP	        b'\x02\x0c\x00'
    pressure	        b'\x02\x08\x00'
    injectionTime	    b'\x00\x01\x06'
    cycleTime	        b'\x00\x02\x04'
    counterShot	        b'\x00\x02\x0A'
'''

var_name = []
var_addr = []
old_var = []
is_disconnect_wifi = 0
wifi_disconnect_flag = threading.Event()
#--------------------------------------------------------------------

#--------------------------- Setup MQTT SPB -------------------------
def callback_message_device(topic, payload):
    global payload_device, ip_eth0
    var_name.clear()
    var_addr.clear()
    old_var.clear()
    print(var_name)
    print(var_addr)
    try:
        payload_device = dict(payload)
        print("Received MESSAGE: %s - %s" % (topic, payload))
        for item in payload['metrics']:
            if item['name'] == '' or item['value'] == '':
                continue
            elif item['name'] == 'deviceProtocol':
                print(item['value'])
                if item['value'] == 'OPC-UA':
                    continue
            elif item['name'] == 'IPAddress':
                ip_eth0 = item['value']
                continue
            elif item['value'].find('ns') == 0:
                # _var_addr = ast.literal_eval(item['value'].encode().decode())
                var_name.append(item['name'])
                # var_addr.append(_var_addr)
                var_addr.append(item['value'])
                old_var.append(-1)
        print(var_name, 'count', len(var_name))
        print(var_addr, 'count', len(var_addr))
        print(old_var, 'count', len(old_var))
        
    except Exception as e:
        print(e)


def callback_message_node(topic, payload):
    global payload_node
    try:
        payload_node = dict(payload)
        print("Received MESSAGE: %s - %s" % (topic, payload))

        for item in payload['metrics']:
            if item['name'] == 'Node Control/Rebirth' and item['value'] == True:
                rebirth_flag.set()
                print('Rebirth')

            elif item['name'] == 'Node Control/Reboot' and item['value'] == True:
                print('Reboot')
    except Exception as e:
        print(e)


def callback_connect_device(rc):
    global is_disconnect_wifi
    is_disconnect_wifi = 0
    print("Connected to MQTT broker with result code "+str(rc))


def callback_disconnect_device(rc):
    global is_disconnect_wifi
    if rc != 0:
        is_disconnect_wifi = 1
        wifi_disconnect_flag.set()
        print("Unexpected disconnection from MQTT broker!")


#------------------------------------------------------    
            
#------------------Initiate Mqtt SPB-----------------
# Create the spB entity object
GroupId = "test"
NodeId = "test"
DeviceId = "DV01"

_DEBUG = False  # Enable debug messages

device = MqttSpbEntityDevice(GroupId, NodeId, DeviceId, _DEBUG)

device.on_message = callback_message_device  # Received messages
# device.on_connect = callback_connect_device
# device.on_disconnect = callback_disconnect_device

# Connect to the broker --------------------------------------------
serverUrl = "20.249.217.5"
_connected = False
# while not _connected:
#     print("Trying to connect to broker...")
#     _connected = device.connect(serverUrl, 1883, "user", "password")
#     if not _connected:
#         print("  Error, could not connect. Trying again in a few seconds ...")
#         time.sleep(3)
device.connect(serverUrl, 1883, "user", "password")
time.sleep(1)
#--------------------------------------------------------------------
# Create the spB entity object

node = MqttSpbEntityEdgeNode(GroupId, NodeId, _DEBUG)

node.on_message = callback_message_node  # Received messages

# Connect to the broker --------------------------------------------
_connected = False
# while not _connected:
#     print("Trying to connect to broker...")
#     _connected = node.connect(serverUrl, 1883, "user", "password")
#     if not _connected:
#         print("  Error, could not connect. Trying again in a few seconds ...")
#         time.sleep(3)
node.connect(serverUrl, 1883, "user", "password")
time.sleep(1)
######################################################3
# Create the spB entity object
GroupId = "test"
NodeId = "test"
DeviceId = "DV02"

_DEBUG = True  # Enable debug messages

device1 = MqttSpbEntityDevice(GroupId, NodeId, DeviceId, _DEBUG)

device1.on_message = callback_message_device  # Received messages

# Connect to the broker --------------------------------------------
serverUrl = "20.249.217.5"
_connected = False
# while not _connected:
#     print("Trying to connect to broker...")
#     _connected = device1.connect(serverUrl, 1883, "user", "password")
#     if not _connected:
#         print("  Error, could not connect. Trying again in a few seconds ...")
#         time.sleep(3)
device1.connect(serverUrl, 1883, "user", "password")
time.sleep(1)
#--------------------------------------------------------------------
# Create the spB entity object

node1 = MqttSpbEntityEdgeNode(GroupId, NodeId, _DEBUG)

node1.on_message = callback_message_node  # Received messages

# Connect to the broker --------------------------------------------
_connected = False
# while not _connected:
#     print("Trying to connect to broker...")
#     _connected = node1.connect(serverUrl, 1883, "user", "password")
#     if not _connected:
#         print("  Error, could not connect. Trying again in a few seconds ...")
#         time.sleep(3)
node1.connect(serverUrl, 1883, "user", "password")
time.sleep(1)


rebirth_flag = threading.Event()
def task_rebirth():
    global payload_device, payload_node
    var_string = ['deviceId', 'deviceProtocol', 'deviceAddress']
    while True:
        rebirth_flag.wait()
        if payload_node is not None:
            for item in payload_node['metrics']:
                if item['name'] == 'BDSEQ':
                    node.data.set_value(item['name'], int(item['value']))
                else:
                    node.data.set_value(item['name'], item['value'])
                print(item)
            # node.publish_birth()
            print(payload_node)

        if payload_device is not None:
            for item in payload_device['metrics']:
                if item['name'] in var_string:
                    device.data.set_value(item['name'], item['value'])
                else:
                    device.data.set_value(item['name'], 0)
                print(item)
            # device.publish_birth()
            print(payload_device)

        rebirth_flag.clear()


def task_wifi_disconnect():
    global is_disconnect_wifi
    count = 0
    while True:
        wifi_disconnect_flag.wait()
        while is_disconnect_wifi:
            time.sleep(1)
            count += 1
            print(count)
            if count == 300:
                print('Reset')
        count = 0
        wifi_disconnect_flag.clear()

def is_ethernet_connected(ip_address):
    try:
        # Execute the ping command asynchronously
        ping_command = ["ping", "-n", "1", str(ip_address)]
        ping_process = subprocess.Popen(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # You may want to check the return code of the ping process to determine success or failure
        return_code = ping_process.wait()

        # Optionally, you can also capture the output of the ping command
        ping_output, ping_error = ping_process.communicate()
        print("Ping output:", ping_output.decode())
        print("Ping error:", ping_error.decode())

        if return_code == 0:
            print("Ping command succeeded.")
            return True
        else:
            print(f"Ping command failed with return code {return_code}.")
            return False
        
    except subprocess.CalledProcessError:
        # Handle subprocess errors if needed
        print("Error running ipconfig command.")
        return False

def task_detect_disconnectPLC():
    htIPEthernet = '192.168.1.200'
    omIPEthernet = '192.168.250.20'

    htOldRes = -1
    omOldRes = -1

    countDisconnect = 0
    while True:
        res = is_ethernet_connected(htIPEthernet)
        print(res)
        if res == 1 and htOldRes != res:
            htOldRes = res
            print("Connected to PLC Siemens!")
        elif res != 1 and htOldRes != res:
            htOldRes = res
            countDisconnect += 1
            print(countDisconnect)
            print("Disconnected to PLC Siemens!")
        time.sleep(2)

        res = is_ethernet_connected(omIPEthernet)
        print(res)
        if res == 1 and omOldRes != res:
            omOldRes = res
            print("Connected to PLC Siemens!")
        elif res != 1 and omOldRes != res:
            omOldRes = res
            countDisconnect += 1
            print(countDisconnect)
            print("Disconnected to PLC Siemens!")
        time.sleep(2)

        if countDisconnect == 10:
            print('reset program')


# Send some telemetry values ---------------------------------------
if __name__ == '__main__':

    # t3 = threading.Thread(target=task_rebirth)
    # t1 = threading.Thread(target=task_wifi_disconnect)
    # t2 = threading.Thread(target=task_detect_disconnectPLC)

    # t3.start()
    # t1.start()
    # t2.start()
    while True:
        pass
        # device.publish_specific_data('DDEATH', 'bdSeq', 0)
        # # time.sleep(5)
        # node.publish_specific_data('NDEATH', 'bdSeq', 0)
        # time.sleep(2)
        # device1.publish_specific_data('DDEATH', 'bdSeq', 0)
        # # time.sleep(5)
        # node1.publish_specific_data('NDEATH', 'bdSeq', 0)
        # time.sleep(2)

        # device.publish_specific_data('DDEATH', 'bdSeq', 1)
        # # time.sleep(5)
        # node.publish_specific_data('NDEATH', 'bdSeq', 1)
        # time.sleep(5)
        # device1.publish_specific_data('DDEATH', 'bdSeq', 1)
        # # time.sleep(5)
        # node1.publish_specific_data('NDEATH', 'bdSeq', 1)
        # time.sleep(5)

        # device.publish_specific_data('DDEATH', 'bdSeq', 0)
        # # time.sleep(5)
        # node.publish_specific_data('NDEATH', 'bdSeq', 1)
        # time.sleep(5)
        # device1.publish_specific_data('DDEATH', 'bdSeq', 0)
        # # time.sleep(5)
        # node1.publish_specific_data('NDEATH', 'bdSeq', 1)
        # time.sleep(5)
        # node.publish_specific_data('NDEATH', 'bdSeq', 1)
        # time.sleep(1)
        # Update the data value
        device.data_set_value("nodeId", 'N02')
        device.data.set_value("nodeName", 'Khu ep cao su')
        device.data.set_value("Node Control/Rebirth", True)
        device.data.set_value("Node Control/Reboot", False)
        device.data.set_value("May ep cao su P010", 'DV01')
        device.data.set_value("BDSEQ", 0)
        # device.publish_birth()
        device.publish_data()
        time.sleep(2)

        device1.data.set_value("nodeId", 'N02')
        device1.data.set_value("nodeName", 'Khu ep cao su')
        device1.data.set_value("Node Control/Rebirth", True)
        device1.data.set_value("Node Control/Reboot", False)
        device1.data.set_value("May ep cao su P010", 'DV01')
        device1.data.set_value("BDSEQ", 0)
        # device.publish_birth()
        device1.publish_data()
        time.sleep(2)
        
        # node.data.set_value("injectionTime", round(random.uniform(1.0, 10.0),3))
        # node.data.set_value("injectionCycle", float(random.randint(10,20)))
        # node.data.set_value("counterShot", round(random.uniform(44.0, 47.0),2))
        # node.publish_birth()
        # # time.sleep(2)

        # device1.data.set_value("injectionTime", round(random.uniform(1.0, 10.0),3))
        # device1.data.set_value("injectionCycle", float(random.randint(10,20)))
        # device1.data.set_value("counterShot", round(random.uniform(44.0, 47.0),2))
        # device1.publish_birth()
        # # time.sleep(2)
        
        # node1.data.set_value("injectionTime", round(random.uniform(1.0, 10.0),3))
        # node1.data.set_value("injectionCycle", float(random.randint(10,20)))
        # node1.data.set_value("counterShot", round(random.uniform(44.0, 47.0),2))
        # node1.publish_birth()
        # time.sleep(2)
        # readSerail()

    # Disconnect device -------------------------------------------------
    # After disconnection the MQTT broker will send the entity DEATH message.
    print("Disconnecting device")
    device.disconnect()

    print("Application finished !")