from MyClasses import PLC_Mitsu
from MyClasses import PLC_Rockwell

plc = PLC_Rockwell.PLC('192.168.1.20', 1230)

plc.readData('M0', 'BOOL')
plc.plc.Read('M0')