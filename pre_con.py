from serial import Serial
import argparse
import json
import time
import sys 
import os
from datetime import datetime
import RPi.GPIO as GPIO
from numpy import trapz
from src.thermal_controller.omega_tc import CNi
from src.uPy import uPy
from src.switch import switch
from src.remote import remote
from src.serial_port import serial_ports

def block_print():
    sys.stdout = open(os.devnull, 'w')

def enable_print():
    sys.stdout = sys.__stdout__


class pre_con:
    def __init__(self, debug=False):
        self.switch = switch(connected_obj=self)
        self._switch_state = self.switch.state
        self.remote = remote()
        if not debug:
            for i in serial_ports():
                try:
                    device = uPy(i)
                    txt = device.echo('name')
                    if txt == 'Valve Controller':
                        self.vc = device
                        print('Successfully connected to Valve Controller!')
                    elif txt == 'Mass Flow Controller':
                        self.mfc = device
                        self.mfc.sample = 0
                        self.mfc.backflush = 1
                        self.mfc.ports = self.mfc.echo('len(MFC)')
                        self.mfc.timeout = self.mfc.echo('timeout') + 1
                        print('Successfully connected to MFC Controller!')
                except:
                    # Will need to add ways to determine if ADS or H2O Trap later.
                    try:
                        block_print()
                        self.ads = CNi(i)
                        enable_print()
                        print('Successfully connected to adsorbent trap!')
                    except:
                        print(f'Unknown device on port: {i}')
                        
            with open('src/thermal_controller/PID calibration.txt') as file:
                data = file.read()
            cal = json.loads(data)
            self.ads.convert = lambda x: x*cal['ads'][0] + cal['ads'][1]
            
            self.current_state = {}
            self.current_state = {'name':      'off',
                                  'valves':    [0,0,0,0],
                                  "h2o":       None,
                                  "ads":       None,
                                  "sample":    None,
                                  "backflush": None,
                                  "pump":      1,
                                  "condition": None,
                                  "value":     None,
                                  "message":   None}
            self.state('off')

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
            pos = positions[1:-1]
            pos.append(0)
            pos.append(positions[-1])
            self.valve(range(0,5), pos)
            self.current_state['name'] = 'manual override'
            self.current_state['valves'] = pos[1:4]
            self.current_state['pump'] = pos[5]

###########################################################################
# Code for PID Controllers
###########################################################################
    def ads_temp(self, temp=None):
        if temp is None:
            print(self.ads.set_point())
        else:
            if temp > 100:
                temp = self.ads.convert(temp)
            self.ads.set_point(round(temp,1))

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
            val.append(self.mfc.echo(msg, timeout = self.mfc.timeout))
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

###########################################################################
# Code for valve controller
###########################################################################
    def valve(self, valve=None, position=None):
        if isinstance(valve, int):
            self.vc.write(f'v[{valve}]({position})')
            if valve < 4:
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

    def pulse(self, valve, sleep):
        if not isinstance(valve, int):
            raise ValueError('Selected valve must be an integer.')
        if valve > 8 or valve < 0:
            raise ValueError('Selected valve outside acceptable range.')
        if not (isinstance(sleep, (int, float))):
            raise ValueError('Sleep time must be a number.')
        return self.vc.write(f'pulse(v[{valve}],sleep={sleep*60})')

    def home_valves(self):
        self.valve(range(0,8),0)

    def stream(self, position=None):
        if position==None:
            return int(self.vc.echo('m.readpos()'))
        elif isinstance(position, int):
            return self.vc.write(f'm.actuate({position})')
        elif isinstance(position, str):
            if position.lower()=='home':
                return self.vc.write('m.home()')
            elif position.lower()=='step':
                return self.vc.write('m.step()')
            else:
                print('Invalid stream select command. Use "home", "step", or enter the position.')
        else:
            raise(ValueError)

    def step(self):
        self.vc.write(f'm.step()\r')

    def pump(self, command = None):
        if command == None:
            print(f"The pump is currently turned {self.current_state['pump']}.")
        elif (command == 'off') or (command == 0):
            self.valve(4, 0)
            self.current_state['pump'] = 'off'
        elif (command == 'on') or (command == 1):
            self.valve(4, 1)
            self.current_state['pump'] = 'on'
        else:
            print('Invalid input, must be 0 or 1, or "off or "on". Use no input to return the current pump state.')

    def state(self, name=None, check=False):
        """
        This function has 4 different routes that depend on name and check:
        Route 1: nothing called (name = None, check = False)
           Info: Print the current state values to the cmd line
           
        Route 2: request available state names (name = None, check = True)
           Info: Print which states can be called.
           
        Route 3: check values of a given state (name = something, check = True)
           Info: Print the values for the declared name. This will return an
                 error if the name does not exist in self.states. This is used
                 to validate if a state name exists prior to running a full sequence
                 and erroring at a crucial step.
                 
        Route 4: change state (name = something, check = False)
           Info: This is where the system is commanded to change states based on the
                 input. The function will hold on any checks that must occur prior to
                 advancing the system: timing, precise timing, temperature, GC ready.
                 If the advancing condition is set to None, the system will apply all
                 settings and automatically return.
        """
        def state_help():
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
            if isinstance(state['pump'], int):
                string += f"Pump is {position[state['pump']]}\n"
            else:
                string += f"Pump is {state['pump']}\n"
            try:
                string += f"Stream selected: {self.stream()}\n"
            except AttributeError:
                pass

            if state['condition'] == None:
                string += f"This state has no check following completion."
            else:
                string += f"With an advancement condition of '{state['condition']}' "
                string += f"set to {state['value']}."
            print(f'{string}\n')
            return

        #######################################################
        # Checks if the function was called for information
        #######################################################
        if name == None:
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
            if isinstance(name, str):
                with open('src/precon_states') as file:
                    data = file.read()
                states = json.loads(data)
                new_state = {'name':name}
                name = states[name].copy()
            else:
                new_state = {}

            keys = ["valves", "h2o", "ads", "sample",
                    "backflush", "pump", "condition",
                    "value", "message", "monitor"]
            for key in keys:
                new_state[key] = None
            for key in name:
                new_state[key] = name[key]
            try:
                name = new_state['name']
            except KeyError:
                for name, values in new_state.items():
                    new_state = values.copy()
                    new_state['name'] = name

            if check:
                print(f"Settings for the {name} state: \n")
                print_state(new_state)
                return

        #######################################################
        # Engage the new state if a state change is requested.
        #######################################################
        condition = new_state['condition']
        monitor = new_state['monitor']
        if condition != None:
            condition = condition.lower()
        valid_conditions = (None, 'gc', 'pulse', 'time', 'temp')
        valid_conditions.index(condition) # Causes an error if an invalid condition is called.
        valid_monitor = (None, 'ads', 'h2o', 'sample', 'backflush')
        valid_monitor.index(monitor)
        if new_state['message'] != None:
            print(f"\n{new_state['message']}\n")
        else:
            print(f"\nBeginning state: {name}.\n")

        #######################################################
        # GC Ready Condition
        #######################################################
        if condition=='gc':
            start = time.time()
            print('Waiting for GC to be ready.')
            try:
                timeout = new_state['timeout']*60
            except:
                timeout = 360
            while not self.remote.gc_ready:
                if time.time() > start + timeout:
                    raise RuntimeError('GC not ready in time. Aborting run.')
            print('GC ready.')
            dt = new_state['value']
            if new_state['value'] == None:
                return True
            
        #######################################################
        # Precision Timing Condition
        #######################################################
        if condition == 'pulse' or condition == 'gc':
            dt = new_state['value']
            v = new_state['valves']
            if condition == 'pulse' or dt != 0:
                if sum(v) > 1:
                    raise ValueError('More than 1 valve specified.')
                else:
                    v = v.index(1)
            if condition == 'pulse':
                print(f'Precision timed pulse on valve {v}.')
            if condition == 'gc':
                self.remote.start()
                if dt == 0:
                    return
            self.pulse(valve=v, sleep=dt)
            t0 = time.time()
            flow_check = []
            t = []
            while True:
                t.append(time.time()-t0)
                if monitor == 'sample':
                    flow_check.append(self.sample(display=False))
                elif monitor == 'backflush':
                    flow_check.append(self.backflush(display=False))
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
                if elapsed >= dt + 0.25:
                    raise SystemError('Valve controller failed to complete pulse cycle.')
                else:
                    progressbar(i = elapsed,
                                total = dt,
                                remaining = dt - elapsed,
                                units='min',
                                interval = 'minutes')
                time.sleep(0.25)
            print('')
            self.current_state = new_state
            self.current_state['name'] = name
            if flow_check != []:
                flow_volume = trapz(flow_check, t)/60
                print(f'{monitor} volume: {flow_volume} mL')
                return flow_volume
            return

        valves = new_state['valves']
        if valves != None:
            self.valve(position=valves)
        pump = new_state['pump']
        if pump != None:
            self.pump(pump)
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

        ads = new_state['ads']
        h2o = new_state['h2o']
        h2o = None #remove when h2o trap implemented
        if condition != 'temp':
            if h2o != None:
                self.h2o_temp(h2o)
                self.current_state['h2o'] = h2o
            if ads != None:
                self.ads_temp(ads)
                self.current_state['ads'] = ads

        ########## Temperature Condition ##########
        if condition == 'temp':
            logic = new_state['value']
            test = get_test(new_state['value'])
            try:
                timeout = new_state['timeout']
            except:
                timeout = 1
            if ads != None and h2o != None:
                print('Checking ADS and H2O trap temperatures.')
                print(f'ADS must be {new_state["value"]}{ads}.')
                print(f'H2O trap must be {new_state["value"]}{h2o}.')
                def check():
                    measure = [self.ads.measure(), self.h2o.measure()]
                    return test(ads, measure[0]) and test(h2o, measure[1]), measure
            if ads != None and h2o == None:
                print(f'Checking that ads trap temperature is {new_state["value"]}{ads}.')
                def check():
                    measure = self.ads.measure()
                    return test(ads, measure), measure
            if ads == None and h2o != None:
                print('Checking that H2O trap temperature is {new_state["value"]}{h2o}.')
                def check():
                    measure = self.h2o.measure()
                    return test(h2o, measure), measure
            t0 = time.time()
            while check()[0]:
                txt = f"Currently measuring: {check()[1]}"
                remaining = round((t0 + timeout*60- time.time())/60, 2)
                txt += f" [timing out in {remaining} minutes]   "
                sys.stdout.write('\r')
                sys.stdout.write(txt)
                sys.stdout.flush()
                time.sleep(0.1)
                if time.time() > t0 + timeout*60:
                    self.state('off')
                    raise SystemError('System failed to reach temperature in time.')
            print('')
            print(f"Temperature threshold reached! Currently measuring {check()[1]}")

        ########## Timing Condition ##########
        if condition == 'time' and new_state['value'] > 0:
            print('Waiting to proceed.')
            dt = new_state['value']*60
            t0 = time.time()
            while time.time() < t0 + dt:
                t = time.time() - t0
                progressbar(i = t,
                            total = dt,
                            remaining = dt - t,
                            units='s',
                            interval = 'seconds')
                time.sleep(.2)
            progressbar(i=dt, total=dt, remaining=0, units='s', interval='seconds')

        self.current_state['name'] = name
        print('')
        return

    def check_sequence(self, name='standard.txt'):
        """
        check_sequence prints each state in a sequence file. This
        also provides a rudamentary check that the sequence file
        contain all the necessary fields and doesn't have any typos.
        """
        if type(name) is str:
            fname = f'src/Sample Sequencing/{name}'
            try:
                sequence, modified_date = read_sequence(fname)
            except json.decoder.JSONDecodeError as x:
                print(f'Unable to read file: {x}')
                return
        elif type(name) is list:
            sequence = name.copy()
            name = 'User Input Sequence'
            modified_date = datetime.now().strftime('%Y-%m-%d, %H:%M:%S')

        notes = f'Checking sequence {name}'
        notes += f', last modified: {modified_date}\n'
        notes += '\nList of states:\n'

        state_names = []
        name_warnings = ''
        timeout = 0
        for state in sequence:
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

        for state in sequence:
            try:
                block_print()
                self.state(state, check=True)
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
                
                valid_monitors = (None, 'ads', 'h2o', 'sample', 'backflush')
                try:
                    valid_monitors.index(monitor)
                except:
                    notes += f'Invalid monitor condition on {state["name"]}: {state["monitor"]}\n'

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
                else:
                    notes += f"Error: {state['name']} - {condition} is not a valid condition.\n"
            except Exception as x:
                notes += f"Error: Sequence fails on {state['name']}: {x}.\n"
                enable_print()
        if gc_flag:
            notes += 'Warning: this sequences does not trigger the GC.\n'

        if notes == start_notes:
            notes += 'No errors or warnings were detected.\n'
        if timeout == 0:
            notes += f'Run time of {round(run_time,2)} minutes.\n'
        else:
            notes += f'Run time of {round(run_time,2)} to {round(run_time+timeout,2)} minutes.\n'
        notes += f'{name} has {len(sequence)} states.\n'
        print(notes)
        
    def run_sequence(self, name=None, stream=None, notes=''):
        """
        """
        start_time = datetime.now().strftime('%Y, %m, %d, %H:%M:%S')
        folder = 'src/Sample Sequencing/'
        if name is None:
            files = os.listdir(folder)
            files.remove('log.csv')
            print('Sequences available to run.\n')
            for file in files:
                print(file)
            return
        
        fname = folder + str(name)
        if type(name) == str:
            sequence, modified_date = read_sequence(fname)
        else:
            sequence = name.copy()
            name = 'User Input Sequence'
            modified_date = datetime.now().strftime('%Y-%m-%d, %H:%M:%S')
        error_flag = False

        if stream != None:
            print(f'Selecting sample #{stream}.')
            self.stream(stream)
        else:
            stream = self.stream()

        notes = ""
        try:
            for state in sequence:
                result = self.state(state)
                if result != None:
                    notes += f'{state["name"]} returned: {result}. '
        except Exception as x:
            notes = f'Failed on {state["name"]}: {x}'
            error_flag = True
            print(notes)
        
        end_time = datetime.now().strftime('%H:%M:%S')
        notes = notes.replace('\n', '')
        log_entry = f'\n{start_time}, {end_time}, {name}'
        log_entry += f', {str(stream)}, {notes}, {modified_date}'
        with open('src/Sample Sequencing/log.csv', 'a') as file:
            file.write(log_entry)

        if error_flag:
            self.state('off')
            raise Exception(notes)

    def standard_run(self, flow=None, volume=None, temp=None, delay=None,
                     inject=None, blank=False, stream=None):
        ''' standard_run is a simple way to make small adjustments
        to the "standard.txt" run without needing to create a new file.
        This is to be used for repeated experiments that only need minor
        modifications to the standard procedure.
        '''
        if flow is None:
            flow = 100
        if volume is None:
            volume = 500
        if temp is None:
            temp = 300
        if inject is None:
            inject = 20
        if delay is None:
            delay = 0

        fname = f'src/Sample Sequencing/standard.txt'
        sequence, modified_date = read_sequence(fname)
        
        for n, state in enumerate(sequence):
            if state['name'] == 'flush':
                sequence[n]['value'] = 50/flow # set flush to purge 50 mL
                sequence[n]['sample'] = flow
            elif state['name'] == 'sampling':
                sequence[n]['value'] = volume/flow # volume/flowrate = time
            elif state['name'] == 'pre-backflush':
                if blank:
                    sequence[n]['backflush'] = flow
            elif state['name'] == 'backflush':
                if blank:
                    sequence[n]['value'] = volume/flow
            elif state['name'] == 'flash heat':
                sequence[n]['ads'] = temp
            elif state['name'] == 'inject':
                sequence[n]['value'] = inject/60
            elif state['name'] == 'bake out':
                bakeout_time = (120 - inject)/60
                if bakeout_time > 0:
                    sequence[n]['value'] = bakeout_time
                else:
                    sequence.remove(state)
                    
        if delay > 0:
            sequence[-1]['condition'] = 'time'
            sequence[-1]['value'] = delay
        
        if blank:
            for state in sequence.copy():
                if (state['name'] == 'flush') or (state['name'] == 'sampling'):
                    sequence.remove(state)
        
        with open('src/Sample Sequencing/custom.txt', 'w') as file:
            file.write(json.dumps(sequence))
        notes = f'flow={flow} volume={volume} temp={temp} inject={inject} blank={blank}'
        if stream is None:
            stream = [None]
        for index in stream:
            self.run_sequence(name='custom.txt', stream=index, notes=notes)
        
    def evacuate(self, stream=None):
        self.state('standby')
        if stream != None:
            if isinstance(stream, int):
                stream = [stream]
        else:
            stream = [self.stream()]

        for index in stream:
            self.stream(index)
            self.state('evacuate')
            self.state('standby')

        self.state('off')

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
    else:
        raise ValueError('Unrecognized logic operator.')


def read_sequence(name):
    try:
        with open(name) as file:
                data = file.read()
    except FileNotFoundError:
        name = f'{name}.txt'
        with open(name) as file:
                data = file.read()
    mod_time = os.path.getmtime(name)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d, %H:%M:%S')
    return json.loads(data), mod_date


def progressbar(i,
                total,
                remaining,
                units = '%',
                interval='minutes',
                size = 20):
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %s %s [%s %s remaining]     " %
                     ('='*int(i/total*size),
                      f'{i:.2f}', units, f'{remaining:.2f}', interval))
    sys.stdout.flush()

parser = argparse.ArgumentParser(description='Pre-concentration system command line interface.')

parser.add_argument('-r', '--run', action='store_true',
                    help='Activate the pre-concentration system to do a run.')
parser.add_argument('-f', '--flow', type=int,
                    help='Set the flowrate in milliliters per minute [sccm].')
parser.add_argument('-v', '--volume', type=int,
                    help='Set the sample size in milliliters [mL].')
parser.add_argument('-t', '--temp', type=int,
                    help='Set the trap heated temperature in celsius [°C].')
parser.add_argument('-i', '--inject', type=int,
                    help='Set the GC injection time in seconds [s].')
parser.add_argument('-b', '--blank', action='store_true',
                    help='Perform a blank run. Sample will not flow.')
parser.add_argument('-s', '--stream', type=int, nargs='+',
                    help='Select sample port.')
parser.add_argument('-p', '--purge', action='store_true',
                    help='Purge sample line.')
parser.add_argument('-n', '--repeat', type=int, default=1,
                    help='Repeat sequence *n* number of times.')
parser.add_argument('-d', '--delay', type=int, default=0,
                    help='Timed delay, in minutes, to occur after a sequence is complete.')
parser.add_argument('--sequence', type=str, default=None,
                    help='Run a specified sequence.')
parser.add_argument('-c', '--cli', action='store_true',
                    help='Enter command line interface for continuous operation.')
parser.add_argument('-l', '--log', action='store_true',
                    help='View the last 10 log entries.')

def cli(obj):
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
            print(f': {x}.')

if __name__ == '__main__':
    args = parser.parse_args()
    check = [args.purge, args.run, args.sequence!=None, args.log, args.cli]
    check = [x!=(None or False) for x in check]
    if sum(check) > 1:
        error_notes = 'Multiple methods called. Please select to only run (-r, --run), '
        error_notes += 'specify a sequence (--sequence), purge (-p, --purge), '
        error_notes += ',call the log (-l, --log), or enter the command line '
        error_notes += 'interface (-c, --cli).'
        raise SystemError(error_notes)
    elif sum(check) == 0:
        print('No methods called.')
    GPIO.setwarnings(False)
    pc = pre_con()
    GPIO.setwarnings(True)

    if args.cli:
        cli(pc)

    if args.purge:
        pc.evacuate(stream=args.stream)

    if args.run:
        for n in range(args.repeat):
            pc.standard_run(flow=args.flow,
                            volume=args.volume,
                            temp=args.temp,
                            inject=args.inject,
                            blank=args.blank,
                            stream=args.stream,
                            delay=args.delay)

    if args.sequence is not None:
        pc.run_sequence(args.sequence)

    if args.log:
        import csv
        fname = 'src/Sample Sequencing/log.csv'
        with open(fname, 'r') as file:
            log = file.read()
        print('Not yet implemented.')

