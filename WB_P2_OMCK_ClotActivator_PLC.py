from MyClasses import PLC_S7_200
from WB_P2_OMCK_ClotActivator_Variables import* 

_HOST = '192.168.0.60'

plc_ClotActivator = PLC_S7_200.PLC(host=_HOST, nameStation='Clot_Activator')
plc_ClotActivator.connect()