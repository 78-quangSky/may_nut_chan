# from MyClasses.Broker.SparkPlugB.mqtt_spb_wrapper import*
# from MyClasses.Broker.SparkPlugB.function import SparkplugB as spB
from MyClasses import spB
import random
import time

#--------------------------- Setup MQTT SPB -------------------------
def callback_message(topic, payload, lsName, lsValue, lsDataType, lsTimestamp):
    print("Received MESSAGE: %s - %s" % (topic, payload))
    print(lsName)
    print(lsValue)
    print(lsDataType)
    print(lsTimestamp)

def callback_connect(rc):
    is_disconnect_wifi = 0
    print("Connected to MQTT broker with result code "+str(rc))


def callback_disconnect(rc):
    if rc != 0:
        print("Unexpected disconnection from MQTT broker!")


#------------------------------------------------------    
serverUrl = "20.249.217.5"
port = 1883            
#------------------Initiate Mqtt SPB-----------------
# Create the spB entity object
GroupId = "g1"
NodeId = "N1"
DeviceId = "DV01"

_DEBUG = False  # Enable debug messages

device = spB(host=serverUrl, port=port, GroupId=GroupId, NodeId=NodeId, DeviceId=DeviceId, levelEntity='Device')
device.on_message = callback_message  # Received messages
device.on_connect = callback_connect
device.on_disconnect = callback_disconnect

device.data_set_value('ka', 0)
device.data_set_value('kb', 0)
device.data_set_value('kc', 0)

device.connect()
device.publish_birth()

GroupId = "g2"
NodeId = "N2"

node = spB(host=serverUrl, port=port, GroupId=GroupId, NodeId=NodeId, DeviceId=DeviceId, levelEntity='Node')
node.on_message = callback_message  # Received messages
node.on_connect = callback_connect
node.on_disconnect = callback_disconnect

node.data_set_value('ka', 0)
node.data_set_value('kb', 0)
node.data_set_value('kc', 0)

node.connect()
node.publish_data()

while True:
    device.Publish_Data('ka', random.randint(0, 100))
    time.sleep(1)
    device.Publish_Birth('kb', random.randint(0, 100))
    time.sleep(1)
    device.Publish_Death(random.randint(0, 100))
    time.sleep(1)
    device.Publish_Command('kc', random.randint(0, 100))
    time.sleep(1)

    node.Publish_Birth('kb', random.randint(0, 100))
    time.sleep(1)
    node.Publish_Death(random.randint(0, 100))
    time.sleep(1)
    node.Publish_Command('kc', random.randint(0, 100))
    time.sleep(1)
