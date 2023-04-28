from serial import Serial
import json
import time
import sys 
import os
import RPi.GPIO as GPIO
from src.thermal_controller.omega_tc import omegatc
from src.uPy import uPy
from src.switch import switch
from src.remote import remote

def block_print():
    sys.stdout = open(os.devnull, 'w')

def enable_print():
    sys.stdout = sys.__stdout__



class pre_con:
    def __init__(self,
                 vc_port = '/dev/ttyACM0',
                 mfc_port = '/dev/ttyUSB2',
                 ads_trap_port = '/dev/ttyUSB0',
                 h2o_trap_port = '/dev/ttyUSB1',
                 debug=False):

        with open('src/precon_states') as file:
            data = file.read()
        self.states = json.loads(data)
        self.switch = switch(connected_obj=self)
        self._switch_state = self.switch.state
        self.remote = remote()
        if not debug:
            ##### Connect to Valve Controller #####
            self.vc = uPy(vc_port)
            block_print()
            check_VC = self.vc.echo('dir()')
            if not check_VC:
                self.vc.close()
                self.vc.connect()
                self.vc.reboot()
            enable_print()

            ##### Connect to Mass Flow Controller #####
            self.mfc = uPy(mfc_port)
            check = self.mfc.echo('dir()')
            if not check:
                print('Failed to connect to Mass Flow Controllers. Try a hardware reset.')
            self.mfc.sample = 0
            self.mfc.backflush = 1
            self.mfc.ports = self.mfc.echo('len(MFC)')
            self.mfc.timeout = self.mfc.echo('timeout')

            ##### Connect to ADS PID #####
            block_print()
            self.ads = omegatc(ads_trap_port)
            enable_print()
            if self.ads.connected:
                print('Successfully connected to adsorbent trap!')
            else:
                print('Failed to connect to adsorbent trap. :(')

#             ##### Connect to H2O PID #####
#             self.h2o = omegatc(h2o_trap_port)
#             if self.h2o.connected:
#                 print('Successfully connected to water trap!')
#             else:
#                 print('Failed to connect to water trap. :(')

        ##### Initial Machine States #####
            self.current_state = {}
            self.state('off')

            if not check_VC:
                self.vc = uPy(vc_port)
                check_VC = self.vc.echo('dir()')
                if not check_VC:
                    print('Failed to connect to Valve controller on second attempt.')
                    print('Check that both lights are lit on the board.')
                    print('Perform a hardware reset as necessary.')
                    txt = 'You will not need to restart the softare if you perform a'
                    txt += 'hardware reset and the valve controller lights up.'
                    print(txt)

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
            self.valve(range(0,8), pos)
            self.current_state['name'] = 'manual override'
            self.current_state['valves'] = pos[1:7]
            self.current_state['pump'] = pos[-1]


############### Code for Mass Flow controller ###############
    def flowrate(self, position = None, flowrate = None):
        if position == None:
            position = range(self.mfc.ports)
        else:
            position = [position]
        val = []
        for i in position:
            msg = 'MFC[{}].flowrate({})'.format(i, flowrate)
            val.append(self.mfc.echo(msg, timeout = self.mfc.timeout))
        return val

    def sampleFlow(self, flowrate=None):
        return self.flowrate(position=0, flowrate=flowrate)[0]

    def backflush(self, flowrate=None):
        return self.flowrate(position=1, flowrate=flowrate)[0]

############### Code for valve controller ###############
    def valve(self, V=None, position=None):
        if isinstance(V, int):
            check = self.vc.write(f'v[{V}]({position})')
            if V < 6:
                self.current_state['valves'][V] = position
            return check
        if isinstance(V, (list, range)):
            check = []
            for n, i in enumerate(V):
                if isinstance(position, int):
                    check.append(self.vc.write(f'v[{i}]({position})'))
                else:
                    check.append(self.vc.write(f'v[{i}]({position[n]})'))
            return check
        if V == None:
            if isinstance(position,list):
                check = []
                for i in range(6):
                    check.append(self.vc.write(f'v[{i}]({position[i]})'))
            return check

                    
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
            if self.valve(7, 0):
                self.current_state['pump'] = 'off'
            else:
                print('Failed to turn pump off.')

        elif (command == 'on') or (command == 1):
            if self.valve(7, 1):
                self.current_state['pump'] = 'on'
            else:
                print('Failed to turn on pump.')

        else:
            print('Invalid input, must be 0 or 1, or "off or "on". Use no input to return the current pump state.')


    def state(self, name = None, check = False, skip = False):
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
            for n, i in enumerate(state['valves']):
                string += f"Valve {str(n)}: {position[i]} \n"
            string += f"H2O Trap Temperature = {str(state['h2o'])}\n"
            string += f"ADS Trap Temperature = {str(state['ads'])}\n"
            string += f"Pump is {position[state['pump']]}\n"
            if state['condition'] == None:
                string += f"This state has no check following completion."
            else:
                string += f"With an advancement condition of '{state['condition']}' "
                string += f"set to {state['value']}."
            print(string)
            return

        ##### Checks if the function was called for information #####
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
            if check:
                print(f"Settings for the {name} state: \n")
                print_state(self.states[name])
                return

        ##### Engage the new state if a state change is requested. #####
        new_state = self.states[name].copy()
        condition = new_state['condition']
        if condition != None:
            condition = condition.lower()
        valid_conditions = [None, 'gc', 'pulse', 'time', 'temp']
        valid_conditions.index(condition) # Caused an error if an invalid condition is called.


        ########## GC Ready Condition ##########
        if condition=='gc':
            start = time.time()
            print('Waiting for GC to be ready.')
            while not self.remote.gc_ready:
                if time.time() > start + 60:
                    print('GC not ready in time. Aborting run.')
                    self.state('off')
                    print('System turned off.')
                    return False
            print('GC ready.')
            dt = new_state['value']
            if new_state['value'] == None:
                return True
            
        ########## Precision Timing Condition ##########
        if condition == 'pulse' or condition == 'gc':
            dt = new_state['value']
            v = new_state['valves']
            if sum(v) > 1:
                raise ValueError('More than 1 valve specified.')
            else:
                v = v.index(1)
            self.pulse(valve=v, sleep=dt)
            if condition == 'pulse':
                print(f'Precision timed pulse on valve {v}.')
            if condition == 'gc':
                print('Injecting sample.')
                self.remote.start()
            t0 = time.time()
            flow_check = []
            t = []
            while True:
                flow_check.append(self.sampleFlow())
                t.append(time.time()-t0)
                # Consider adding check if flowrate drops out.
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
                    print('System failure.')
                    self.state('off')
                    return
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
            if condition == 'pulse':
                return t, flow_check
            else:
                return True
        
        
        valves = new_state['valves']
        self.valve(position=valves)
        pump = new_state['pump']
        self.pump(pump)
        sample = new_state['sample']
        backflush = new_state['backflush']
        if sample != None:
            if sample == 0:
                print('Sample flow disabled.')
            else:
                print(f'Setting sample flow rate to {sample}. Please wait for flow to stabilize.')
            self.sampleFlow(sample)
        if backflush != None:
            if backflush == 0:
                print('Backflush flow disabled.')
            else:
                print(f'Setting backflush flow rate to {backflush}. Please wait for flow to stabilize.')
            self.backflush(backflush)

        ads = new_state['ads']
        h2o = new_state['h2o']
        h2o = None #comment out when h2o trap implemented
        if condition != 'temp':
#             if h2o != None:
#                 self.h2o.set_point(h2o)
            if ads != None:
                self.ads.set_point(ads)

        ########## Temperature Condition ##########
        if condition == 'temp':
            logic = new_state['value']
            def test(a, b):
                if logic == '<':
                    return a < b
                elif logic == '>':
                    return a > b
                elif logic == '==':
                    return a == b
                elif logic == '>=':
                    return a >= b
                elif logic == '<=':
                    return a <= b

            if ads != None and h2o != None:
                print('Checking both ads and h2o trap temperatures.')
                def check():
                    measure = [self.ads.measure(), self.h2o.measure()]
                    return test(ads, measure[0]) and test(h2o, measure[1]), measure
            if ads != None and h2o == None:
                print('Checking ads trap temperature.')
                def check():
                    measure = self.ads.measure()
                    return test(ads, measure), measure
            if ads == None and h2o != None:
                print('Checking h2o trap temperature.')
                def check():
                    measure = self.h2o.measure()
                    return test(h2o, measure), measure
            t0 = time.time()
            while check()[0]:
                txt = f"Waiting for temperature. Currently measuring: {check()[1]}"
                remaining = round((t0 + 15*60- time.time())/60,2)
                txt += f" [timing out in {remaining} minutes]"
                sys.stdout.write('\r')
                sys.stdout.write(txt)
                sys.stdout.flush()
                time.sleep(1)
                if time.time() > t0 + 15*60:
                    print('System failed to reach temperature in time.')
                    self.state('off')
                    raise SystemError('System was shut down.')
            print('')
            print(f"Temperature threshold reached! Currently measuring {check()[1]}")

        ########## Timing Condition ##########
        if condition == 'time':
            print('Waiting to proceed.')
            dt = new_state['value']*60
            t0 = time.time()
            if not skip:
                while time.time() < t0 + dt:
                    t = time.time() - t0
                    progressbar(i = t,
                                total = dt,
                                remaining = dt - t,
                                units='s',
                                interval = 'seconds')
                    time.sleep(.2)
                progressbar(i=dt, total=dt, remaining=0, units='s', interval='seconds')

        self.current_state = new_state
        self.current_state['name'] = name
        print('')
        return

    def run_sa(self, stream=None, sample=None):
        if sample != None:
            sa_name = 'sampling ' + sample
            self.state(sa_name, check=True)
            print('This feature has not been implemented.')
            return

        ########## Standby ##########
        print('Beginning micro-trap sampling sequence.')
        self.state('standby')
        print('System being evacuated.')
        if stream != None:
            print(f'Selecting sample #{stream}.')
            self.stream(stream)
        else:
            stream = self.stream()
        print('Waiting for traps to reach trapping temperature.')
        self.state('cool down')

        print('Traps ready! Flushing system with sample.')
        while pc.stream() != stream:
            time.sleep(.1)
        self.state('flush')

        print('Beginning sampling')
        self.state('sampling')

        print('Preparing to backflush.')
        self.state('pre-backflush')

        print('Beginning backflush')
        self.state('backflush')

        print('Check GC status prior to heating.')
        self.state('pre-heat')

        print('Flash heating trap.')
        self.state('flash heat')

        print('Injecting Sample')
        self.state('inject')

        print('Beginning bakeout')
        self.state('bake out')
        
        print('Beginning post-back evacuation.')
        self.state('post bake')
        
        print('Returning to standby')
        self.state('standby')

    def run_loop(self, stream=None, flow=25, delay=5):
        ##### Flush #####
        print('Beginning loop sample injection sequence.')
        self.state('standby')
        print('System being evacuated.')
        if stream != None:
            self.stream(stream)
        time.sleep(5)

        ##### Load #####
        print('Initializing sample flow.')
        self.sampleFlow(flow)
        self.state('loop sample')
        if self.sampleFlow(flow):
            print('Sample flushing the system.')
        else:
            print('MFC failed to regulate sample. Aborting run.')
            self.sampleFlow(0)
            self.state('off')
            return

        ##### Flush loop #####
        start = time.time()
        while not self.remote.gc_ready or (start + delay > time.time()):
            if time.time() > start + 360:
                print('GC not ready. Aborting run.')
                self.sampleFlow(0)
                self.state('off')
                print('System turned off.')
                return

        ##### Inject #####
        print('Injecting sample')
        self.pulse(valve=0, sleep=20)
        self.remote.start()
        print('Sample injected. MFC disabled.')
        self.sampleFlow(0)

        ##### Shut off #####
        time.sleep(20)
        print('Disabling pre-concentration system.')
        self.state('off')

def progressbar(i,
                total,
                remaining,
                units = '%',
                interval='minutes',
                size = 20):
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %s %s [%s %s remaining]" %
                     ('='*int(i/total*size),
                      f'{i:.2f}',
                      units,
                      f'{remaining:.2f}',
                      interval))
    sys.stdout.flush()

if __name__ == '__main__':
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setwarnings(True)
    pc = pre_con()
