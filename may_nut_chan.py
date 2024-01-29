from pymelsec import Type3E
from pymelsec.constants import DT
import paho.mqtt.client as mqtt
import time
import pandas as pd
import os, sys
import threading
from datetime import datetime, timedelta
import json
from mqtt_spb_wrapper import*
import asyncio

# time.sleep(20)

is_raspberry = 0

if is_raspberry:
    header_topic_mqtt = '/home/'
else:
    header_topic_mqtt = 'home/'

'''
    Quy định trạng thái:
    0: On (Khi vừa bật máy)
    1: Run (Running)
    2: Idle (trạng thái ngừng do không có đơn hàng, lúc đầu máy Run nhưng sau đó ngưng nhưng không tắt máy)
    3. Alarm
    4. Setup (bảo trì)
    5. Off
    6. Ready (khi power on và ko bị idle, ko bị fault)
    7. Wifi disconnect

'''
class ST():
    On = 0
    Run = 1
    Idle = 2
    Alarm = 3
    Setup = 4
    Off = 5
    Ready = 6
    Wifi_disconnect = 7

lock = threading.Lock()

# Tạo các ngắt với các task khi bị mất kết nối ethernet
reConEth_flg = threading.Event()
enStoreData_flg = threading.Event()
t1_interupt = threading.Event()
t2_interupt = threading.Event()
t3_interupt = threading.Event()
t4_interupt = threading.Event()
t5_interupt = threading.Event()
t6_interupt = threading.Event()
t7_interupt = threading.Event()
t8_interupt = threading.Event()
t9_interupt = threading.Event()
t10_interupt = threading.Event()

t1_interupt.set()
t2_interupt.set()
t3_interupt.set()
t4_interupt.set()
t5_interupt.set()
t6_interupt.set()
t7_interupt.set()
t8_interupt.set()
t9_interupt.set()
t10_interupt.set()


# Các biến setting về chiều cao để xác định sản phẩm đạt, ko đạt
may_nut_chan_setting_value = pd.read_csv(header_topic_mqtt + 'pi/setting_value.csv', index_col=0)
dset_addr = [*may_nut_chan_setting_value['ID_Setting']]
dset_type = [*may_nut_chan_setting_value['Setting_Type']]
dset_name = [name.strip() for name in [*may_nut_chan_setting_value['Setting_Name']]]
dset_lenght = len(dset_addr)
# dset_old = [*may_nut_chan_setting_value['Setting_Value']]
dset_old = [-1]*dset_lenght

# Các biến good, bad, eff 
may_nut_chan_counting_value = pd.read_csv(header_topic_mqtt + 'pi/counting_value.csv', index_col=0)
dcount_addr = [*may_nut_chan_counting_value['ID_Counting']]
dcount_type = [*may_nut_chan_counting_value['Counting_Type']]
dcount_name = [name.strip() for name in [*may_nut_chan_counting_value['Counting_Name']]]
dcount_lenght = len(dcount_addr)
# dcount_old = [*may_nut_chan_counting_value['Counting_Value']]
dcount_old = [-1]*dcount_lenght

# Các biến trang Rejection Details
may_nut_chan_checking_value = pd.read_csv(header_topic_mqtt + 'pi/checking_value.csv', index_col=0)
dcheck_addr = [*may_nut_chan_checking_value['ID_Checking']]
dcheck_type = [*may_nut_chan_checking_value['Checking_Type']]
dcheck_name = [name.strip() for name in [*may_nut_chan_checking_value['Checking_Name']]]
dcheck_lenght = len(dcheck_addr)
# dcheck_old = [*may_nut_chan_checking_value['Checking_Value']]
dcheck_old = [-1]*dcheck_lenght


# Các biến alarm về danh sách lỗi hiển thị trên HMI
may_nut_chan_alarm_value = pd.read_csv(header_topic_mqtt + 'pi/alarm_value.csv', index_col=0)
dalarm_addr = [*may_nut_chan_alarm_value['ID_Alarm']]
dalarm_type = [*may_nut_chan_alarm_value['Alarm_Type']]
dalarm_name = [name.strip() for name in [*may_nut_chan_alarm_value['Alarm_Name']]]
dalarm_lenght = len(dalarm_addr)
# dalarm_old = [*may_nut_chan_alarm_value['Alarm_Value']]
dalarm_old = [-1]*dalarm_lenght


is_connectWifi = 0
status_old = -1
initRunSt = 1
runStTimestamp = None
onStTimestamp = None
'''
M1	    MANUAL MODE
M0	    AUTO ON
M170	ALL B/F FLT
M3	    FLT FLG
Y4	    INDEX MOTOR ON
T4	    M/C IDLE TD
M799    POWER ON

M0, Y4  	Run	    -->     M0.Y4./M170./M3./T4
M170, M3	Alarm	-->     (M170+M3)
T4	        Idle	-->     T4./Y4./M170./M3
M1, Y4  	Setup   -->     M1.Y4./M170./M3./T4
Y4 = 0	    Ready	-->     /Y4./T4./M170./M3
M799 = 0    Off     -->     /M799 hoặc khi code bị lỗi do ko thể giao tiếp với PLC        
M799 = 1    ON      -->     M799 

'''
list_status_addr = ['M1', 'M0', 'Y4', 'M170', 'M3', 'TS4', 'SM400']
list_status_old = [0]*len(list_status_addr)

#---------------------------------------------------------------------------
def create_excel_file(file_name):
    try:
        with open(header_topic_mqtt + 'pi/' + file_name) as store_data:
            pass
    except FileNotFoundError:
        with open(header_topic_mqtt + 'pi/' + file_name,'w+') as store_data:
            store_data.write('{0},{1},{2},{3},{4},{5},{6}\n'.format('No.','ID','Name Variable','Value','Timestamp','Kind of Data','Connected Wifi'))

create_excel_file('stored_data.csv')
#---------------------------------------------------------------------------
__HOST = '192.168.1.250' # REQUIRED
__PORT = 4095           # OPTIONAL: default is 5007
__PLC_TYPE = 'Q'     # OPTIONAL: default is 'Q'

while True:
    if is_raspberry:
        res = os.system('ping -c 1 ' + str(__HOST) + ' > /dev/null 2>&1')
    else:
        res = os.system('ping -n 1 ' + str(__HOST) + ' > nul')
    time.sleep(1)
    if res == 0:
        print('Connected to the ip')
        break
    else:
        print("Can't connect to PLC")

plc = Type3E(host=__HOST, port=__PORT, plc_type=__PLC_TYPE)
plc.set_access_opt(comm_type='binary')
plc.connect(ip=__HOST, port=__PORT)


#---------- Generate Json Payload -------------------------------
def generate_data_status(state, value):
	data = [{
                'name': 'machineStatus',
                'value': value,
                'timestamp': datetime.now().isoformat(timespec='microseconds')
	}]
	return (json.dumps(data))


def generate_data(data_name, data_value):
	data = [{
                'name': str(data_name),
                'value': data_value,
                'timestamp': datetime.now().isoformat(timespec='microseconds')
	}]
	return (json.dumps(data))


def generate_data_disconnectWifi(data_name, data_value, timestamp):
	data = [{
                'name': str(data_name),
                'value': data_value,
                'timestamp': timestamp
	}]
	return (json.dumps(data))

#-------------------------------------------------------------

#----------------------Option Functions-----------------------
def restart_program():
    python = sys.executable
    os.execl(python,python, *sys.argv)


def restart_raspberry():
    os.system('sudo reboot')

#-------------------------------------------------------------

topic_standard = 'HCM/HC001/Metric/'
# topic_standard = 'Test/WEMBLEY/Data/'

#----------------Store and Publish Functions------------------
def store_and_pubish_data(No, Name, Value, RealValue, KindOfData):
    global is_connectWifi
    with lock:
        Timestamp = datetime.now().isoformat(timespec='microseconds')
        with open(header_topic_mqtt + 'pi/stored_data.csv','a+') as store_data:
            store_data.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(No, Value.device, Name, RealValue, Timestamp, KindOfData, is_connectWifi))

        data = generate_data(Name, RealValue)
        mqtt_topic = topic_standard + str(Name)
        if KindOfData == 'Alarm':
            data = generate_data(Value.device, RealValue)
        print(data)
        client.publish(mqtt_topic,str(data),1,1)

        if is_connectWifi:
            print(f'{No}: ',Value.device, Name, RealValue)
        else:
            print('LOG ->', f'{No}: ',Value.device, Name, RealValue)
            with open(header_topic_mqtt + 'pi/stored_disconnectWifi_data.txt', 'a+') as file:
                file.write(str(data)+'\n')


def store_and_publish_status(No, nameStatus, IDStatus):
    global is_connectWifi
    with lock:
        Timestamp = datetime.now().isoformat(timespec='microseconds')

        with open(header_topic_mqtt + 'pi/stored_data.csv','a+') as store_data:
            store_data.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(No, nameStatus, nameStatus, IDStatus, Timestamp, 'MachineStatus', is_connectWifi))

        data = str(generate_data_status(nameStatus, IDStatus))
        client.publish(topic_standard + 'machineStatus',data,1,1)
        print(data)

        if not is_connectWifi:
            with open(header_topic_mqtt + 'pi/stored_disconnectWifi_data.txt', 'a+') as file:
                file.write(data+'\n')

#-------------------------------------------------------------

# --------------------------- Setup MQTT -------------------------------------
# Define MQTT call-back function
def on_connect(client, userdata, flags, rc):
    global status_old, is_connectWifi, initRunSt, onStTimestamp, runStTimestamp
    print('Connected to MQTT broker with result code ' + str(rc))

    if status_old == 0:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('On', 0)),1,1)
    elif status_old == 1:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('Run', 1)),1,1)
    elif status_old == 2:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('Idle', 2)),1,1)
    elif status_old == 3:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('Alarm', 3)),1,1)
    elif status_old == 4:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('Setup', 4)),1,1)
    elif status_old == 5:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('OFF', 5)),1,1)
    elif status_old == 6:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('Ready', 6)),1,1)
    elif status_old == 7:
        client.publish(topic_standard + 'machineStatus',str(generate_data_status('Wifi disconnect', 7)),1,1)

    if onStTimestamp != None:
        client.publish(topic_standard + 'machineStatus', str(onStTimestamp), 1, 1)
        print(onStTimestamp)
        onStTimestamp = None
        
    if runStTimestamp != None:
        client.publish(topic_standard + 'machineStatus', str(runStTimestamp), 1, 1)
        print(runStTimestamp)
        runStTimestamp = None
    
    initRunSt = 0
    is_connectWifi = 1

def on_disconnect(client, userdata, rc):
    global is_connectWifi
    if rc != 0:
        print('Unexpected disconnection from MQTT broker')
        is_connectWifi = 0


mqttBroker = '20.249.217.5'  # cloud
mqttPort = 1883
mqttKeepAliveINTERVAL = 45

# Initiate Mqtt Client
client = mqtt.Client()
# if machine is immediately turned off --> last_will sends 'machineStatus: Off' to topic
client.will_set(topic_standard + 'machineStatus',str(generate_data_status('Off', ST.Off)),1,1)
# Register callback function
client.on_connect = on_connect
client.on_disconnect = on_disconnect
# Connect with MQTT Broker
print('connecting to broker ',mqttBroker)
# Check connection to MQTT Broker 
try:
	client.connect(mqttBroker, mqttPort, mqttKeepAliveINTERVAL)
except:
	print("Can't connect MQTT Broker!")
	
client.loop_start()
time.sleep(1)

old_operationTime = datetime.now()
offset_operationTime = 0

productCountAddr = 'D3039'
read_result = plc.batch_read(ref_device=productCountAddr, read_size=1, data_type=DT.SDWORD)
read_result = read_result[0].value
while True:
    if int(read_result) > 100:
        try:
            with open(header_topic_mqtt + 'pi/old_operationTime.txt') as file:
                offset_operationTime = float(file.read())
            break
        except FileNotFoundError:
            print('No old_operationTime.txt file')
            read_result = 0
        except Exception as e:
            print(e)
            read_result = 0
    else:
        store_and_publish_status(0, 'On', ST.On)
        status_old = ST.On
        time.sleep(1)
        if not is_connectWifi:
            timestamp = datetime.now().isoformat(timespec='microseconds')
            onStTimestamp = generate_data_disconnectWifi('machineStatus', ST.On, timestamp)
        break

# ----------------------------------------------------------------------------

#--------------------------- Setup MQTT SPB ----------------------------
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

_DEBUG = True  # Enable debug messages

Device = MqttSpbEntityDevice(GroupId, NodeId, DeviceId, _DEBUG)

Device.on_message = callback_message_device  # Received messages

Device.data.set_value('machineStatus', 'On')

# Connect to the broker --------------------------------------------
_connected = False
while not _connected:
    print("Trying to connect to broker...")
    _connected = Device.connect(mqttBroker, 1883, "user", "password")
    if not _connected:
        print("  Error, could not connect. Trying again in a few seconds ...")
        time.sleep(3)
time.sleep(1)
Device.publish_birth()

#---------------------------------------------------------------------------
def task_data_setting_process():
    global may_nut_chan_setting_value, dset_old
    count = 0

    for i in range(dset_lenght):
        time.sleep(0.01)
        t1_interupt.wait()
        try:
            with lock:
                read_result = plc.batch_read(
                    ref_device=str(dset_addr[i]),
                    read_size=1, 
                    data_type=str(dset_type[i])
                )
            for value in read_result:
                real_value = value.value/100
                store_and_pubish_data(count, dset_name[i], value, real_value, 'Setting')
                dset_old[i] = read_result[0].value

        except Exception as e:
            print('task_data_setting_process')
            print(e)
            reConEth_flg.set()

    while True:
        for i in range(dset_lenght):
            time.sleep(5)
            t1_interupt.wait()
            try:
                with lock:
                    read_result = plc.batch_read(
                        ref_device=str(dset_addr[i]),
                        read_size=1, 
                        data_type=str(dset_type[i])
                    )
                if dset_old[i] != read_result[0].value:
                    for value in read_result:
                        real_value = value.value/100
                        store_and_pubish_data(count, dset_name[i], value, real_value, 'Setting')
                        count+=1
                        dset_old[i] = read_result[0].value

            except Exception as e:
                print('task_data_setting_process')
                print(e)
                reConEth_flg.set()


def task_data_count_process():
    global may_nut_chan_counting_value
    count = 0
    errorProduct = 0    

    while True:
        for i in range(dcount_lenght):
            time.sleep(0.01)
            t2_interupt.wait()
            try:
                with lock:
                    read_result = plc.batch_read(
                        ref_device=str(dcount_addr[i]),
                        read_size=1, 
                        data_type=str(dcount_type[i]), 
                    )
                if dcount_old[i] != read_result[0].value:
                    for value in read_result:

                        if dcount_name[i] == 'EFF':
                            real_value =  int(value.value)/10 
                        elif dcount_name[i] == 'S8_TOTAL_HEIGHT_TR1':
                            real_value = int(value.value)/100
                        elif dcount_name[i] == 'S8_TOTAL_HEIGHT_TR3':
                            real_value = int(value.value)/100
                        elif dcount_name[i] == 'S9_TOTAL_HEIGHT_TR2':
                            real_value = int(value.value)/100
                        elif dcount_name[i] == 'S9_TOTAL_HEIGHT_TR4':
                            real_value = int(value.value)/100
                        else:
                            real_value = value.value
                        
                        store_and_pubish_data(count, dcount_name[i], value, real_value, 'Counting')
                        count+=1
                        dcount_old[i] = read_result[0].value
                        
            except Exception as e:
                print('task_data_count_process')
                print(e)
                reConEth_flg.set()


# async def task_publish_operationTime():
#     global old_operationTime, offset_operationTime
#     while True:
#         await asyncio.sleep(1)
#         # t10_interupt.wait()

#         new_operationTime = datetime.now()
#         delta_operationTime = (new_operationTime - old_operationTime + timedelta(seconds=offset_operationTime)).total_seconds()
#         _delta_operationTime = (datetime.fromtimestamp(delta_operationTime) + timedelta(hours=-7)).strftime('%H:%M:%S')
#         data = generate_data('operationTimeRaw', _delta_operationTime)
#         topic = topic_standard + 'operationTimeRaw'
#         with lock:
#             client.publish(topic, data, 1, 1)
#             with open(header_topic_mqtt + 'pi/old_operationTime.txt', 'w+') as file:
#                 file.write(str(delta_operationTime))
#         print(data)


def task_publish_operationTime():
    global old_operationTime, offset_operationTime
    while True:
        time.sleep(1)
        # t10_interupt.wait()

        new_operationTime = datetime.now()
        delta_operationTime = (new_operationTime - old_operationTime + timedelta(seconds=offset_operationTime)).total_seconds()
        _delta_operationTime = (datetime.fromtimestamp(delta_operationTime) + timedelta(hours=-7)).strftime('%H:%M:%S')
        data = generate_data('operationTimeRaw', _delta_operationTime)
        topic = topic_standard + 'operationTimeRaw'
        with lock:
            client.publish(topic, data, 1, 1)
            with open(header_topic_mqtt + 'pi/old_operationTime.txt', 'w+') as file:
                file.write(str(delta_operationTime))
        print(data)


def task_data_checking_process():
    global may_nut_chan_checking_value
    count = 0

    while True:
        for i in range(dcheck_lenght):
            time.sleep(0.01)
            t3_interupt.wait()
            try: 
                with lock:
                    read_result = plc.batch_read(
                        ref_device=str(dcheck_addr[i]),
                        read_size=1, 
                        data_type=str(dcheck_type[i]), 
                    )
                if dcheck_old[i] != read_result[0].value:
                    for value in read_result:
                        store_and_pubish_data(count, dcheck_name[i], value, value.value, 'Checking')
                        count+=1
                        dcheck_old[i] = read_result[0].value

            except Exception as e:
                print('task_data_checking_process')
                print(e)
                reConEth_flg.set()


def task_data_alarm_process():
    global may_nut_chan_alarm_value
    count = 0

    while True:
        for i in range(dalarm_lenght):
            time.sleep(0.01)
            t5_interupt.wait()
            try: 
                with lock:
                    read_result = plc.batch_read(
                        ref_device=str(dalarm_addr[i]),
                        read_size=1, 
                        data_type=str(dalarm_type[i]), 
                    )
                if dalarm_old[i] != read_result[0].value:
                    for value in read_result:
                        store_and_pubish_data(count, dalarm_name[i], value, value.value, 'Alarm')
                        count+=1
                        dalarm_old[i] = read_result[0].value

            except Exception as e:
                print('task_data_alarm_process')
                print(e)
                reConEth_flg.set()


def task_machineStatus_process():
    '''
    M1	    MANUAL MODE
    M0	    AUTO ON
    M170	ALL B/F FLT
    M3	    FLT FLG
    Y4	    INDEX MOTOR ON
    T4	    M/C IDLE TD
    SM400    POWER ON
    '''
    global status_old, initRunSt, is_connectWifi, runStTimestamp
    count = 0
    status_new = -1

    while True:
        try:
            for i in range(len(list_status_addr)):
                t6_interupt.wait()
                time.sleep(0.01)
                with lock:
                    read_result = plc.batch_read(
                        ref_device=str(list_status_addr[i]),
                        read_size=1, 
                        data_type=DT.BIT 
                    )
                if list_status_old[i] != read_result[0].value:
                    list_status_old[i] = read_result[0].value
                    value = read_result[0]
                    print(f'{count}: ',value.device, value.value)

            M1 = list_status_old[0]
            M0 = list_status_old[1]
            Y4 = list_status_old[2]
            M170 = list_status_old[3]
            M3 = list_status_old[4]
            T4 = list_status_old[5]
            SM400 = list_status_old[6]

            if SM400:
                if M0 and Y4 and (not M3) and (not T4):
                    status_new = ST.Run
                    if status_old != status_new:
                        store_and_publish_status(count, 'Run', ST.Run)
                        status_old = status_new
                        count += 1

                        if initRunSt and not is_connectWifi:
                            timestamp = datetime.now().isoformat(timespec='microseconds')
                            runStTimestamp = generate_data_disconnectWifi('machineStatus', ST.Run, timestamp)
                            initRunSt = 0

                elif T4 and (not Y4) and (not M3) and status_old!=ST.Setup and status_old!=ST.On:
                    status_new = ST.Idle
                    if status_old != status_new:
                        store_and_publish_status(count, 'Idle', ST.Idle)
                        status_old = status_new
                        count += 1

                elif (M3):
                    status_new = ST.Alarm
                    if status_old != status_new:
                        store_and_publish_status(count, 'Alarm', ST.Alarm)
                        status_old = status_new
                        count += 1

                elif M1 and Y4 and (not M3) and (not T4):
                    status_new = ST.Setup
                    if status_old != status_new:
                        store_and_publish_status(count, 'Setup', ST.Setup)
                        status_old = status_new
                        count += 1

        except Exception as e:
            print('task_machineStatus_process')
            print(e)
            reConEth_flg.set()


def task_reconnect_ethernetPLC():
    global status_old
    """
    -handles connect/disconnect/reconnect
    -connection-monitoring with cyclic read of the service-level
    """
    __HOST = '192.168.1.250' # REQUIRED
    __PORT = 4095           # OPTIONAL: default is 5007
    while True:
        reConEth_flg.wait()
        print('PLC disconnect!')

        t1_interupt.clear()
        t2_interupt.clear()
        t3_interupt.clear()
        t10_interupt.clear()
        t5_interupt.clear()
        t6_interupt.clear()
        t7_interupt.clear()
        t8_interupt.clear()
        t9_interupt.clear()
        t10_interupt.clear()

        store_and_publish_status(ST.Off, 'Off', ST.Off)

        case = 0
        count = 0
        alwaysOn = 'SM400'
        
        while True:
            print(case)
            if case == 1:
                # connect
                print("connecting...")
                try:
                    plc.connect(__HOST, __PORT)
                    print("connected!")

                    case = 2
                except Exception as e:
                    print("connection error:", e)
                    case = 1
                    time.sleep(5)
            elif case == 2:
                # running => read cyclic the service level if it fails disconnect and unsubscribe => wait 5s => connect
                try:
                    with lock:
                        read_result = plc.batch_read(
                            ref_device=alwaysOn,
                            read_size=1, 
                            data_type=DT.BIT, 
                        )

                    service_level = read_result[0].value
                    print("service level:", service_level)
                    if service_level:
                        count += 1
                        case = 2
                        time.sleep(0.2)
                        if count == 5:
                            count = 0
                            break
                    else:
                        case = 3
                        time.sleep(5)
                except Exception as e:
                    print("error during operation:", e)
                    case = 3
            elif case == 3:
                # disconnect
                print("disconnecting...")
                try:
                    plc.close()
                except Exception as e:
                    print("disconnection error:", e)
                case = 0
            else:
                # wait
                case = 1
                time.sleep(5)

        store_and_publish_status(status_old, 'status_old', status_old)
        reConEth_flg.clear()

        t1_interupt.set()
        t2_interupt.set()
        t3_interupt.set()
        t10_interupt.set()
        t5_interupt.set()
        t6_interupt.set()
        t7_interupt.set()
        t8_interupt.set()
        t9_interupt.set()
        t10_interupt.set()

async def test():
    while True:
        print('test')
        await asyncio.sleep(1)

def run_task_publish_operationTime():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task_publish_operationTime())
    # loop.run_until_complete(asyncio.gather(task_publish_operationTime(), test()))
    # loop.create_task(task_publish_operationTime())
    # loop.run_forever()


#---------------------------------------------------------------------------

if __name__ == '__main__':
    
    t1 = threading.Thread(target=task_data_setting_process)
    t2 = threading.Thread(target=task_data_count_process)
    t3 = threading.Thread(target=task_data_checking_process)
    t4 = threading.Thread(target=task_data_alarm_process)
    t5 = threading.Thread(target=task_machineStatus_process)
    t6 = threading.Thread(target=task_publish_operationTime)
    # t7 = threading.Thread(target=run_task_publish_operationTime)

    task_reconnect_ehtPLC = threading.Thread(target=task_reconnect_ethernetPLC)

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    # t7.start()

    task_reconnect_ehtPLC.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    # t7.join()

    task_reconnect_ehtPLC.join()
    while True:
        pass

        