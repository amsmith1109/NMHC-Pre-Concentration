import sys
import glob
import serial
import time

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    result.remove('/dev/ttyAMA0') #removes default port from list
    return result

def scanner(name, BR=115200):
    ports = serial_ports()
    result = []
    for p in ports:
        try:
            s = serial.Serial(p, baudrate=BR, timeout=0.05)
            if s.in_waiting > 0:
                s.readall()
            s.write(b'name()\r\n')
            time.sleep(0.5)
            device_name = s.readall()
            if name in device_name.decode("utf-8"):
                result.append(p)
            s.close()
        except (OSError, serial.SerialException):
            pass
    return result

if __name__ == '__main__':
    print(serial_ports())