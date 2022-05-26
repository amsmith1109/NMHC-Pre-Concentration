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
        
        units = self.unit().decode('utf-8')
        model = self.model().decode('utf-8')
        self.serial.write(b'f\r')
        scale = self.serial.readall().decode('utf-8').split()
        self.units = units[0:-2]
        self.model = model[0:-2]
        self.scale = scale
        # The conversion to float then back to string gets rid of the added
        # exponent. That way a print displays 10.0, not 10.00e+0.
        self.scale = str(float(self.scale[0])), str(float(self.scale[1]))
    
    def info(self):
        print(self.model + ':')
        print('Measurements are made in ' + self.units + '.')
        print('Gauge 1 has a range of 0 - ' + self.scale[0] + ' ' + self.units)
        print('Gauge 2 has a range of 0 - ' + self.scale[1] + ' ' + self.units)
        print('')
        print('Use <object>.read() to get instrument measurements.')
    
    def read(self):
        self.serial.write(b'p\r')
        raw = self.serial.readall()
        g1,g2 = raw.decode('utf-8').split()
        return float(g1),float(g2)
    
    def model(self):
        self.serial.write(b'v\r')
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
    t.info()