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

        self.units = self.c_units()
        # self.write('R07')
        # inpt = self.serial.readall().decode('utf-8')
        # inpt = inpt[3:4]
        
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
        msg = msg.decode("utf-8")
        if msg[0:-1] == '?43':
            print('Command error.')
        elif msg[0:-1] == '?46':
            print('Format error.')
        elif msg[0:-1] == '?50':
            print('Parity error.')
        elif msg[0:-1] == '?56':
            print('Serial Device Address Error.')
        else:
            return msg
        return None
        
    def readline(self):
        msg = self.serial.readline()
        return msg
        
    def close(self):
        self.serial.close()

    # rc is used to perform a write followed by a read.
    def rc(self, message):
        self.write(message)
        time.sleep(0.5)
        msg = self.read()
        return msg
        
    def reset(self):
        check = self.rc('Z02')
        if check[0:3] == 'Z02':
            flag = True
        else:
            flag = False
        return flag

    def measure(self):
        temp = self.rc('X01')[3:-1]
        return float(temp)

    # c for "change" units
    def c_units(self, selection=None):
        code = self.rc('R08')  # Requests device settings, need to only change temperature
        if code.__len__() > 6:
            # Find the returned command from the request
            return
        # Get the byte that stores what the instrument uses for temperature units.
        # Also grab the decimal place information (bits 0 - 2) to write the same
        # value to eeprom when the command to change temperature units is called.
        b = int(code[4], 16)
        if b > 7:
            temp = 'F'
            dec = b - 8
        else:
            temp = 'C'
            dec = b
        # Do nothing if the eeprom doesn't need to be updated.
        # Otherwise calculate the byte to send.
        if selection == None:
            return temp
        elif selection in ('F', 'f'):
            if temp == 'F':
                return 'F'
            else:
                b = str(hex(dec + 8))[2]
        elif selection in ('C', 'c'):
            if temp == 'C':
                return 'C'
            else:
                b = str(hex(dec))[2]
        self.rc('W'+code[1:4]+b)
        flag = self.reset()
        if flag:
            print('Units successfully changed to °' + selection.upper() + '.')

    def set_decimal(self, n):
        if not(isinstance(n, int)):
            print('Select an integer between 0 and 3')
            return
        if n < 0 or n > 3:
            print('Invalid decimal place.')
            return
        code = self.rc('R08')
        b = int(code[4], 16)
        temp = 0
        if b > 7:
            temp = 8
        b = str(hex(n + 1 + temp))[-1]
        self.rc('W' + code[1:4] + b)
        flag = self.reset()
        if flag:
            print('Decimal point successfully changed to ' + str(n) + '.')
        
if __name__ == '__main__':
    from serial_port import serial_ports
    import serial
    s = serial_ports()
    o = omegatc(s[0])
    o.c_units('f')
    o.close()
