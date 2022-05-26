# bit_converter is a collection of the generic commands used for bit
# manipulation in the omega_tc class. This also allows these codes to be
# used for other hardware that may need similar bit manipulation.

from math import floor

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

# compact is the inverse of extract.
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

def hexstr2dec(msg):
    if isinstance(msg,str):
        msg = int(msg, 16)
    _index = [0,20,23,24]
    bits = extract(msg,_index)
    # bits contains a pseudo-floating point interpretation of the data.
    # bits[0] = data, bits[1] = decimal, bits[2] = sign
    output = bits[0] / (10**(bits[1]-1)) * ((-1)**bits[2])
    return output

def dec2hexstr(val):
    if val > 9999 or val < -9999:
        print('Input value outside of acceptable range. Must be between -9,999 and 9,999.')
        return
    _index = [0,20,23,24]
    
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
        exponent = 1
    else:
        exponent += 1
    val = int(val*(10**(exponent-1)))
    msg = [val, exponent, sign]
    output = compact(msg, _index, 6)
    return output
