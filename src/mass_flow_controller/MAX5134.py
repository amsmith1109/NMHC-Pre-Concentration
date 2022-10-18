import ustruct
import time

_CLR            =   b'\x02\xff\xff'
_LDAC           =   0x01
_POWER_CONTROL  =   0x03
_LINEARITY      =   b'\x05\x02\x00'
_WRITE          =   0x10
_WRITE_THROUGH  =   0x30
_DEVICES        =   [5134, 5135, 5136, 5137]
_CHANNELS       =   [4, 4, 2, 2]
_RESOLUTION     =   [16, 12, 16, 12]

# Datasheet available at https://datasheets.maximintegrated.com/en/ds/MAX5134-MAX5137.pdf
# Declare which device is connected to get the proper functionality.
class MAX513X:
    def __init__(self, CS, SPI, maximum=None, mz=False, device=5136):
        if maximum is None:
            maximum = 5 #Assumes a default of 5 V max
        self.cs = CS
        self.spi = SPI
        self.max = maximum
        self.power = 1
        idx = _DEVICES.index(device)
        channels = _CHANNELS[idx]
        # self.setpoint saves the current output setting of the DAC
        # The startup behavior of the MAX5134 depends on how the M/Z
        # pin has been wired. 0 = ground, 1 = 5 V.
        # Setting a logic high defaults the output to the halfway point.
        self.resolution = self.max / (2 ** _RESOLUTION[idx])
        self.setpoint = []
        self.register = []
        for i in range(0, channels):
            self.setpoint.append(mz * self.max * 0.5)
            self.register.append(0)

    # Uses the write-through command on the MAX5134 to immediately
    # output the desired voltage to the specified channels.
    def write(self, channel, voltage):
        channel_word = self.channel_word(channel)
        select = _WRITE_THROUGH + channel_word
        val, voltage = self.v2b(voltage)
        stream = ustruct.pack('>BH', select, val)
        self.push(stream)
        self.update_setpoint(channel, voltage)

    def load(self, channel, voltage):
        channel_word = self.channel_word(channel)
        select = _WRITE + channel_word
        val, voltage = self.v2b(voltage)
        stream = ustruct.pack('>BH', select, val)
        self.push(stream)
        if isinstance(channel, list):
            for i in channel:
                self.register[i] = voltage
        else:
            self.register[channel] = voltage

    # Command built in the MAX5134 to clear all registers
    def clear(self):
        print('Clearing DAC registers.')
        self.push(_CLR)
        self.setpoint = [0, 0, 0, 0] #unsure of how this interacts with M/Z settings
        self.register = [0, 0, 0, 0]

    # Performs the integrated linearity calibration on the DAC
    def linearity(self):
        self.push(_LINEARITY)

    # Moves the values stored in the channel register to the output
    # of the MAX5134. Inputs must be loaded using the load function
    # prior to using load.
    #
    # This feature is commonly used when multiple channels or multiple
    # MAX5134 need to have their output changed simultaneously
    def ldac(self, channel):
        channel_word = self.channel_word(channel)
        stream = ustruct.pack('>BBB', _LDAC, channel_word, 0xff)
        self.push(stream)
        self.update_setpoint(channel, self.register)

    # Turns off the dac via software
    def pwr(self, channel):
        channel_word = self.channel_word(channel)
        if self.power == 1:
            set = 0xef
            self.power = 0
            print('Powering Off.')
        stream = ustruct.pack('>BBB', _POWER_CONTROL, channel_word, set)
        self.push(stream)

    # push simply sends stream via SPI to the MAX5134
    def push(self, stream):
        try:
            self.cs(0)
            time.sleep_ms(1)
            self.spi.write(stream)
        finally:
            self.cs(1)

    # Generates the binary command sent over spi to specify which
    # channels are targetted by the command.
    def channel_word(self, channel):
        if isinstance(channel, list):
            word = 0
            for i in channel:
                word += 2**i
        if isinstance(channel, int):
            word = 2**channel
        return word

    # v2b is used to convert a voltage value to the corresponding
    # binary value on the DAC. This makes it easier for the user to
    # instead specify the voltage they want and let the module do
    # the conversion.
    #
    # Warnings are issued if the selected voltage is out of range.
    def v2b(self, voltage):
        if voltage >= self.max: #Handles rollover
            val = 2**16-1
            voltage = self.max
            print('Input set to max.')
        elif voltage < 0: #Handles rollover (again)
            val = 0
            voltage = 0
            print('Input is negative. Setting to zero.')
        else:
            val = int(round(voltage * 2 ** 16 / self.max))
        return val, voltage
    
    def update_setpoint(self, channel, voltage):
        if isinstance(channel, list):
            for i in channel:
                if isinstance(voltage, list):
                    self.setpoint[i] = voltage[i]
                else:
                    self.setpoint[i] = voltage
        else:
            self.setpoint[channel] = voltage
