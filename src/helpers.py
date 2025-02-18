import sys, os
from datetime import datetime
from dateutil.relativedelta import *
import textwrap
import json
import subprocess

datetime_string_format = '[%Y] %b %d %H:%M:%S'

def block_print():
    sys.stdout = open(os.devnull, 'w')

def enable_print():
    sys.stdout = sys.__stdout__

def get_test(logic):
    if logic == '<':
        return lambda a,b: a < b
    elif logic == '>':
        return lambda a,b: a > b
    elif logic == '==' or logic == '=':
        return lambda a,b: a == b
    elif logic == '>=' or logic == '=>':
        return lambda a,b: a >= b
    elif logic == '<=' or logic == '=<':
        return lambda a,b: a <= b
    elif logic is None:
        return lambda a,b: True
    else:
        raise ValueError('Unrecognized logic operator.')

def print_header(message):
    block = ''
    block_size = 70
    text_width = 50
    for i in range(block_size):
        block += '*'
    print(block)
    lines = message.split('\n')
    message = []
    for line in lines:
        wrapper = textwrap.wrap(line, width=text_width)
        for chunk in wrapper:
            message.append(chunk)
    for line in message:
        length = len(line)
        if len(line) < block_size:
            spacer = ''
            for i in range(int((block_size-length)/2)-1):
                spacer += ' '
            line = '*' + spacer + line + spacer
            if len(line) == block_size-2:
                line += ' *'
            else:
                line += '*'
        print(line.upper())
    print(block)

def read_file(name):
    try:
        with open(name) as file:
                data = file.read()
    except FileNotFoundError:
        name = f'{name}.txt'
        with open(name) as file:
                data = file.read()
    mod_time = os.path.getmtime(name)
    mod_date = datetime.fromtimestamp(mod_time).strftime(datetime_string_format)
    return json.loads(data), mod_date

def stop_string(dt):
    now = datetime.now()
    stop_time = now + relative_seconds(dt)
    return stop_time.strftime(datetime_string_format)

def relative_seconds(seconds):
    hours = int(seconds/3600)
    minutes = int((seconds - hours*3600)/60)
    seconds = seconds - hours*3600 - minutes*60
    return relativedelta(seconds=+seconds, minutes=+minutes, hours=+hours)

def progressbar(i,
                total,
                remaining,
                units = '%',
                interval='minutes',
                size = 20):
    sys.stdout.write('\r')
    if total != 0:
        sys.stdout.write("[%-20s] %s %s [%s %s remaining]     " %
                         ('='*int(i/total*size),
                          f'{i:.2f}', units, f'{remaining:.2f}', interval))
    sys.stdout.flush()

def print_files(folder, background=False):
    files = os.listdir(folder)
    if not background:
        print(f'Items in {folder}:')
        for n, file in enumerate(files):
            print(f'{n}: {file}')
    return files

def now():
    ''' datetime.now is called in many different instances.
    This function used to ensure standarized use across the code.
    '''
    return datetime.now().strftime(datetime_string_format)

def print_method(method):
    file_text = '[\n'
    for state in method:
        if isinstance(state, str):
            file_text += f'"{state}",\n'
            continue
        file_text += '{\n'
        for key in state:
            key_text = f'    "{key}":'
            while len(key_text) < 19:
                key_text += ' '
            if isinstance(state[key], str):
                key_text += f'"{state[key]}",\n'
            elif isinstance(state[key], bool):
                key_text += f'{["false", "true"][state[key]]},\n'
            else:
                key_text += f'{state[key]},\n'
            file_text += key_text
        file_text = file_text[:-2]
        file_text += '},\n'
    file_text = file_text[:-2] + '\n]'
    return file_text

def clean_method(file):
    met = read_file(file)[0]
    txt = print_method(met)
    with open(file, 'w') as file:
        file.write(txt)

def bash2list(bstring):
    ''' Converts a list of strings printed while executing a cmd line
    function to a python list.
    '''
    return str(bstring)[2:-3].split('\\n')    

def get_devices():
    ''' loads and returns the dictionary specified in the devices setup file
    Includes the path this script is located in to 
    '''
    fd = os.path.abspath(__file__)
    cwd = os.path.dirname(fd)
    return read_file(os.path.join(cwd, 'devices'))[0], cwd

def find_devices():
    ''' find_devices finds the serial port path of the pre_con devices:
        adsorbent trap
        mass flow controller
        valve controller
    
    This runs the bash script scan.sh which returns the port path and the
    name of the device. An issue with this method is that it doesn't deal
    with multiple devices that use the same serial devices, e.g., there are
    two CH340 devices attached.
    
    The found devices are compared to the setup file "devices" to specify
    which serial device is which. If an unknown device appears, the user
    will be prompted to add it to the list. They can skip over it.
    '''
    known_devices, cwd = get_devices()
    path = os.path.join(cwd, 'scan.sh')
    bstring_devices = subprocess.check_output(['bash', path])
    lst = bash2list(bstring_devices)
    devices = {}
    for item in lst:
        split_item = item.split(' - ')
        ID = None
        for key in known_devices:
            if known_devices[key]['name'] == split_item[1]:
                ID = key
                break
        if ID is None:
            response = input(f'{split_item[1]} is an unknown device. Add it to registry? (y/n): ')
            if response.lower() == 'y':
                ID = input('What is the name of this device (e.g., mfc, ads, vc): ')
                known_devices[ID]['name'] = split_item[1]
                with open('devices', 'w') as file:
                    file.write(json.dumps(known_devices))
            else:
                continue
        devices[ID] = f'/{split_item[0]}'
    return devices

def reset_usb(obj):
    ''' Performs a hard reboot on the serial port.
    The device is reconnected upon completion of the port being reset.
    This is only done for pre_con devices. The setup file devices is
    used to locate the ID for resetting the port, finding what the new
    port path is, and reconnecting.

    Input:
    obj is either the serial object, or an object with a serial device
    attached to it.
    '''
    try:
        obj = obj.serial
    except AttributeError:
        pass
    known_devices = get_devices()[0]
    for device, port in find_devices().items():
        if port == obj.port:
            name = device
            break
    device_id = known_devices[name]['ID']
    obj.close()
    subprocess.call(['sudo', 'usbreset', device_id])
    obj.port = find_devices()[name]
    obj.open()

# if __name__=='__main__':
#    # Tests for the helper functions
#    print(find_devices())
#    print(reset_usb(0,'mfc'))
#    progressbar(0,1,1)
#    print()
#    relative_seconds(5*3600)
#    print(stop_string(5*60))
#    met, dt = read_file('Methods/standard.txt')
#    txt = print_method(met)
#    print_header('something\nanother thing')
#    get_test('>')
#    block_print()
#    enable_print()
#    print(now())
