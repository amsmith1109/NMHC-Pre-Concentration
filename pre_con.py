from serial import Serial
import json
import time
import sys, os
import RPi.GPIO as GPIO


def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def enablePrint():
    sys.stdout = sys.__stdout__
    
from src.thermal_controller.omega_tc import omegatc
from src.uPy import uPy
from src.switch import switch
from src.remote import remote

class pre_con:
    def __init__(self,
                 vc_port = '/dev/ttyACM0',
                 mfc_port = '/dev/ttyUSB0',
                 ads_trap_port = '/dev/ttyUSB1',
                 h2o_trap_port = '/dev/ttyUSB2'):
        
        ##### Connect to Valve Controller #####
        self.vc = uPy(vc_port)       
        blockPrint() 
        checkVC = self.vc.echo('dir()')
        if checkVC == False:
            self.vc.close()
            self.vc.connect()
            self.vc.reboot()
        enablePrint()
                
        ##### Connect to Mass Flow Controller #####
        self.mfc = uPy(mfc_port)
        check = self.mfc.echo('dir()')
        if check==False:
            print('Failed to connect to Mass Flow Controllers. Try a hardware reset.')
        self.mfc.sample = 0
        self.mfc.backflush = 1
        self.mfc.ports = self.mfc.echo('len(MFC)')
        self.mfc.timeout = self.mfc.echo('timeout')
        
        ##### Connect to ADS PID #####
        blockPrint()
        self.ads = omegatc(ads_trap_port)
        enablePrint()
        if self.ads.connected:
            print('Successfully connected to adsorbent trap!')
        else:
            print('Failed to connect to adsorbent trap. :(')
            
        ##### Connect to H2O PID #####
#         self.h2o = omegatc(h2o_trap_port)
#         if self.h2o.connected:
#             print('Successfully connected to water trap!')
#         else:
#             print('Failed to connect to water trap. :(')

        ##### Initial Machine States #####
        with open('src/precon_states') as f:
            data = f.read()
        self.states = json.loads(data)    
#         self.current_state = {'valves':    [0,0,0,0,0,0],
#                               'h2o':       25,
#                               'ads':       25,
#                               'sampleMFC': 0,
#                               'carrierMFC':0,
#                               'pump':      0,
#                               'time':      0}
        self.current_state = {}
        self.state('off')
        self.switch = switch(connected_obj=self)
        self._switch_state = self.switch.state
        self.remote = remote()
        
        if not checkVC:
            self.vc = uPy(vc_port)
            checkVC = self.vc.echo('dir()')
            if checkVC==False:
                print('Failed to connect to Valve controller on second attempt.')
                print('Check that both lights are lit on the board.')
                print('Perform a hardware reset as necessary.')
        
    @property
    def switch_state(self):
        return self._switch_state
        
    @switch_state.setter
    def switch_state(self, newState):
        self._switch_state = newState
        self.manual_override()
        
    def manual_override(self):
        if self.switch.state['enable']:
            positions = [x for x in self.switch.state.values()]
            pos = positions[1:-1]
            pos.append(0)
            pos.append(positions[-1])
            self.valve(range(0,8), pos)
       
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
        elif isinstance(V, list) or isinstance(V, range):
            check = []
            for n, i in enumerate(V):
                if isinstance(position, int):
                    check.append(self.vc.write(f'v[{i}]({position})'))
                    if n < 6:
                        self.current_state['valves'][i] = position
                else:
                    check.append(self.vc.write(f'v[{i}]({position[n]})'))
                    if n < 6:
                        self.current_state['valves'][i] = position[n]
            return check
        elif V == None:
            if isinstance(position,list):
                check = []
                for i in range(6):
                    check.append(self.vc.write(f'v[{i}]({position[i]})'))
    
    
    def pulse(self, valve, sleep):
        if not isinstance(valve, int):
            raise ValueError('Selected valve must be an integer.')
        if valve > 8 or valve < 0:
            raise ValueError('Selected valve outside acceptable range.')
        if not (isinstance(sleep, int) or isinstance(sleep, float)):
            raise ValueError('Sleep time must be a number.')
                
        return self.vc.write(f'pulse(v[{valve}],sleep={time})')
    
    
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
            
        elif (command =='off') or (command == 0):
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


    def state(self, name = None):
        def state_help():
            string = 'You may use one of the following keys: '
            for i in states.keys():
                string += i + ', '
            string = string[:-2] + '.'
            return string
        
        if name == 'help':
            print(state_help())
            return
        elif name == None:
            position = ['off', 'on']
            string = 'The pre-concentration system is currently in the '
            string += f"{self.current_state['name']} state: \n"
            for n, i in enumerate(self.current_state['valves']):
                string += 'Valve ' + str(n) + ': ' + position[i] + '\n'
            string += f"H2O Trap Temperature = {str(self.current_state['h2o'])}"+'\n'
            string += f"ADS Trap Temperature = {str(self.current_state['ads'])}"+'\n'
            string += f"Pump is {position[self.current_state['pump']]}"
            print(string)
            return
            
        new_state = self.states[name]
        condition = new_state['condition']
        
        if condition == 'pulse':
            dt = new_state['value']
            v = new_state['valve'].index(1)
            self.pulse(valve=v, sleep=dt)
            t0 = time.time()
            flow_check = []
            t = []
            while True:
                flow_check.append(self.sampleFlow())
                t.append(time.time())
                # Consider adding check if flowrate drops out.
                elapsed = t[-1] - t0
                if self.vc.serial.in_waiting > 9:
                    msg = self.vc.read()
                    if msg[2:4] == 'ok':
                        progressbar(i = dt, total = dt, remaining=0, units='s', interval = 's')
                if elapsed >= dt + 20:
                    print('System failure.')
                    self.state('off')
                    return
                else:
                    progressbar(i = elapsed, total = dt, remaining = (dt-elapsed), units='s', interval = 's')
                time.sleep(0.25)
            return t, flow_check
            
        if condition=='gc':
            start = time.time()
            while not self.remote.gc_ready or (start + delay > time.time()):
                if time.time() > start + 60:
                    print('GC not ready in time. Aborting run.')
                    self.state('off')
                    print('System turned off.')
                    return False
            dt = new_state['value']
            self.pulse(valve=v, sleep=dt)
            if dt != None:
                v = new_state['valve'].index(1)
                self.remote.start()
            return True
            
        valves = new_state['valves']
        self.valve(position=valves)
        
        sample = new_state['sample']
        backflush = new_state['backflush']
        if sample != None:
            self.sampleFlow(sample)
        if backflush != None:
            self.backflush(backflush)
        
        ads = new_state['ads']
        h2o = new_state['h2o']
#         if h2o != None:
#             h2o.set_point = h2o
        if ads != None:
            ads.set_point = ads
        
        if condition == None:
            return
        
        elif condition == 'temp':
            t0 = time.time()
            temp = ads.measure()
            if ads != None and h2o != None:
                def check():
                    return (ads < self.ads.measure()) and (h2o < self.h2o.measure())
            if ads != None and h2o == None:
                def check():
                    return ads < self.ads.measure()
            if ads == None and h2o != None:
                def check():
                    return h2o < self.h2o.measure()
            while check():
                time.sleep(1)
                if time.time() > t0 + 15*60:
                    print('System failed to reach temperature in time.')
                    self.state('off')
                    raise SystemError('System was shut down.')
        elif condition == 'time':
            time.sleep(new_state['value'])
        
        self.current_state = new_state
        self.current_state['name'] = name.lower()
        return

    def run_sa(self, stream=None, sample='normal'):
        ########## Standby ##########
        print('Beginning micro-trap sample injection sequence.')
        self.state('standby')
        print('System being evacuated.')
        if stream != None:
            print(f'Selecting sample #{stream}.')
            self.stream(stream)
        else:
            stream = self.stream()
            
        print('Flushing system with sample.')    
        self.state('pre-flush')
        while pc.stream() != stream:
            time.sleep(.1)
        self.state('flush')
        
        print('Beginning sampling')
        self.state('sampling')
        print('Sampling completed, beginning backflush.')
        self.state('pre-backflush')
        self.state('backflush')
        self.state('pre-heat')
        self.state('flash-heat')
        self.state('inject')
        self.state('bakeout')
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
    pc = pre_con()
    