from serial_port import serial_ports
import serial
from omega_tc import omegatc
s = serial_ports()
# o = omegatc(s[0],
#             baud=9600,
#             parity=serial.PARITY_ODD,
#             stops=serial.STOPBITS_ONE,
#             size=serial.SEVENBITS,
#             timeout=0.05,
#             recognition='*',
#             Addr=1)
# stp = [serial.STOPBITS_ONE, serial.STOPBITS_TWO]
# pty = [serial.PARITY_ODD, serial.PARITY_NONE, serial.PARITY_EVEN]
# sz = [serial.SEVENBITS, serial.EIGHTBITS]
# bd = [19200]
# for i in stp:
#     for j in pty:
#         for k in sz:
#             for z in bd:
#                 print([i,j,k,z])
#                 o = omegatc(s[0], baud=z, size=k, parity=j, stops=i)
#                 o.rc('^AE \r')
#                 o.close()
                
o = omegatc(s[0])
o.rc('^AE\r')
