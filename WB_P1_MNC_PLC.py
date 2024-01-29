from MyClasses import PLC_Mitsu, DT
from WB_P1_MNC_Variables import*

__HOST = '192.168.1.250' # REQUIRED
__PORT = 4095           # OPTIONAL: default is 5007
plc = PLC_Mitsu.PLC(host=__HOST, port=__PORT, is_pc=is_pc, nameStation='May_nut_chan')
plc.connect()