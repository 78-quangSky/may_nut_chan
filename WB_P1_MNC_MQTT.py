from MyClasses import MQTT, spB
from MyClasses import restart_raspberry
from MyClasses import generate_general_data
from WB_P1_MNC_Variables import *
from WB_P1_MNC_PLC import *
from datetime import datetime, timedelta
import time

# topic_standard = 'HCM/HC001/Metric/'
topic_standard = 'Test/WB-MNC/Data/'

# --------------------------- Publish data -------------------------------------
def publish_data(varName, varAddr, varValue, KindOfData):
    if KindOfData == 'Alarm':
        client.publish_data(varAddr, varValue)
    else:
        client.publish_data(varName, varValue)
    Log.log_data(varName, varAddr, varValue, KindOfData, ST.is_connectWifi)

# --------------------------- Setup MQTT -------------------------------------
# Define MQTT call-back function
def on_connect(client, rc):
    global onStTimestamp, runStTimestamp
    print('Connected to MQTT broker with result code ' + str(rc))
    # publish machine status
    if ST.status_old >= 0:
        client.publish_data('machineStatus', ST.status_old)
    ST.is_connectWifi = 1

    if onStTimestamp != None:
        client.publish_data('machineStatus', onStTimestamp, is_payload=True)
        onStTimestamp = None
        
    if runStTimestamp != None:
        client.publish_data('machineStatus', runStTimestamp, is_payload=True)
        runStTimestamp = None
    
    init.Run = 0

def on_disconnect(client, rc):
    if rc != 0:
        print('Unexpected disconnection from MQTT broker')
        ST.is_connectWifi = 0

mqttBroker = '20.249.217.5'  # cloud
mqttPort = 1883
client = MQTT(host=mqttBroker, port=mqttPort, user="user", password="password")
client.standardTopic = topic_standard
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect()

# --------------------------- Check data -------------------------------------
old_operationTime = datetime.now()
offset_operationTime = 0

productCountAddr = 'D3039'
_, read_result = plc.readData(varAddr=productCountAddr, varType=DT.SDWORD)

while True:
    if int(read_result) > 100:
        try:
            with open(filepath + 'old_operationTime.txt') as file:
                offset_operationTime = float(file.read())
            break
        except FileNotFoundError:
            print('No old_operationTime.txt file')
            read_result = 0
        except Exception as e:
            print(e)
            read_result = 0
    else:
        publish_data('machineStatus', ST.On, ST.On, 'MachineStatus')
        ST.status_old = ST.On
        time.sleep(1)
        if not ST.is_connectWifi:
            timestamp = datetime.now().isoformat(timespec='microseconds')
            onStTimestamp = generate_general_data('machineStatus', ST.On, timestamp)
        break


# --------------------------- Setup SparkPlugB  -------------------------------------
def callback_message_device(topic, payload):
    try:
        print("Received MESSAGE: %s - %s" % (topic, payload))

        for item in payload['metrics']:
            if item['name'] == 'Reboot' and item['value'] == True:
                print('REBOOT!')
                restart_raspberry()
    except Exception as e:
        print(e)

GroupId = "WB"
NodeId = "NC"
DeviceId = "NCmachine"

device = spB(host=mqttBroker, port=mqttPort, GroupId=GroupId, NodeId=NodeId, DeviceId=DeviceId, levelEntity='device')
device.on_message = callback_message_device
device.connect()

