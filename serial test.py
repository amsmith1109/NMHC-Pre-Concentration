import serial
import serial_port

ports = serial_port.serial_ports()

# valve_port = serial_port.scanner('Valve Controller')
# valves = serial.Serial(valve_port, baudrate=115200, timeout=0.05)
# 
# mfc_port = serial_port.scanner('Mass Flow Controller')
# mfc = serial.Serial(mfc_port, baudrate=115200, timeout=0.05)

### For Omega temperature controller
s = serial.Serial(ports[0],
                  baudrate=19200,
                  parity=serial.PARITY_ODD,
                  stopbits=serial.STOPBITS_ONE,
                  bytesize=serial.SEVENBITS,
                  timeout=0.05)

