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
    
    # Performs a serial write on the RS232 line.
    # Some functionality is added to mainstream sending messages.
    # Strings are automatically converted to byte arrays.
    # Recognition character and return lines are automatically added.
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
            msg = 'Command error.'
        elif msg[0:-1] == '?46':
            msg = 'Format error.'
        elif msg[0:-1] == '?50':
            msg = 'Parity error.'
        elif msg[0:-1] == '?56':
            msg = 'Serial Device Address Error.'
        return msg
        
    def readline(self):
        msg = self.serial.readline()
        return msg
        
    def close(self):
        self.serial.close()

    # echo is used to perform a write followed by a read.
    def echo(self, message):
        self.write(message)
        time.sleep(self.serial.timeout)
        msg = self.read()
        return msg
        
    def reset(self):
        check = self.echo('Z02')
        if check[0:3] == 'Z02':
            flag = True
        else:
            flag = False
        return flag

    def measure(self):
        temp = self.echo('X01')[3:-1]
        return float(temp)

    # c for "change" units. can use upper or lower case for celcius or fahrenheit
    # Calling this function with no 'selection' returns the meter setting.
    def c_units(self, selection=None):
        code = self.echo('R08')  # Requests device settings, need to only change temperature
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
        self.echo('W'+code[1:4]+b.upper())
        flag = self.reset()
        if flag:
            print('Units successfully changed to °' + selection.upper() + '.')
    
    # Omega displays customize how many decimal places are displayed on
    # the faceplate, and how many are written to the serial line.
    # This command specifies and sets how many decimal points are displayed
    # by the instrument. Can be 0, up to 3.
    #
    # Note that for some probes, the decimal place is limited (e.g. must be
    # less than 2 decimal places).
    def set_decimal(self, n):
        if not(isinstance(n, int)):
            print('Select an integer between 0 and 3')
            return
        if n < 0 or n > 3:
            print('Invalid decimal place.')
            return
        code = self.echo('R08')
        b = int(code[4], 16)
        temp = 0
        if b > 7:
            temp = 8
        b = str(hex(n + 1 + temp))[-1]
        self.echo('W' + code[1:4] + b)
        flag = self.reset()
        if flag:
            print('Decimal point successfully changed to ' + str(n) + '.')
    
    # type = type of probe. Can be: ['TC', 'RTD', 'PROCESS']
    # Range type will depend on which type of probe is called
    # For TC's, range = ['J','K','T','E','N','DIN-J','R','S','B','C']
    # For RTDs, range = [100, 500, 1000]
    # For 'PROCESS' range = [100, 1, 10, 20]
    #
    # First byte (right-most of string)
    # 'type' lives in the first 2 bits (0 & 1)
    # TC settings live in bits 2 - 5
    # RTD settings lives in bits 6 - 7
    # PROCESS lives in 8 - 9
    # Ratio enable/disable is at 10
    # Low/High Resolution (0 or 1) is bit 11
    # peak/gross (0 or 1) is bit 12
    # Remaining bits are unused
    #
    # See section 5.7.1 "Input Type Format for Temperature/Process Instrument
    # on pg 22-23 of Communication Manual
    #
    # Note: SCASS-020 is a type-K TC
    def probe(self,
              typ = None,
              tc = None,
              rtd = None):
        
        # Check if changes are being called. This is used later to perform
        # a write to memory
        if all(x is None for x in [typ, tc, rtd]):
            flag = False
        else:
            flag = True
        
        # Definitions of possible inputs
        _indices = [0, 2, 6, 7]
        _types = ['TC', 'RTD']
        _tc_type = ['J',
                    'K',
                    'T',
                    'E',
                    'N',
                    'DIN-J',
                    'R',
                    'S',
                    'B',
                    'C']
        _rtd_type = ['100 ohm',
                     '500 ohm',
                     '1000 ohm']
        # If a user input the name without the index, this converts it to the index
        if isinstance(typ, str):
            typ = _types.index(typ.upper())
        if isinstance(tc, str):
            tc = _tc_type.index(tc.upper())
        
        # Grab the current memory state
        prb_val = int(self.echo('R07')[3:-1], 16)
        mem = extract(prb_val, _indices)
        
        # Assign grabbed values:
        if typ == None:
            typ = _types[mem[0]]
        else:
            mem[0] = typ
        if tc == None:
            tc = _tc_type[mem[1]]
        else:
            mem[1] = tc
        if rtd == None:
            rtd = _rtd_type[mem[2]]
        else:
            mem[2] = rtd
        if flag:
            new_val = compact(mem, _indices, 2)
            write = self.echo('W07' + new_val)
            if write[0:3] != 'W07':
                print(write)
                return typ, tc, rtd
            check = self.reset()
            if check != True:
                print('Probe parameters were not updated.')
                return typ, tc, rtd
            print('Successfully updated settings.')
            
        return typ, tc, rtd

# Takes the hex code from the omega system and extracts the
# individual components to return a list.
#
# Example:
# 0x11 memory address contains three 2-bit sets of data
# Each pertain to how colors are displayed
# Normal color starts at bit 0
# Alarm 1 color starts at bit 2
# Alarm 2 color starts at bit 4
# Normal_color = extract(36, 0, 1) -> 0
# Alarm1 = extract(36, 2, 3) -> 1
# Alarm2 = extract(36, 4, 5) -> 2
# decimal 36 = 0b 00 10 01 00
def extract(code, index):
    val = []
    for i in range(0, index.__len__()-1):
        start = index[i]
        stop = index[i+1]
        max_val = 2**stop
        if code < max_val:
            code = code + 2**(max_val+1)
        code_bin = bin(code)[::-1]
        out_bin = code_bin[start:stop]
        val.append(int(out_bin[::-1], 2))
    return val

# compact is effectively the inverse of extract.
# Converts values located at a binary index to hex characters.
def compact(code, index, length = None):
    c_len = code.__len__()
    i_len = index.__len__()
    if (c_len != i_len) and (c_len != (i_len-1)):
        print('Input values must match index length.')
        return
    val = 0
    for n, i in enumerate(code):
        val = val + i*(2**index[n])
    output = hex(val)[2:].upper()
    if length != None:
        if output.__len__() < length:
            while output.__len__() < length:
                output = '0' + output
    return output

if __name__ == '__main__':
    from serial_port import serial_ports
    import serial
    s = serial_ports()
    o = omegatc(s[0])
    val = o.probe(typ='TC',tc='K')