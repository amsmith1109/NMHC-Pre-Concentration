import serial
import time
import codecs

class omegatc:
    # Initialize with factory default settings.
    #
    # From Communication Manual:
    # To Enable the iSeries Protocol, set Modbus
    # menu item to “No” in the Bus Format Submenu
    # of the Communication Menu. Refer to Section 5.7.11.
    def __init__(self,
                 com,
                 baud=9600,
                 parity=serial.PARITY_ODD,
                 size=serial.SEVENBITS,
                 stops=serial.STOPBITS_ONE):
        
        # Initialize serial connection based on inputs
        # Use a USB-to-RS232 Adapter for the connection.
        timeout = 2e3/baud
        
        self.serial = serial.Serial(
            com,
            baudrate=baud,
            parity=parity,
            stopbits=stops,
            bytesize=size,
            timeout=timeout)
        self.serial.write(b'^AE\r')
        
        t = time.time()
        while True:
            time.sleep(0.01)
            if self.serial.in_waiting==9:
                break
            if abs(time.time() - t) > 5:
                print('Unable to connect with omega device.')
                break
        print('Connection to Omega TC successful!')        
        # check returns the communication configuration:
        # Byte 1 - Recognition character
        # Byte 2 - Meter address
        # Byte 3 - Bus Format
        # Byte 4 - Communications configuration
        check = self.serial.readall()
        self.__communication_protocol__ = check
        
        recognition = codecs.decode(check[0:2],'hex')
        self.recognition = recognition
        self.port = com
        #self.address = Addr
        
    def write(self, message):
        #Check input type and convert it to byte string
        if isinstance(message, str):
            msg = message.encode('utf-8')
        elif isinstance(message, bytes):
            msg = message
        elif isinstance(message, float) or isinstance(message, int):
            msg = str(message)
            msg = msg.encode('utf-8')
        else:
            print('Incorrect message')
        
        # Check if a return line is present
        # If not, one is added.
        if msg[-1] != b'\r': 
            msg = msg + b'\r'
        
        # Check if the recognition character is present
        # Ignore if the instrument settings are called
        if msg[0] != self.recognition:
            if msg[0] != b'^':
                msg = self.recognition + msg
            
        self.serial.write(msg)
        
    def read(self):
        msg = self.serial.readall()
        if msg[0:-1] == b'?43':
            print('Command error.')
        elif msg[0:-1] == b'?46':
            print('Format error.')
        elif msg[0:-1] == b'?50':
            print('Parity error.')
        elif msg[0:-1] == b'?56':
            print('Serial Device Address Error.')
        if __name__ != '__main__':
            print(msg)
        return msg
        
    def readline(self):
        msg = self.serial.readline()
        if __name__ != '__main__':
            print(msg)
        return msg
        
    def close(self):
        self.serial.close()
        
    def rc(self, message):
        self.write(message)
        time.sleep(0.5)
        self.read()
        
    def reset(self):
        self.write('Z02')
        
        
if __name__ == '__main__':
    from serial_port import serial_ports
    import serial
    s = serial_ports()
    o = omegatc(s[0])