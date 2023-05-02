from __future__ import absolute_import
import serial
import time
import codecs
import src.thermal_controller.bit_converter as bc
# degree_sign = u'\N{DEGREE SIGN}'


class CNi:
    """
    Initialize with factory default settings.
    
    From Communication Manual:
    To Enable the iSeries Protocol, set Modbus
    menu item to “No” in the Bus Format Submenu
    of the Communication Menu. Refer to Section 5.7.11.
    """
    def __init__(self,
                 com,
                 baud=9600,
                 parity=serial.PARITY_ODD,
                 size=serial.SEVENBITS,
                 stops=serial.STOPBITS_ONE):

        # Initialize serial connection and get comm settings
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
        # Gives the controller up to 5 seconds to respond.
        while True:
            time.sleep(0.01)
            if self.serial.in_waiting == 9:
                self.connected = True
                break
            if abs(time.time() - t) > 5:
                if __name__ == '__main__':
                    print('Unable to connect with omega device.')
                self.connected = False
                return

        print('Connection to Omega TC successful!')
        self.init_offset()

        # Get controller settings
        check = self.serial.readall()
        self.__communication_protocol__ = check
        recognition = codecs.decode(check[0:2], 'hex')
        self.recognition = recognition
        self.port = com
        self.probe_type = self.probe()

        reading_config = self.reading_configuration()
        self.decimal = reading_config['decimal']
        self.units = '°' + reading_config['units']
        print('Omega controller is ready!')

    ########################################################################################
    # PID Functions
    ########################################################################################
    """
    Below are commands that correspond to functions that an integrated
    into the PID controller. See communication manual pg 14-15 for a 
    list of all commands.
    """
    # 0x01 & 0x02, called by position
    def set_point(self, temp=None, position=1, eeprom=False):
        # Input checks to make sure a valid command is being requested.
        if position > 2 or position < 1:
            print('Invalid set point target')
            return
        if temp is None:
            val = []
            if eeprom:
                cd = 'R'
            else:
                cd = 'G'
            for i in ['1', '2']:
                raw_msg = self.echo(f'{cd}0{i}')
                msg = self.msg2dec(raw_msg)
                temp = bc.hexstr2dec(msg)
                val.append(temp)
            return val
        if eeprom:
            msg = 'W'
        else:
            msg = 'P'
        msg = msg + '0' + str(position)

        '''
        Process the input value and convert it to the machine readable value.
        bits 0 - 19 = temperature value, 0 - 9999
        bits 20 - 22 = decimal place, 0 - 4 (note 4 = F.FFF)
        bit 23 = sign, 0 = positive, 1 = negative
        '''
        temp_hex = bc.dec2hexstr(temp)

        # Compile the message and send it
        msg = msg + temp_hex
        check = self.echo(msg)
        if check[0:3] == msg[0:3]:
            return f'Set point successfully changed to: {str(temp)}.'
        else:
            return check
    # 0x03 (not implemented)
    # 0x04 (not implemented)

    # 0x05
    def id(self, instrument_id=None):
        if instrument_id is not None:
            check = self.echo(f'W05{instrument_id}')
            return check
        else:
            check = self.echo('R05')
            return check[3:-1]

    # 0x07 (0x06 does not exist)
    def probe(self,
              probe_type=None,
              tc=None,
              rtd=None):
        _indices = [0, 2, 6, 7]
        _tc_type = ['J', 'K', 'T', 'E', 'N',
                    'DIN-J', 'R', 'S', 'B', 'C']
        _rtd_type = ['100 ohm',
                     '500 ohm',
                     '1000 ohm']
        _addr = '07'
        _dict = {'probe_type': probe_type,
                 'tc': tc,
                 'rtd': rtd}
        _valid = {'probe_type': [0, 1],
                  'tc': [0, 9],
                  'rtd': [0, 2]}
        _valid_names = {'probe_type': ['TC', 'RTD'],
                        'tc': _tc_type,
                        'rtd': _rtd_type}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x08
    def reading_configuration(self,
                              decimal=None,
                              units=None,
                              filter_constant=None):
        _indices = [0, 3, 5, 7]
        _addr = '08'
        _dict = {}
        _dict = {'decimal': decimal,
                 'units': units,
                 'filter_constant': filter_constant}
        _valid = {'decimal': [0, 2],
                  'units': [0, 2],
                  'filter_constant': [0, 2]}
        _valid_names = {'decimal': [1, 2, 3, 4],
                        'units': ['F', 'C'],
                        'filter_constant': [2**x for x in range(8)]}

        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x09
    def alarm_1_configuration(self,
                              retransmission=None,
                              alarm_type=None,
                              latch=None,
                              normal=None,
                              active=None,
                              loop=None,
                              power=None):
        _indices = [0, 1, 2, 3, 4, 6, 7, 8]
        _addr = '09'
        _dict = {'retransmission': retransmission,
                 'alarm_type': alarm_type,
                 'latch': latch,
                 'normal': normal,
                 'active': active,
                 'loop': loop,
                 'power': power}
        _valid = {'retransmission': [0, 1],
                  'alarm_type': [0, 1],
                  'latch': [0, 1],
                  'normal': [0, 1],
                  'active': [0, 3],
                  'loop': [0, 1],
                  'power': [0, 1]}
        _valid_names = {'retransmission': ['Enable', 'Disable'],
                        'alarm_type': ['Absolute', 'Deviation'],
                        'latch': ['Unlatch', 'Latch'],
                        'normal': ['Normally Open', 'Normally Closed'],
                        'active': ['Above', 'Below', 'Hi/Lo', 'Active Band'],
                        'loop': ['Disable', 'Enable'],
                        'power': ['Disable at Power On', 'Enable at Power On']}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x0A
    def alarm_2_configuration(self,
                              enable=None,
                              alarm_type=None,
                              latch=None,
                              normal=None,
                              active=None,
                              retransmission=None):
        _indices = [0, 1, 2, 3, 4, 7, 8]
        _addr = '0A'
        _dict = {'enable': enable,
                 'alarm_type': alarm_type,
                 'latch': latch,
                 'normal': normal,
                 'active': active,
                 'retransmission': retransmission}
        _valid = {'enable': [0, 1],
                  'alarm_type': [0, 1],
                  'latch': [0, 1],
                  'normal': [0, 1],
                  'active': [0, 3],
                  'retransmission': [0, 1]}
        _valid_names = {'enable': ['Enable', 'Disable'],
                        'alarm_type': ['Absolute', 'Deviation'],
                        'latch': ['Unlatch', 'Latch'],
                        'normal': ['Normally Open', 'Normally Closed'],
                        'active': ['Above', 'Below', 'Hi/Lo', 'Active Band'],
                        'retransmission': ['Disable', 'Enable']}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x0B
    # def loop_break_time(self, break_time=None):

    # 0x0C
    def output_1_configuration(self,
                               pid=None,
                               direction=None,
                               auto_pid=None,
                               anti_wind=None,
                               auto_tune=None,
                               analog=None):
        _indices = [0, 1, 2, 4, 5, 6, 7]
        _addr = '0C'
        _dict = {'pid': pid,
                 'direction': direction,
                 'auto_pid': auto_pid,
                 'anti_wind': anti_wind,
                 'auto_tune': auto_tune,
                 'analog': analog}
        _valid = {'pid': [0, 1],
                  'direction': [0, 1],
                  'auto_pid': [0, 1],
                  'anti_wind': [0, 1],
                  'auto_tune': [0, 1],
                  'analog': [0, 1]}
        _valid_names = {'pid': ['Time Proportional On/Off', 'Time Proportional PID'],
                        'direction': ['Reverse', 'Direct'],
                        'auto_pid': ['Disable', 'Enable'],
                        'anti_wind': ['Disable', 'Enable'],
                        'auto_tune': ['Stop', 'Start'],
                        'analog': ['0 - 20 mA', '4 - 20 mA']}
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x0D
    def output_2_configuration(self,
                               pid=None,
                               direction=None,
                               auto_pid=None,
                               ramp=None,
                               soak=None,
                               damping=None):
        _indices = [0, 1, 2, 3, 4, 5, 7]
        _addr = '0D'
        _dict = {'pid': pid,
                 'direction': direction,
                 'auto_pid': auto_pid,
                 'ramp': ramp,
                 'soak': soak,
                 'damping': damping}
        _valid = {'pid': [0, 1],
                  'direction': [0, 1],
                  'auto_pid': [0, 1],
                  'ramp': [0, 1],
                  'soak': [0, 1],
                  'damping': [0, 7]}
        _valid_names = {'pid': ['Time Proportional On/Off', 'Time Proportional PID'],
                        'direction': ['Reverse', 'Direct'],
                        'auto_pid': ['Disable', 'Enable'],
                        'ramp': ['Disable', 'Enable'],
                        'soak': ['Disable', 'Enable'],
                        'damping': ['Damping ' + str(x) for x in range(0, 8)]}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x10
    def communication_parameters(self,
                                 baud=None,
                                 parity=None,
                                 bit=None,
                                 stop=None):
        _indices = [0, 3, 5, 6, 7]
        _addr = '10'
        _dict = {'baud': baud,
                 'parity': parity,
                 'bit': bit,
                 'stop': stop}
        _valid = {'baud': [0, 6],
                  'parity': [0, 2],
                  'bit': [0, 1],
                  'stop': [0, 1]}
        _valid_names = {'baud': ['300', '600', '1200', '2400',
                                 '4800', '9600', '19200'],
                        'parity': ['No Parity', 'Odd', 'Even'],
                        'bit': ['7 bit', '8 bit'],
                        'stop': ['1 Stop Bit', '2 Stop Bit']}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x11
    def color(self,
              normal=None,
              alarm1=None,
              alarm2=None):
        _indices = [0, 2, 4, 6]
        _addr = '11'
        _dict = {'normal': normal,
                 'alarm1': alarm1,
                 'alarm2': alarm2}
        _valid = {'normal': [0, 2],
                  'alarm1': [0, 2],
                  'alarm2': [0, 2]}
        colors = ['Amber', 'Green', 'Red']
        _valid_names = {'normal': colors,
                        'alarm1': colors,
                        'alarm2': colors}

        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    # 0x1F
    def bus_format(self,
                   modbus=None,
                   feed=None,
                   echo=None,
                   rs=None,
                   bus_format=None,
                   terminator=None):
        _indices = [0, 1, 2, 3, 4, 5, 6]
        _addr = '1F'
        _dict = {'modbus': modbus,
                 'feed': feed,
                 'echo': echo,
                 'rs': rs,
                 'bus_format': bus_format,
                 'terminator': terminator}
        _valid = {'modbus': [0, 1],
                  'feed': [0, 1],
                  'echo': [0, 1],
                  'rs': [0, 1],
                  'bus_format': [0, 1],
                  'terminator': [0, 1]}
        _valid_names = {'modbus': ['No Modbus', 'Modbus'],
                        'feed': ['No Line Feed', 'Line Feed'],
                        'echo': ['No ECHO', 'ECHO'],
                        'rs': ['RS-232', 'RS-485'],
                        'bus_format': ['Continuous', 'Command'],
                        'terminator': ['Space', 'Carriage Return']}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings

    """
    Below are all the "one-shot" commands where no data is sent to the PID.
    These are written in order from D01 to Z02. The function names are made
    to match what is written in the manual, except  
    See page 15 of communication manual.
    """
    def disable_alarm1(self):
        return self.echo('D01')

    def disable_alarm2(self):
        return self.echo('D02')

    def disable_standby(self):
        return self.echo('D03')

    def disable_self(self):
        return self.echo('D04')

    def enable_alarm1(self):
        return self.echo('E01')

    def enable_alarm2(self):
        return self.echo('E02')

    def enable_standby(self):
        return self.echo('E03')

    def enable_self(self):
        return self.echo('E04')

    def measure(self):
        temp = self.echo('X01')
        start = temp.rfind('X01') + 3
        stop = temp.rfind('\r')
        if stop != -1:
            return float(temp[start:stop])
        else:
            return False

    def send_alarm_status(self):
        return self.echo('U01')

    def send_sw_version(self):
        return self.echo('U03')

    def send_data_string(self):
        return self.echo('V01')

    def reading(self, option=1):
        if isinstance(option, str):
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

    def reset(self):
        check = self.echo('Z02')
        if check[0:3] == 'Z02':
            flag = True
        else:
            flag = False
        self.init_offset()
        return flag

    ########################################################################################
    # Communication Code
    ########################################################################################
    """
    Below are the functions used to generalize communication. These do all of the 
    interpretation of byte-code from or for the PID controller and handle getting
    data to and from the serial line.
    """
    def value_process(self, _addr, value=None, eeprom=False):
        """
        Value Process is the general code for reading/writing a value value that follows
        the hex format used on omega controllers. i.e. bit 23 = sign, bits 20-22 = exponent
        and bits 0 - 19 = data.
        """
        if value is None:
            if eeprom:
                cmd = 'R'
            else:
                cmd = 'G'
            msg = cmd + _addr
            code = self.msg2dec(self.echo(msg))
            val = bc.hexstr2dec(code)
            return val
        else:
            if eeprom:
                cmd = 'W'
            else:
                cmd = 'P'
            data = bc.dec2hexstr(value)
            msg = cmd + _addr + data
            check = self.echo(msg)
            return check

    def memory_process(self, _addr, _indices, _dict, _valid, _valid_names):
        """
        memory_process() generalizes the serial communication when multiple settings
        are stored in a single address location on the PID. This function accepts either
        an empty call (i.e., _dict contains None entries) and will return the machine
        settings. If _dict contains non-None entries, it will overwrite what is saved
        on the PID. The values called in _dict can be either the human readable words
        (e.g., 'Amber'), or a numerical value that indicates the position. Only non-None
        values will be overwritten.

        _addr = the index location
        _indices = list of start and stop positions of each byte code. Must be one longer
                   than the number of settings. Example: color has 3 settings stored in 2
                   bytes. There are 4 elements in this list.
        _dict = dictionary with user request (see above)
        _valid = dictionary that contains the range of numeric inputs that are acceptable.
        _valid_names = dictionary that contains human readable text. Is used to convert
                       _dict input to a number for being interpreted by the PID.
        """
        for i in _dict:
            if _dict[i] is not None:
                if isinstance(_dict[i], str):
                    try:
                        _dict[i] = _valid_names[i].index(_dict[i])
                    except KeyError:
                        raise KeyError('Invalid input for', i,
                                       '. Please input something from the following:',
                                       _valid_names[i],
                                       'Or select a number in the range of',
                                       _valid[i], '.')
                elif isinstance(_dict[i], (int, float)):
                    if (_dict[i] < _valid[i][0]) or (_dict[i] > _valid[i][1]):
                        raise ValueError(f'The number {_dict[i]} is not valid '
                                         f'for the {i} setting. '
                                         f'Please select a number between '
                                         f'{_valid[i][0]} and {_valid[i][1]}.')
                else:
                    raise TypeError('Input must be a string or int.')

        msg = self.msg2dec(self.echo('R'+_addr))

        """
        Check for a request from the user to change parameters
        A flag is set as _dict may be changed depending on what is read
        from the controller.
        """
        if all(_dict[x] is None for x in _dict):
            flag = False
        else:
            flag = True
        mem = bc.extract(msg, _indices)

        """
        The next step compares the current values with any values requested.
        If the user doesn't call to change a value, _dict is overwritten by
        what is stored on the controller.
        """
        for n, i in enumerate(_dict):
            if _dict[i] is not None:
                mem[n] = _dict[i]
        settings = _dict   
        if flag:
            new_val = bc.compact(mem, _indices, 2)
            write = self.echo('W' + _addr + new_val)
            # check for errors
            if write[0:3] != 'W'+_addr:
                print(write)
                return _dict
            check = self.reset()
            if not check:
                print('Failed to update controller.')
                return
            print('Successfully updated controller.')
        else:
            for n, i in enumerate(_dict):
                settings[i] = _valid_names[i][mem[n]]
                print(i, ': ', _valid_names[i][mem[n]])
        if flag:
            return
        else:
            return settings

    def write(self, message):
        """
        Performs a serial write on the RS232 line.
        Some functionality is added to mainstream sending messages.
        Strings are automatically converted to byte arrays.
        Recognition character and return lines are automatically added.
        """
        # Check input type and convert it to byte string
        if isinstance(message, str):
            msg = message.encode('utf-8')
        elif isinstance(message, bytes):
            msg = message
        elif isinstance(message, float) or isinstance(message, int):
            msg = str(message)
            msg = msg.encode('utf-8')
        else:
            raise ValueError('Incorrect message type.')

        # Check if a return line is present.
        if msg[-1] != b'\r':
            msg = msg + b'\r'

        # Check if the recognition character is present.
        if msg[0] != self.recognition:
            if msg[0] != b'^':  # Ignore if the instrument settings are called.
                msg = self.recognition + msg

        self.serial.write(msg)

    def read(self):
        """
        Read from the serial line and return the message.
        Errors from the PID do not cause programs to error.
        """
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

    def echo(self, message):
        """
        echo('message') clears the serial port, sends a message and
        waits for a response from the PID.
        """
        self.serial.flush()
        self.write(message)
        time.sleep(self.serial.timeout)
        msg = self.read()
        return msg

    ########################################################################################
    # General Code
    ########################################################################################
    """
    Below are a collection of some custom functions added as quality of life
    improvement for operating a PID controller.
    """
    def init_offset(self):
        """
        Omega thermal controllers do not initialize with the offset
        that is saved to the eeprom. This simply grabs it and pushes it
        to memory.
        """
        msg = self.echo('R03')
        self.echo(f'P03{msg}')

    def offset(self,
               offset=None,
               eeprom=False,
               target=None):
        """
        offset() is used for calibrating the reading on the PID. It will take either
        a target, or an offset value.

        offset = a define offset that is added to the raw reading
        target = compares the current measurement and finds the offset that would
                 result in reading the target value.
        """
        if target is not None and offset is not None:
            print('You cannot select an offset and target value. Pick one or the other.')
            return
        _addr = '03'
        # Compile the message and send it
        if target is None:
            check = self.value_process(_addr, offset, eeprom)
        else:
            current_val = self.measure()
            offset = target - current_val
            check = self.value_process(_addr, offset, eeprom=eeprom)
        if offset is None and target is None:
            return check
        else:
            if check[1:3] == _addr:
                print(f'Offset updated to {offset}')

    def default_values(self, write=False):
        """
        default_values is a fail-safe that can reset a PID controller
        to the factory default settings (according to the com. manual).

        An empty argument e.g., pid.default_values() will return each
        setting that is stored on the PID controller.
        """
        default_values = {'01': '200000',  # Set Point 1
                          '02': '200000',  # Set Point 2
                          '03': '200000',  # Reading Offset
                          '04': '400000',  # ANLOFF
                          '05': '0000',    # ID
                          '07': '04',      # Input Type
                          '08': '4A',      # Reading Configuration
                          '09': '00',      # Alarm 1 Configuration
                          '0A': '00',      # Alarm 2 Configuration
                          '0B': '003B',    # Loop Break Time
                          '0C': '00',      # Output 1 Configuration
                          '0D': '60',      # Output 2 Configuration
                          '0E': '0000',    # Ramp Time
                          '0F': '9186A0',  # Bus Format
                          '10': '0D',      # Communication Parameters
                          '11': '09',      # Color Display
                          '12': 'A003E8',  # Alarm 1 Low
                          '13': '200FA0',  # Reading Scale Offset
                          '14': '100001',  # Reading Scale
                          '15': 'A003E8',  # Alarm 2 Lo
                          '16': '200FA0',  # Alarm 2 Hi
                          '17': '00C8',    # PB1/Dead Band
                          '18': '00B4',    # Reset 1
                          '19': '0000',    # Rate 1
                          '1A': '07',      # Cycle 1
                          '1C': '00C8',    # PB2/Dead Band
                          '1D': '07',      # Cycle 2
                          '1E': '0000',    # Soak Time
                          '1F': '14',      # Bus Format
                          '20': '02',      # Data Format
                          '21': '01',      # Address
                          '22': '0010',    # Transit Time Interval
                          '24': '00',      # Miscellaneous
                          '25': '200000',  # C.J. Offset Adjust
                          '26': '2A',      # Recognition Character
                          '27': '00',      # % Low
                          '28': '63',      # % Hi
                          '29': '00'}      # Linearization Point
        if write:
            for i in default_values:
                print(f'Writing {default_values[i]} to address {i}.')
                self.echo(f'W{i}{default_values[i]}')
        else:
            for i in default_values:
                print(self.echo(f'R{i}'))

    def msg2dec(self, msg):
        return int(msg[3:-1], 16)

    def c2f(self, val):
        return val * 1.8 + 32

    def f2c(self, val):
        return (val - 32) / 1.8


if __name__ == "__main__":
    o = CNi('com3')
""""
Below is the general code for memory calls.
Inputs are None by default, which indicate no changes to be made.
If the function is called without any inputs it will simply return
the current settings on the controller. Return settings, which is _dict
but with filled out values. Otherwise, new settings will be written to the
controller.
def config_setting(self,
                   a=None,
                   b=None,
                   c=None,
                   d=None):
        _indices = [0, 1, 2, 3, 7]
        _addr = 'XX'
        _dict = {'a': a,
                 'b': b,
                 'c': c,
                 'd': d}
        _valid = {'a': [0, 1],
                  'b': [0, 1],
                  'c': [0, 1],
                  'd': [0, 7]}
        _valid_names = {'a': ['on', 'off'],
                        'b': ['on', 'off'],
                        'c': ['Disable', 'Enable'],
                        'd': ['Setting ' + str(x) for x in range(0, 8)]}
                
        settings = self.memory_process(_addr, _indices, _dict, _valid, _valid_names)
        return settings
"""
