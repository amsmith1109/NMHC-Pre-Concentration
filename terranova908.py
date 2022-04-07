import serial_port
import serial
import time

class terranova908:
    # Uses default communication parameters for terranova 908A
    def __init__(self,
                 com,
                 baud=9600,
                 parity=serial.PARITY_NONE,
                 size=serial.EIGHTBITS,
                 stops=serial.STOPBITS_ONE):
        self.port = com
        timeout = 2e3/baud
        
        self.serial = serial.Serial(
            com,
            baudrate=baud,
            parity=parity,
            stopbits=stops,
            bytesize=size,
            timeout=timeout)
        
        self.units = self.unit()
        self.model = self.model()
        self.scale = self.scale()
        
    def read(self):
        self.serial.write(b'p\r')
        raw = self.serial.readall()
        g1,g2 = raw.decode('utf-8').split()
        return float(g1),float(g2)
    
    def model(self):
        self.serial.write(b'v\r')
        return self.serial.readall()
    
    def scale(self):
        self.serial.write(b'f\r')
        return self.serial.readall()
            
    def unit(self):
        self.serial.write(b'u\r')
        return self.serial.readall()
    
    def write(self, msg):
        self.serial.write(msg)
        
    def readall(self):
        self.serial.readall()
        
if __name__ == '__main__':
    from serial_port import serial_ports
    import serial
    s = serial_ports()
    t = terranova908('/dev/ttyUSB0') #setting this to the port I plugged in to
    print(t)
    