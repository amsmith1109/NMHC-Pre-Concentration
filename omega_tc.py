# Commands not implemented:
# Setting/tuning offsets in 03
# 04, 05, 09 & beyond
# Alarms D01 - E04, X02 - V01
import serial
import time
import codecs

degree_sign = u'\N{DEGREE SIGN}'

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
                return
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
        
        # init_offset is called any time the instrument is reset
        # offset values stored in eeprom, but not passed to memory.
        # .init_offset() grabs what's stored in the eeprom and pushes
        # it to memory to obtain the correct reading.
        # Note: the same may be necessary for scale offsets.
        # Note 2: Be sure to change the offset calibration with new probes.
        self.init_offset()
        self.port = com
        # Read values at 0x07 register
        self.probe_type = self.probe()
        
        # Read values at 0x08 register
        idx = [0,3,5,8]
        msg = msg2dec(self.echo('R08'))
        R08 = extract(msg, idx)
        self.decimal = R08[0] - 1 # note: 0 = "not allowed", '1' = 0 ...
        if R08 == 0:
            self.units = '°C'
        else:
            self.units = '°F'
        self.filter_constant = 2**R08[2]
        print('Omega controller is ready!')

    def reading(self, option=1):
        if isinstance(option,str):
            if option.upper() == 'PEAK':
                option = 2
            elif option.upper() == 'VALLEY':
                option = 3
            else:
                print('Invalid reading option.')
                return
        if option > 3 or option < 0:
            print('Invalid reading option. (out of range)')
            return
        cmd = 'X0' + str(option)
        msg = self.echo(cmd)[3:-1]
        return float(msg)
    
    def set_point(self, temp = None, position = 1, eeprom=False):
        # Input checks to make sure a valid command is being requested.
        idx = [0,20,23,24]
        if position > 2 or position < 1:
            print('Invalid set point target')
            return
        if temp == None:
            val = []
            if eeprom == True:
                cd = 'R'
            else:
                cd = 'G'
            for i in ['1','2']:
                msg = msg2dec(self.echo(f'{cd}0{i}'))
                bits = extract(msg, idx)
                temp = bits[0] / (10**(bits[1]-1)) * ((-1)**bits[2])
                val.append(temp)
            return val
            
        if eeprom==True:
            msg = 'W'
        else:
            msg = 'P'
        if temp > 9999 or temp < -9999:
            print('Temperature setting is out of range.')
            return
        msg = msg + '0' + str(position)
        
        # Process the input value and convert it to the machine readable value.
        # bits 0 - 19 = temperature value, 0 - 9999
        # bits 20 - 22 = decimal place, 0 - 4 (note 4 = F.FFF)
        # bit 23 = sign, 0 = positive, 1 = negative
        
        val = []
        temp_string = str(abs(temp))
        if '.' in temp_string[0:5]:
            temp_string = temp_string[0:5]
            dec = temp_string[::-1].find('.')
        else:
            temp_string = temp_string[0:4]
            dec = 0
        temp_val = int(round(abs(temp)*10**dec))
        val.append(temp_val)
        val.append(dec + 1)
        if temp > 0:
            val.append(0)
        else:
            val.append(1)
        temp_hex = compact(val,idx,6)
        
        # Compile the message and send it
        msg = msg + temp_hex
        check = self.echo(msg)
        if check[0:3] == msg[0:3]:
            return 'Set point successfully changed to: ' + str(temp) + '.'
        else:
            return check
    
    
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
        self.serial.flush()
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
        self.init_offset()
        return flag

    def measure(self):
        temp = self.echo('X01')
        start = temp.rfind('X01') + 3
        stop = temp.rfind('\r')
        if stop!=-1:
            return float(temp[start:stop])
        else:
            return

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
            print(f'Units successfully changed to °{selection.upper()}.')
    
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
            print(f'Decimal point successfully changed to {n}.')
    
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
              Type = None,
              tc = None,
              rtd = None):
        
        _indices = [0, 2, 6, 7]
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
        _addr = '07'
        _dict = {'Type':Type,
                 'tc':tc,
                 'rtd':rtd}
        _valid = {'Type':[0,1],
                 'tc':[0,9],
                 'rtd':[0,2]}
        _valid_names = {'Type':['TC','RTD'],
                 'tc':_tc_type,
                 'rtd':_rtd_type}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
    
    # Omega thermal controllers do not initialize with the offset
    # that is saved to the eeprom. This simply grabs it and pushes it
    # to memory.
    def init_offset(self):
        msg = self.echo('R03')
        self.echo('P' + msg[1:-1])
    
    def color(self,
                normal=None,
                alarm1=None,
                alarm2=None):
            _indices = [0, 2, 4, 6]
            _addr = '11'
            _dict = {'normal':normal,
                     'alarm1':alarm1,
                     'alarm2':alarm2}
            _valid = {'normal':[0,2],
                     'alarm1':[0,2],
                     'alarm2':[0,2]}
            _valid_names = {'normal':['Amber','Green','Red'],
                         'alarm1':['Amber','Green','Red'],
                         'alarm2':['Amber','Green','Red']}
                    
            settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
            return settings
    
    def alarm_1_configuration(self,
                            retransmission=None,
                            Type=None,
                            latch=None,
                            normal=None,
                            active=None,
                            loop=None,
                            power=None):
        _indices = [0,1,2,3,4,6,7,8]
        _addr = '09'
        _dict = {'retransmission':retransmission,
                 'Type':Type,
                 'latch':latch,
                 'normal':normal,
                 'active':active,
                 'loop':loop,
                 'power':power}
        _valid = {'retransmission':[0,1],
                 'Type':[0,1],
                 'latch':[0,1],
                 'normal':[0,1],
                 'active':[0,3],
                 'loop':[0,1],
                  'power':[0,1]}
        _valid_names = {'retransmission':['Enable','Disable'],
                     'Type':['Absolute', 'Deviation'],
                     'latch':['Unlatch','Latch'],
                     'normal':['Normally Open','Normally Closed'],
                     'active':['Above','Below', 'Hi/Lo','Active Band'],
                     'loop':['Disable','Enable'],
                     'power':['Disable at Power On', 'Enable at Power On']}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
    
    def alarm_2_configuration(self,
                            enable=None,
                            Type=None,
                            latch=None,
                            normal=None,
                            active=None,
                            retransmission=None):
        _indices = [0,1,2,3,4,7,8]
        _addr = '09'
        _dict = {'enable':enable,
                 'Type':Type,
                 'latch':latch,
                 'normal':normal,
                 'active':active,
                 'retransmission':retransmission}
        _valid = {'enable':[0,1],
                 'Type':[0,1],
                 'latch':[0,1],
                 'normal':[0,1],
                 'active':[0,3],
                 'retransmission':[0,1]}
        _valid_names = {'enable':['Enable','Disable'],
                     'Type':['Absolute', 'Deviation'],
                     'latch':['Unlatch','Latch'],
                     'normal':['Normally Open','Normally Closed'],
                     'active':['Above','Below', 'Hi/Lo','Active Band'],
                     'retransmission':['Disable','Enable']}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
    
    def config_output_1(self,
                       PID=None,
                       direction=None,
                       auto_PID=None,
                       anti_wind=None,
                       auto_tune=None,
                       analog=None):
        _indices = [0, 1, 2, 4, 5, 6, 7]
        _addr = '0C'
        _dict = {'PID':PID,
                 'direction':direction,
                 'auto_PID':auto_PID,
                 'anti_wind':anti_wind,
                 'auto_tune':auto_tune,
                 'analog':analog}
        _valid = {'PID':[0,1],
                 'direction':[0,1],
                 'auto_PID':[0,1],
                 'anti_wind':[0,1],
                 'auto_tune':[0,1],
                 'analog':[0,1]}
        _valid_names = {'PID':['Time Proportional On/Off','Time Proportional PID'],
                     'direction':['Reverse', 'Direct'],
                     'auto_PID':['Disable','Enable'],
                     'anti_wind':['Disable','Enable'],
                     'auto_tune':['Stop','Start'],
                     'analog':['0 - 20 mA', '4 - 20 mA']}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
    
    def config_output_2(self,
                       PID=None,
                       direction=None,
                       auto_PID=None,
                       ramp=None,
                       soak=None,
                       damping=None):
        _indices = [0, 1, 2, 3, 4, 5, 7]
        _addr = '0D'
        _dict = {'PID':PID,
                 'direction':direction,
                 'auto_PID':auto_PID,
                 'ramp':ramp,
                 'soak':soak,
                 'damping':damping}
        _valid = {'PID':[0,1],
                 'direction':[0,1],
                 'auto_PID':[0,1],
                 'ramp':[0,1],
                 'soak':[0,1],
                 'damping':[0,7]}
        _valid_names = {'PID':['Time Proportional On/Off','Time Proportional PID'],
                     'direction':['Reverse', 'Direct'],
                     'auto_PID':['Disable','Enable'],
                     'ramp':['Disable','Enable'],
                     'soak':['Disable','Enable'],
                     'damping':['Damping '+str(x) for x in range(0,8)]}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
    
    # Note that changing communication parameters will require changing
    # how this object interacts with the controller.
    def communication_paramters(self,
                    baud=None,
                    parity=None,
                    bit=None,
                    stop=None):
        _indices = [0, 3, 5, 6, 7]
        _addr = '10'
        _dict = {'baud':baud,
                 'parity':parity,
                 'bit':bit,
                 'stop':stop}
        _valid = {'baud':[0,6],
                 'parity':[0,2],
                 'bit':[0,1],
                 'stop':[0,1]}
        _valid_names = {'baud':['300','600','1200','2400','4800','9600','19200'],
                     'parity':['No Parity', 'Odd', 'Even'],
                     'bit':['7 bit','8 bit'],
                     'stop':['1 Stop Bit','2 Stop Bit']}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
    
    def bus_format(self,
                    modbus=None,
                    feed=None,
                    echo=None,
                    rs=None,
                    Type=None,
                    terminator=None):
        _indices = [0, 1, 2, 3, 4, 5, 6]
        _addr = '1F'
        _dict = {'modbus':modbus,
                 'feed':feed,
                 'echo':echo,
                 'rs':rs,
                 'Type':Type,
                 'terminator':terminator}
        _valid = {'modbus':[0,1],
                 'feed':[0,1],
                 'echo':[0,1],
                 'rs':[0,1],
                  'Type':[0,1],
                  'terminator':[0,1]}
        _valid_names = {'modbus':['No Modbus','Modbus'],
                     'feed':['No Line Feed', 'Line Feed'],
                     'echo':['No ECHO','ECHO'],
                     'rs':['RS-232','RS-485'],
                     'Type':['Continuous','Command'],
                     'terminator':['Space','Carriage Return']}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    
    def memory_process(self, _addr, _indices, _dict, _valid, _valid_names):
        flag = False
        for i in _dict:
            if _dict[i]!=None:
                if isinstance(_dict[i],str):
                    try:
                        _dict[i] = _valid_names[i].index(_dict[i])
                    except:
                        print('Invalid input for',i,
                              '. Please input something from the following:',
                              _valid_names[i],
                             'Or select a number in the range of',
                              _valid[i],'.')
                        print()
                        flag = True
                else:
                    if not(_valid[i][0] <= _dict[i] <= _valid[i][1]):
                        print('Invalid input range. ',i,
                              ' must be between ',
                              _valid[i][0], ' and ',
                              _valid[1],'.')
                        print()
                        flag = True
        if flag:
            return
        msg = msg2dec(self.echo('R'+_addr))
        
        # Check for a request from the user to change parameters
        # A flag is set as _dict may be changed depending on what is read
        # from the controller.
        if all(_dict[x] is None for x in _dict):
            flag = False
        else:
            flag = True
        
        # mem is the extracted values that correspond to the memory location
        # supplied by the controller at address _addr
        mem = extract(msg, _indices)
        
        # The next step compares the current values with any values requested.
        # If the user doesn't call to change a value, _dict is overwritten by
        # what is stored on the controller.
        for n, i in enumerate(_dict):
            if _dict[i]!=None:
                mem[n] = _dict[i]
        settings = _dict   
        if flag:
            new_val = compact(mem, _indices, 2)
            write = self.echo('W' + _addr + new_val)
            if write[0:3] != 'W'+_addr: #check for errors
                print(write)
                return _dict
            write = self.echo(f'R{_addr}')
            #print(write)
            check = self.reset()
            if check != True:
                print('Failed to update controller.')
                return
            print('Successfully updated controller.')
        else:
            for n, i in enumerate(_dict):
                settings[i] = _valid_names[i][mem[n]]
                print(i,': ',_valid_names[i][mem[n]])
        if flag:
            return
        else:
            return settings

    def defaults_value(self,read_write=False):       
        default_values = {'01':'200000',
                         '02':'200000',
                         '03':'200000',
                         '04':'400000',
                         '05':'0000',
                         '07':'04',
                         '08':'4A',
                         '09':'00',
                         '0A':'00',
                         '0B':'003B',
                         '0C':'00',
                         '0D':'60',
                         '0E':'0000',
                         '0F':'9186A0',
                         '10':'0D',
                         '11':'09',
                         '12':'A003E8',
                         '13':'200FA0',
                         '14':'100001',
                         '15':'A003E8',
                         '16':'200FA0',
                         '17':'00C8',
                         '18':'00B4',
                         '19':'0000',
                         '1A':'07',
                         '1C':'00C8',
                         '1D':'07',
                         '1E':'0000',
                         '1F':'14',
                         '20':'02',
                         '21':'01',
                         '22':'0010',
                         '24':'00',
                         '25':'200000',
                         '26':'2A',
                         '27':'00',
                         '28':'63',
                         '29':'00'}
        if read_write:
            for i in default_values:
                self.echo(f'W{i}{default_values[i]}')
        else:
            for i in default_values:
                print(self.echo(f'R{i}'))
            
            
# extract() takes the hex code from the omega system and extracts the
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
    # Max val is used to ensure that the conversion to the binary value is the correct length.
    # For an 8-bit number, 0x04 is printed as 0b100, but should be '0b00000100'. A large enough
    # number is added to make 0x04 print as '0b100000100'. This reverses to '001000001b0'. The
    # Reading the 1st to 8rd bit is then obtains from out_bin[0] to out_bin[7].
    max_val = 2**(index[-1]+2)
    if code < max_val:
        code = code + max_val
    code_bin = bin(code)[::-1]
    for i in range(0, index.__len__()-1):
        start = index[i]
        stop = index[i+1]
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

def msg2dec(msg):
    return int(msg[3:-1], 16)

def dec2hexstr(msg):
    output = 0
    return output

if __name__ == '__main__':
    from serial_port import serial_ports
    import serial
    s = serial_ports()
    o = omegatc(s[0])
# Below is the general code for memory calls.
# Inputs are None by default, which indicate no changes to be made.
# If the function is called without any inputs it will simply return
# the current settings on the controller. Return settings, which is _dict
# but with filled out values. Otherwise, new settings will be written to the
# controller.
# def config_setting(self,
#                     a=None,
#                     b=None,
#                     c=None,
#                     d=None):
#         _indices = [0, 1, 2, 3, 7]
#         _addr = 'XX'
#         _dict = {'a':a,
#                  'b':b,
#                  'c':c,
#                  'd':d}
#         _valid = {'a':[0,1],
#                  'b':[0,1],
#                  'c':[0,1],
#                  'd':[0,7]}
#         _valid_names = {'a':['on','off'],
#                      'b':['on', 'off'],
#                      'c':['Disable','Enable'],
#                      'd':['Setting '+str(x) for x in range(0,8)]}
#                 
#         settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
#         return settings