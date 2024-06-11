from serial import Serial
import traceback
import argparse
import json
import time
import subprocess
from dateutil.relativedelta import *
from datetime import datetime
import sys
import os
import RPi.GPIO as GPIO
from numpy import trapz
from src.thermal_controller.omega_tc import CNi
from src.uPy import uPy
from src.helpers import *
from src.pre_con_classes import *
from src.switch import switch
from src.remote import remote
from src.serial_port import serial_ports

class pre_con:
    def __init__(self, debug=False):
        try:
            self.switch = switch(connected_obj=self)
            self._switch_state = self.switch.state
            if self.switch_state['debug'] == 1:
                debug = True
            self.remote = remote()
        except RuntimeError:
            GPIO.cleanup()
            self.__init__(debug=debug)
        if not debug: # debug being true disables connecting to external devices in init
            devices = find_devices()
            for device in ['vc', 'mfc', 'ads']:
                port = devices[device]
                try:
                    if device == 'vc':
                        self.vc = uPy(port)
                    elif device == 'mfc':
                        self.mfc = uPy(port)
                        self.mfc.sample = 0
                        self.mfc.backflush = 1
                        self.mfc.ports = self.mfc.echo('len(MFC)')
                        self.mfc.timeout = self.mfc.echo('timeout') + 1
                    elif device == 'ads':
                        self.ads_connect(devices[device])
                except KeyError:
                    print(f'{device.upper()} not found.')

                print(f'Successfully connected to {device.upper()} on port {port}!')

            self.current_state = {}
            self.current_state = {'name':      'off',
                                  'valves':    [0,0,0,0,0],
                                  "h2o":       None,
                                  "ads":       None,
                                  "sample":    None,
                                  "backflush": None,
                                  "pump":      0,
                                  "aux1":      0,
                                  "aux2":      0,
                                  "condition": None,
                                  "value":     None,
                                  "message":   None}

    @property
    def switch_state(self):
        return self._switch_state

    @switch_state.setter
    def switch_state(self, new_state):
        self._switch_state = new_state
        self.manual_override()

    def manual_override(self):
        if self.switch.state['enable']:
            positions = [x for x in self.switch.state.values()]
            self.valve(range(0, 6), positions[1:7])
            self.current_state['name'] = 'manual override'
            self.current_state['valves'] = positions[1:6]
            self.current_state['pump'] = positions[6]
            if self.switch.state['debug']:
                raise AssertionError('Emergency stop initiated. Override and debug enabled')

###########################################################################
# Code for PID Controllers
###########################################################################
    def ads_connect(self, serial):
        # Add getting id info
        with open('src/thermal_controller/PID calibration.txt') as file:
            data = file.read()
        cal = json.loads(data)
        try:
            if self.ads.serial.is_open:
                self.ads.serial.sendBreak()
                self.ads.serial.close()
        except AttributeError:
            pass
        block_print()
        self.ads = CNi(serial, limit=320, band=2)
        self.ads.convert = lambda x: x*cal['ads'][0] + cal['ads'][1]
        enable_print()

    def ads_temp(self, temp=None):
        if temp > self.ads.limit:
            print(f'Set point too high! Must be lower than {self.ads.limit}.')
            return
        if temp is None:
            print(self.ads.set_point())
        else:
            if temp > 100:
                print(f'Setting calibrated setpoint for {temp}')
                temp = self.ads.convert(temp)
            self.ads.set_point(round(temp,1))
        self.current_state['ads'] = temp

    def ads_calibrate(self, temp=None):
        from src.thermal_controller import pid_tuning
        new_cal = pid_tuning.calibrate(pre_con=self, temp=temp)
        filename = 'src/thermal_controller/PID calibration.txt'
        with open(filename) as file:
                data = file.read()
        cal = json.loads(data)
        cal['ads'] = list(new_cal)
        with open(filename, 'w') as file:
            file.write(json.dumps(cal))
        self.__init__(debug=True)

    def h2o_temp(self, temp=None):
        if temp > self.h2o.limit:
            print(f'Set point too high! Must be lower than {self.h2o.limit}.')
            return
        if temp is None:
            print(self.h2o.set_point())
        else:
            if temp > 0:
                temp = self.h2o.convert(temp)
            self.ads.set_point(sp)


###########################################################################
# Code for Mass Flow Controller
###########################################################################
    def flowrate(self, position=None, flowrate=None):
        if position == None:
            position = range(self.mfc.ports)
        else:
            position = [position]
        val = []
        for i in position:
            msg = 'MFC[{}].flowrate({})'.format(i, flowrate)
            if flowrate == None:
                timeout = 0.5
            else:
                timeout = self.mfc.timeout
            val.append(self.mfc.echo(msg, timeout=timeout))
        return val

    def sample(self, flowrate=None, display=True):
        sample_flowrate = self.flowrate(position=0, flowrate=flowrate)[0]
        self.current_state['sample'] = flowrate
        if flowrate is None:
            if display:
                print(sample_flowrate)
            else:
                return(sample_flowrate)

    def backflush(self, flowrate=None, display=True):
        backflush_flowrate = self.flowrate(position=1, flowrate=flowrate)[0]
        self.current_state['backflush'] = flowrate
        if flowrate is None:
            if display:
                print(backflush_flowrate)
            else:
                return(backflush_flowrate)

    def check_battery(self):
        cal = [3.4459, 0.0152]
        return cal[0]*self.mfc.echo('adc.single(3)') + cal[1]

###########################################################################
# Code for valve controller
###########################################################################
    def valve(self, valve=None, position=None):
        if isinstance(valve, int):
            self.vc.write(f'rotate({valve},{position})')
            if valve < 5:
                self.current_state['valves'][valve] = position
        if isinstance(valve, (list, range)):
            check = []
            for n, i in enumerate(valve):
                if isinstance(position, int):
                    self.valve(i, position)
                else:
                    self.valve(i, position[n])
        if valve == None:
            if isinstance(position, list):
                length = position.__len__()
                if length > 8:
                    raise ValueError('Position list cannot be more than 8 items.')
                for i in range(length):
                    self.valve(i, position[i])
            elif position is None:
                p = self.vc.echo('rotate()')
                return p

    def pulse(self, valve, sleep):
        if not isinstance(valve, int):
            raise ValueError('Selected valve must be an integer.')
        if valve > 8 or valve < 0:
            raise ValueError('Selected valve outside acceptable range.')
        if not (isinstance(sleep, (int, float))):
            raise ValueError('Sleep time must be a number.')
        try:
            pulse = self.vc.write(f'pulse(v[{valve}],sleep={sleep*60})')
        except SystemError as x:
            if x.__str__()== 'Device timed out.':
                print('Device timeout detected. Attempting to reconnect to valve controller.')
                reset_usb(self.vc)
            else:
                raise SystemError(x)
        return pulse

    def home_valves(self):
        self.valve(range(0,8),0)

    def stream(self, position=None):
        if position==None:
            return int(self.vc.echo('m.readpos()'))
        elif isinstance(position, int):
            self.vc.echo(f'm.actuate({position})', timeout=10)
            return
        elif isinstance(position, str):
            if position.lower()=='home':
                return self.vc.write('m.home()')
            elif position.lower()=='step':
                return self.vc.write('m.step()')
            else:
                raise ValueError('Invalid stream select command. Use "home", "step", or enter the position.')
        else:
            raise(ValueError)

    def step(self):
        self.vc.write(f'm.step()\r')

    def relay(self, name, command):
        pin = {'pump':5, 'aux1':6, 'aux2':7}[name]
        if command == None:
            print(f"The {name} is currently turned {self.current_state['pump']}.")
        elif (command == 'off') or (command == 0):
            self.valve(pin, 0)
            self.current_state['pump'] = 'off'
        elif (command == 'on') or (command == 1):
            self.valve(pin, 1)
            self.current_state['pump'] = 'on'
        else:
            print('Invalid input, must be 0 or 1, or "off or "on". Use no input to return the current pump state.')

    def pump(self, command=None):
        self.relay(name='pump', command=command)

    def aux1(self, command=None):
        self.relay(name='aux1', command=command)

    def aux2(self, command=None):
        self.relay(name='aux2', command=command)

    def measure(self, device=None):
        if device == 'ads':
            return self.ads.measure()
        elif device == 'h2o':
            return self.h2o.measure()
        elif device == 'battery':
            return self.check_battery()

    def state(self, state=None, check=False, background=False):
        """
        This function has 4 different routes that depend on name and check:
        Route 1: nothing called (name = None, check = False)
           Info: Print the current state values to the cmd line

        Route 2: request available state names (name = None, check = True)
           Info: Print which states can be called.

        Route 3: check values of a given state (name = something, check = True)
           Info: Print the values for the declared name. This will return an
                 error if the name does not exist in self.states. This is used
                 to validate if a state name exists prior to running a full method
                 and erroring at a crucial step.

        Route 4: change state (name = something, check = False)
           Info: This is where the system is commanded to change states based on the
                 input. The function will hold on any checks that must occur prior to
                 advancing the system: timing, precise timing, temperature, GC ready.
                 If the advancing condition is set to None, the system will apply all
                 settings and automatically return.
        """
        def state_help():
            # need to update to look up pre_con states
            print('You may use one of the following keys:')
            for i in self.states.keys():
                print(i)
            return

        def print_state(state):
            string = ""
            position = ['off','on']
            if state['valves'] == None:
                string += "Valves are not altered by this state call.\n"
            else:
                for n, i in enumerate(state['valves']):
                    string += f"Valve {str(n)}: {position[i]} \n"
            string += f"H2O Trap Temperature = {str(state['h2o'])}\n"
            string += f"ADS Trap Temperature = {str(state['ads'])}\n"
            string += f"Sample flowrate = {str(state['sample'])}\n"
            string += f"Backflush flowrate = {str(state['backflush'])}\n"
            string += f"Pump is {state['pump']}\n"
            string += f"Aux1 is {state['aux1']}\n"
            string += f"Aux2 is {state['aux2']}\n"
            try:
                string += f"Stream selected: {self.stream()}\n"
            except AttributeError:
                pass

            if state['condition'] == None:
                string += f"This state has no check following completion."
            else:
                string += f"With an advancement condition of '{state['condition']}' "
                string += f"set to {state['value']}."
            if not background:
                print(f'{string}\n')
            return

        #############################################################
        # Checks if the function was called for information
        #############################################################
        if state == None:
            if check:
                state_help()
                return
            else:
                string = 'The pre-concentration system is currently in the '
                string += f"{self.current_state['name']} state: \n"
                print(string)
                print_state(self.current_state)
                return
        else:
            if isinstance(state, str):
                with open('src/precon_states') as file:
                    data = file.read()
                states = json.loads(data)
                name = state
                state = states[name].copy()
                state['name'] = name
            elif isinstance(state, dict):
                pass
            else:
                raise TypeError('Name must be the name of a default state, or a state_item.')

            new_state = state_item(state)
            name = new_state['name']

            if check:
                if not background:
                    print(f"Settings for the {name} state: \n")
                    print_state(new_state)
                return state

        #############################################################
        # Engage the new state if a state change is requested.
        #############################################################
        condition = new_state['condition']
        monitor = new_state['monitor']
        _monitor = []
        if condition != None:
            condition = condition.lower()
        valid_conditions = (None, 'gc', 'pulse', 'time', 'temp', 'manual')
        valid_conditions.index(condition) # Causes an error if an invalid condition is called.
        print(f"Beginning state: {name}.\n{new_state['message']}")            

        #############################################################
        # GC Ready Condition
        #############################################################
        if condition=='gc':
            try:
                timeout = new_state['timeout']*60
            except:
                timeout = 360
            print('Waiting for GC to be ready.')
            print(f'Method will time out at {stop_string(timeout)} if the GC is not ready.')
            start = time.time()
            while not self.remote.check_ready():
                if time.time() > start + timeout:
                    self.__init__(debug=True)
                    if not self.remote.check_ready():
                        raise RuntimeError('GC not ready in time. Aborting run.')

            print('GC ready.')
            dt = new_state['value']
            if new_state['value'] == None:
                return

        #############################################################
        # Precision Timing Condition
        #############################################################
        if condition=='pulse' or condition=='gc':
            dt = new_state['value']
            v = new_state['valves']
            if condition == 'pulse' or dt != 0:
                if sum(v) > 1:
                    raise ValueError('More than 1 valve specified.')
                else:
                    v = v.index(1)
            if condition == 'pulse':
                print(f'Precision timed pulse ({dt} min) on valve {v}.')
                print(f'Pulse will complete at {stop_string(dt*60)}.')
            if condition == 'gc':
                self.remote.start()
                if dt == 0:
                    return
            self.pulse(valve=v, sleep=dt)
            t0 = time.time()
            t = []
            while True:
                t.append(time.time()-t0)
                if monitor:
                    if self.current_state['sample'] != 0:
                        _monitor.append(self.sample(display=False))
                    else:
                        _monitor.append(self.backflush(display=False))
                elapsed = t[-1]/60
                if self.vc.serial.in_waiting > 9:
                    msg = self.vc.read()
                    if msg[2:4] == 'ok':
                        progressbar(i = dt,
                                    total = dt,
                                    remaining=0,
                                    units='min',
                                    interval = 'minutes')
                    break
                if elapsed >= dt + 1:
                    raise SystemError('Valve controller failed to complete pulse cycle.')
                else:
                    if not background:
                        progressbar(i = elapsed,
                                    total = dt,
                                    remaining = dt - elapsed,
                                    units='min',
                                    interval = 'minutes')
                time.sleep(0.25)

            self.current_state = new_state
            self.current_state['name'] = name
            if monitor:
                flow_volume = trapz(_monitor, t)/60
                print(f'{monitor} volume: {flow_volume} mL')
                return flow_volume
            return

        ads = new_state['ads']
        h2o = new_state['h2o']
        h2o = None # remove when h2o trap implemented
        if condition != 'temp':
            if h2o != None:
                self.h2o_temp(h2o)
            if ads != None:
                self.ads_temp(ads)

        if new_state['valves'] != None:
            self.valve(position=new_state['valves'])
        if new_state['pump'] != None:
            self.pump(new_state['pump'])
        if new_state['aux1'] != None:
            self.aux1(new_state['aux1'])
        if new_state['aux2'] != None:
            self.aux2(new_state['aux2'])
        sample = new_state['sample']
        backflush = new_state['backflush']
        if sample != None:
            if sample == 0:
                print('Sample flow disabled.')
            else:
                print(f'Setting sample flow rate to {sample}. Please wait for flow to stabilize.')
            self.sample(sample)
        if backflush != None:
            if backflush == 0:
                print('Backflush flow disabled.')
            else:
                print(f'Setting backflush flow rate to {backflush}. Please wait for flow to stabilize.')
            self.backflush(backflush)

        #############################################################
        #  Temperature Condition
        #############################################################
        if condition=='temp':
            test = get_test(new_state['value'])
            timeout = new_state['timeout']
            if timeout is None:
                timeout = 1
            for i in ['ads', 'h2o', 'battery']:
                if new_state[i] != None:
                    device = i
                    print(f'Checking that {device} is {new_state["value"]}{new_state[device]}')
                    def check():
                        return test(new_state[device], self.measure(device)), self.measure(device)
            t0 = time.time()
            while True:
                if monitor:
                    _monitor.append(check()[1])
                if check()[1] is False:
                    print()
                    if device == 'ads':
                        if not self.ads.measure():
                            print(f'Detected connection loss with ADS (port {self.ads.serial.port}). Attempting to reconnect.')
                            reset_usb(self.ads)
                            if not self.ads.measure():
                                raise RuntimeError('Failed to reconnect to ADS.')
                            self.state(new_state)
                if not background:
                    txt = f"Currently measuring: {check()[1]:.2f}"
                    remaining = round((t0 + timeout*60- time.time())/60, 2)
                    txt += f" [timing out in {remaining} minutes]   "
                    sys.stdout.write('\r')
                    sys.stdout.write(txt)
                    sys.stdout.flush()
                if not check()[0]:
                    break
                time.sleep(0.5)
                if time.time() > t0 + timeout*60:
                    self.state('off')
                    if abs(check()[1]-new_state[device]) < abs(new_state[device])*.01:
                        print(f'System within ({check()[1]}) within 1%. Continuing to next state.')
                        break
                    raise SystemError(f'{device} failed to reach {new_state[device]} in time. Currently measuring: {check()[1]:.2f}')
            print('')
            print(f"{device} threshold reached! Currently measuring {check()[1]:.2f}")

        #############################################################
        # Timing Condition
        #############################################################
        if condition == 'time' and new_state['value'] > 0:
            dt = int(new_state['value']*60)
            print(f'Waiting {dt} seconds to proceed.')
            t0 = time.time()
            print(f'Wait will complete at {stop_string(dt)}.')
            while time.time() < t0 + dt:
                t = time.time() - t0
                if dt > 10:
                    if not background:
                        progressbar(i = t,
                                    total = dt,
                                    remaining = dt - t,
                                    units='s',
                                    interval = 'seconds')
                    time.sleep(.2)
            progressbar(i=dt, total=dt, remaining=0, units='s', interval='seconds')

        #############################################################
        # Manual Condition
        #############################################################
        if condition == 'manual':
            print('Flick the "debug" switch on then front on then off to continue.')
            try:
                timeout = new_state['timeout']
            except:
                timeout = 5*60
            t0 = time.time()
            pointer = 0
            states = [0,1,0]
            while True:
                if self.switch_state['debug'] == states[pointer]:
                    pointer += 1
                    if pointer == len(states):
                        break
                if time.time() > t0 + timeout:
                    raise TimeoutError(f'Manual switching timed out after {timeout} minutes.')

        self.current_state['name'] = name
        print('')
        if _monitor != []:
            return _monitor
        else:
            return

    def check_method(self, name='standard.txt', background=False):
        """
        check_method prints each state in a method file. This
        also provides a rudamentary check that the method file
        contain all the necessary fields and doesn't have any typos.
        """
        if type(name) is str:
            fname = f'src/Methods/{name}'
            try:
                method, modified_date = read_file(fname)
            except json.decoder.JSONDecodeError as x:
                print(f'Unable to read file: {x}')
                return
        elif type(name) is list:
            method = name.copy()
            name = 'User Input method'
            modified_date = now()

        notes = f'Checking method {name}'
        notes += f', last modified: {modified_date}\n'
        notes += '\nList of states:\n'

        state_names = []
        name_warnings = ''
        timeout = 0
        for state in method:
            if isinstance(state, str):
                next_name = state
                try:
                    self.state(state, check=True, background=True)
                except KeyError:
                    raise KeyError(f'{next_name} is not a valid default state.')
            else:
                next_name = state['name']
            notes += f'{next_name}\n'
            if next_name in state_names:
                name_warnings += f'Warnings: {next_name} is repeated.\n'
            state_names.append(next_name)
        notes += '\n'
        start_notes = notes
        notes += name_warnings
        run_time = 0
        gc_flag = True

        for state in method:
            try:
                block_print()
                state = self.state(state, check=True, background=True)
                enable_print()
                try:
                    condition = state['condition']
                except KeyError:
                    condition = None
                try:
                    value = state['value']
                except KeyError:
                    value = None
                try:
                    timeout += state['timeout']
                except:
                    pass
                try:
                    monitor = state['monitor']
                except KeyError:
                    monitor = None

                valid_monitors = (None, False, True)
                try:
                    valid_monitors.index(monitor)
                except:
                    notes += f'Invalid monitor condition on {state["name"]}: {state["monitor"]}\n'
                if monitor:
                    notes += f'Monitoring on {state["name"]}\n'
                if condition == 'temp':
                    get_test(state['value'])
                    try:
                        state['timeout']
                    except KeyError:
                        notes += f"Warning: {state['name']} does not have a timeout.\n"
                elif condition == 'pulse':
                    if sum(state['valves']) > 1:
                        notes += f"Error: {state['name']} has more than 1 valve specified.\n"
                    if not isinstance(value, (int, float)):
                        notes += f"Error: {state['name']} value is not numerical.\n"
                    if value < 0:
                        notes += f"Error: {state['name']} value is negative.\n"
                    run_time += value
                elif condition == 'time':
                    if not isinstance(value, (int, float)):
                        notes += f"Error: {state['name']} value is not numerical.\n"
                    if value < 0:
                        notes += f"Warning: {state['name']} value is negative.\n"
                    run_time += value
                elif condition == 'gc':
                    if value != None:
                        if not isinstance(value, (int, float)):
                            notes += f"Error: {state['name']} value is not numerical.\n"
                        else:
                            if value < 0:
                                notes += f"Error: {state['name']} value is negative.\n"
                            else:
                                run_time += value
                                gc_flag = False
                elif condition == None:
                    if value != None:
                        notes += f"Warning: {state['name']} condition is None, but a value is given.\n"
                elif condition == 'manual':
                    if value != None:
                        notes += f"Warnings: {state['name']} a value is given for a manual advancing condition"
                else:
                    notes += f"Error: {state['name']} - {condition} is not a valid condition.\n"
            except Exception as x:
                notes += f"Error: Method fails on {state['name']}: {x}.\n"
                enable_print()
        if gc_flag:
            notes += 'Warning: this methods does not trigger the GC.\n'

        if notes == start_notes:
            notes += 'No errors or warnings were detected.\n'
        if timeout == 0:
            notes += f'Run time of {round(run_time,2)} minutes.\n'
        else:
            notes += f'Run time of {round(run_time,2)} to {round(run_time+timeout,2)} minutes.\n'
        notes += f'{name} has {len(method)} states.\n'
        if not background:
            print(notes)
        return run_time

    def run_method(self, name=None, stream=None, notes='', background=False):
        """
        """
        start_time = now()
        folder = 'src/Methods/'
        if name is None:
            files = print_files(folder, background=background)
            return files
        if isinstance(name, int):
            files = self.run_method(background=True)
            print(f'Running method {files[name]}')
            name = files[name]
        fname = folder + str(name)
        if type(name) == str:
            method, modified_date = read_file(fname)
        else:
            method = name.copy()
            name = 'User Input method'
            modified_date = now()
        error_flag = False
        if stream != None and stream != self.stream():
            print(f'Selecting sample #{stream}.')
            print('Running change over method to prime sample line.')
            self.pump(1)
            self.stream(stream)
            self.run_method('change over', background=background)
            print(f'Change over complete. Continuing to {name} method.')
        elif stream == None:
            stream = self.stream()

        error_notes = ''
        try:
            for state in method:
                if isinstance(state, str):
                    state = self.state(state, check=True, background=False)
                result = self.state(state, background=background)
                if result != None:
                    if notes != '':
                        notes += ' '
                    if isinstance(result, list):
                        # Save list results to something (temp monitors currently return a list)
                        result = result[-1]
                    notes += f'{state["name"]} returned: {result:.2f}. '
        except Exception as x:
            error_notes = f'Failed at {now()} on {state["name"]}: {x}.'.replace('\n', '')
            error_notes = error_notes.replace('..','.')

        end_time = now()
        log_entry = f'\n{start_time}, {end_time}, {name}'
        log_entry += f', {str(stream)}, {notes}, {modified_date}, {error_notes}'
        with open('logs/method log.csv', 'a') as file:
            file.write(log_entry)

        if error_notes != '':
            self.state('off')
            raise Exception(f'{error_notes} {notes}')
        else:
            print(notes)

    def standard_run(self, flow=None, volume=None, temp=None, delay=None,
                     inject=None, blank=False, stream=None, background=False,
                     save_name=None, run=True):
        ''' standard_run is a simple way to make small adjustments
        to the "standard.txt" run without needing to create a new file.
        This is to be used for repeated experiments that only need minor
        modifications to the standard procedure.

        Selecting a save_name will generate a method file with the given 
        modifications to the standard run. These can then be called directly
        in a sequence.
        '''
        if save_name is None:
            save_name = 'custom.txt'
        if flow is None:
            flow = 100
        if volume is None:
            volume = 500
        if temp is None:
            temp = 300
        if inject is None:
            inject = 30
        if delay is None:
            delay = 0

        fname = f'src/Methods/standard.txt'
        method, modified_date = read_file(fname)

        for n, state in enumerate(method):
            if state['name'] == 'flush':
                method[n]['value'] = 50/flow # set flush to purge 50 mL
                method[n]['sample'] = flow
            elif state['name'] == 'sampling':
                method[n]['value'] = volume/flow # volume/flowrate = time
            elif state['name'] == 'pre-backflush':
                if blank:
                    method[n]['backflush'] = flow
            elif state['name'] == 'backflush':
                if blank:
                    method[n]['value'] = volume/flow
            elif state['name'] == 'flash heat':
                method[n]['ads'] = temp
            elif state['name'] == 'inject':
                method[n]['value'] = inject/60
            elif state['name'] == 'bake out':
                bakeout_time = (120 - inject)/60
                if bakeout_time > 0:
                    method[n]['value'] = bakeout_time
                else:
                    method.remove(state)

        if blank:
            for state in method.copy():
                if (state['name'] == 'flush') or (state['name'] == 'sampling'):
                    method.remove(state)

        with open(f'src/Methods/{save_name}', 'w') as file:
            file.write(print_method(method))

        if delay > 0:
            method[-1]['condition'] = 'time'
            run_time = self.check_method(save_name, background=True)
            method[-1]['value'] = delay - run_time
            with open(f'src/Methods/{save_name}', 'w') as file:
                file.write(json.dumps(method))
            clean_method(f'src/Methods/{save_name}')

        notes = f'flow={flow} volume={volume} temp={temp} inject={inject} blank={blank}. '
        if stream is None or isinstance(stream, int):
            stream = [stream]
        if run:
            for index in stream:
                self.run_method(name=save_name, stream=index, notes=notes, background=background)

    def run_sequence(self, sequence=None, continuous=False, background=True):
        if sequence is None:
            files = print_files('src/Sequences/', background=background)
            return files
        sequence_name = sequence
        if isinstance(sequence, str):
            try:
                sequence = read_file(f'src/Sequences/{sequence}')[0]
            except FileNotFoundError:
                print(f'{sequence} not found. Available sequences are:\n')
                print(self.run_sequence)
                return
        elif isinstance(sequence, list):
            pass
        while True:
            print_header(f'Beginning sequence: {sequence_name}.')
            for item in sequence:
                item = sequence_item(item)
                repeats = list(range(item['Repetition']))
                for n in repeats:
                    txt = f'Beginning run ({n+1}/{item["Repetition"]})\n'
                    txt += f'Method: {item["Method"]}\n'
                    txt += f'Sample: "{item["Sample Name"]}".'
                    print_header(txt)
                    try:
                        start_time = time.time()
                        self.run_method(item['Method'],
                                        stream=item['Stream'],
                                        notes=f'Sample Name: {item["Sample Name"]}',
                                        background=background)
                        if item['Macro'] != None:
                            print('Macros have not been implemented.')
                    except Exception as x:
                        on_error = item['on_error']
                        if on_error == None:
                            print(type(x))
                            print(x.args)
                            raise x
                        if on_error == 'reset':
                            print(f'Exception occurred: {x}')
                            print('Resetting system and continuing.')
                            GPIO.cleanup()
                            self.__init__()
                            self.run_method('bake out', background=True)
                            continue
                        elif on_error == 'continue':
                            print(f'Exception occurred: {type(x)}:{x}')
                            print('Continuing sequence.')
                            continue
                    finally:
                        if self.switch.poll('debug'):
                            print('debug switch enabled')
                            break
                    if item['time'] != None:
                        if time.time() < (start_time + item['time']*60):
                            self.state({'name':      'sequence wait',
                                        'condition': 'time',
                                        'value':     item['time']-(time.time()-start_time)/60},
                                       background=background)
            if not continuous or self.switch.poll('debug'):
                break

parser = argparse.ArgumentParser(description='Pre-concentration system command line interface.')

#####################################################################
# Root arguments
#####################################################################
parser.add_argument('-r', '--run', action='store_true',
                    help='Activate the pre-concentration system to do a standard run.')
parser.add_argument('-m', '--method', type=str, default=False,
                    help='Run a specified method.')
parser.add_argument('-s', '--sequence', type=str, default=False,
                    help='Run a specified sequence.')
parser.add_argument('-c', '--cli', action='store_true',
                    help='Enter command line interface for continuous operation.')
parser.add_argument('-l', '--log', action='store_true',
                    help='View the last 10 log entries.')
parser.add_argument('--continuous', action='store_true', default=False,
                    help='Run specified sequence continuously.')

#####################################################################
# Optional Arguments for -r, --run
#####################################################################
parser.add_argument('--flow', type=int,
                    help='Set the flowrate in milliliters per minute [sccm].')
parser.add_argument('--volume', type=int,
                    help='Set the sample size in milliliters [mL].')
parser.add_argument('--temp', type=int,
                    help='Set the trap heated temperature in celsius [°C].')
parser.add_argument('--inject', type=int,
                    help='Set the GC injection time in seconds [s].')
parser.add_argument('--blank', action='store_true',
                    help='Perform a blank run. Sample will not flow.')
parser.add_argument('--stream', type=int, nargs='+',
                    help='Select sample port.')
parser.add_argument('--repeat', type=int, default=1,
                    help='Repeat method *n* number of times.')
parser.add_argument('--delay', type=int, default=0,
                    help='Timed delay, in minutes, to occur after a method is complete.')

def cli(obj):
    previous_entry = ''
    while True:
        user_input = input("> ")
        if user_input == 'exit()':
            pc.state('off')
            exit()
        else:
            if user_input[0:6] == 'print(' and user_input[-1] == ')':
                user_input = user_input[0:6] + 'pc.' + user_input[6:]
            else:
                user_input = 'pc.' + user_input
        try:
            eval(user_input)
        except Exception as x:
            traceback.print_exc()

if __name__ == '__main__':
    args = parser.parse_args()
    check = [args.run, args.method, args.sequence, args.log, args.cli]
    check = [(x!=False) for x in check]
    if sum(check) > 1:
        error_notes = 'Multiple methods called. Please select to only run (-r, --run), '
        error_notes += 'specify a method (-m, --method), sequence (-s, --sequence), '
        error_notes += ',call the log (-l, --log), or enter the command line '
        error_notes += 'interface (-c, --cli).'
        raise SystemError(error_notes)
    elif sum(check) == 0:
        print('No arguments given.')
    GPIO.setwarnings(False)
    pc = pre_con()
    GPIO.setwarnings(True)

    if args.cli:
        cli(pc)

    if args.run:
        for n in range(args.repeat):
            pc.standard_run(flow=args.flow,
                            volume=args.volume,
                            temp=args.temp,
                            inject=args.inject,
                            blank=args.blank,
                            stream=args.stream,
                            delay=args.delay)

    if args.method is not False:
        pc.run_method(args.method)

    if args.sequence is not False:
        pc.run_sequence(args.sequence, continuous=args.continuous)

    if args.log:
        import csv
        fname = 'logs/method log.csv'
        with open(fname, 'r') as file:
            log = file.read()
        print('Not yet implemented.')

    pc.state('off')
    print('EOF')
