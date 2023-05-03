"""
bit_converter is a collection of the generic commands used for bit
manipulation in the CNi class. This also allows these codes to be
used for other hardware that may need similar bit manipulation.

extract() takes the hex code from the omega system and extracts the
individual components to return a list.

Example:
    0x11 memory address contains three 2-bit sets of data
    Each pertain to how colors are displayed
    Normal color starts at bit 0
    Alarm 1 color starts at bit 2
    Alarm 2 color starts at bit 4
    Normal_color = extract(36, 0, 1) -> 0
    Alarm1 = extract(36, 2, 3) -> 1
    Alarm2 = extract(36, 4, 5) -> 2
    decimal 36 = 0b 00 10 01 00
"""
from math import floor


def extract(code, index):
    """
    extract gets the raw hex code from the PID, and with the specified index it returns
    what the individual values of the code mean.

    code = raw hex code from PID
    index = start and stop positions of stored values.
    """
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


def compact(code, index, length=None):
    """
    compact is the inverse of extract.
    Converts values located at a binary index to hex characters.
    code provides the values stored in the hex string.
    index species which bits contain the code values.
    length specifies how long the hex code is supposed to be.

    In practice, length will pad zeros to make sure the returned
    value is the proper size. That's why length is called here
    but not in extract.
    """
    if (len(code) is not len(index)) and (len(code) is not len(index)-1):
        raise ValueError('Input values must match index length.')
    val = 0
    for n, i in enumerate(code):
        val = val + i*(2**index[n])
    output = hex(val)[2:].upper()
    if length is not None:
        if len(output) < length:
            while len(output) < length:
                output = '0' + output
    return output


def hexstr2dec(msg):
    """
    Converts the omega engineering scheme 6-byte number to decimal.
    Their 6-byte values are similar to floating point numbers.
    """
    if isinstance(msg, str):
        msg = int(msg, 16)

    _index = [0, 20, 23, 24]
    bits = extract(msg, _index)
    # bits[0] = data, bits[1] = decimal, bits[2] = sign
    output = bits[0] / (10**(bits[1]-1)) * ((-1)**bits[2])
    return output


def dec2hexstr(val):
    """
    inverse of hexstr2dec. Takes a decimal number and converts it to a 6-byte
    hex code ready to send to an omega engineering PID.

    Should be updated to include a specified decimal place for desired code output
    instead of assigning one based on the input value. Defaults to decimal code 2.
    """
    if val > 9999 or val < -9999:
        print('Input value outside of acceptable range. Must be between -9,999 and 9,999.')
        return
    _index = [0, 20, 23, 24]

    # First grab the sign of the value
    if val < 0:
        sign = 1
    else:
        sign = 0
    val = abs(val)
    
    # Determine the exponent and limit the value to 4 digits
    str_val = str(val)[0:5]
    exponent = str_val[::-1].find('.')
    if exponent == -1:
        exponent = 2
    else:
        exponent += 1
    val = int(val*(10**(exponent-1)))
    msg = [val, exponent, sign]
    output = compact(msg, _index, 6)
    return output

def msg2dec(msg):
    """
    Converts message with address and hexadecimal data to decimal.
    """
    return int(msg[3:-1], 16)
