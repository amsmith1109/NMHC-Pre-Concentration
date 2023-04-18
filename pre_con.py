from serial import Serial
import json
import time
import sys, os

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def enablePrint():
    sys.stdout = sys.__stdout__
    
from src.thermal_controller.omega_tc import omegatc
from src.uPy import uPy
from src.switch import switch

class pre_con:
    def __init__(self,
                 vc_port = '/dev/ttyACM0',
                 mfc_port = '/dev/ttyUSB0',
                 ads_trap_port = '/dev/ttyUSB1',
                 h2o_trap_port = '/dev/ttyUSB2'):
        
        ##### Connect to Valve Controller #####
        self.vc = uPy(vc_port)        
        check = self.vc.echo('dir()')
        if check==False:
            self.vc.write('\x01')
            if self.vc.readline()==False:
                print('Failed to connect to valve controller. Try a hardware reset.\n')
            else:
                self.vc.reboot()
                
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
            
        self.current_state = {'valves':    [0,0,0,0,0,0],
                              'h2o':       25,
                              'ads':       25,
                              'sampleMFC': 0,
                              'carrierMFC':0,
                              'pump':      0,
                              'time':      0}
        self.switch = switch(connected_obj=self)
        self._switch_state = self.switch.state
        
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
            val.append(self.mfc.echo('MFC[{}].flowrate({})'.format(i, flowrate),
                                  timeout = self.mfc.timeout))
        return val
    
    def sampleFlow(self, flowrate=None):
        return self.flowrate(position=0, flowrate=flowrate)
    
    def carrierFlow(self, flowrate=None):
        return self.flowrate(position=1, flowrate=flowrate)
       
############### Code for valve controller ###############
    def valve(self, V, position):
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
            
    def home_valves(self):
        self.valve(range(0,8),0)
        
    def stream(self, position=None):
        if position==None:
            val = self.vc.echo('m.readpos()')
            print(val)
        elif isinstance(position, int):
            self.vc.write(f'm.actuate({position})')
        elif isinstance(position, str):
            if position.lower()=='home':
                self.vc.write('m.home()')
            elif position.lower()=='step':
                self.vc.write('m.step()')
            else:
                print('Invalid stream select command. Use "home" or "step".')
        else:
            raise(ValueError)
        
    def step(self):
        self.vc.write(f'm.step()\r')
            
    def pump(self, command = None):
        if command == None:
            print(f"The pump is currently turned {self.current_state['pump']}.")
            
        elif (command =='off') or (command == 0):
            check = self.valve(7, 0)
            if check:
                self.current_state['pump'] = 0
            else:
                print('Failed to turn on pump.')
            
        elif (command == 'on') or (command == 1):
            check = self.valve(7, 1)
            if check:
                self.current_state['pump'] = 1
            else:
                print('Failed to turn on pump.')
            
        else:
            print('Invalid input, must be 0 or 1, or "off or "on". Use no input to return the current pump state.')


    def state(self, name = None):
        # Import the file precon_states where each system state
        # is defined by the file.
        with open('src/precon_states') as f:
            data = f.read()
        states = json.loads(data)
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
            string = 'Current state of the system: \n'
            for n, i in enumerate(self.current_state['valves']):
                string += 'Valve ' + str(n) + ': ' + position[i] + '\n'
            string += f"H2O Trap Temperature = {str(self.current_state['h2o'])}"+'\n'
            string += f"ADS Trap Temperature = {str(self.current_state['ads'])}"+'\n'
            string += f"Pump is {position[self.current_state['pump']]}"
            print(string)
            return
            
        try:
            new_state = states[name.lower()]
        except KeyError:
            print(f'State "{name}" name does not exist!')
            print(state_help())
            return
                
        valve = []
        position = []
        h2o = None
        ads = None
        
        # Determine which valves need to be rotated, and if
        # any temperature settings need to change.
        for n, i in enumerate(new_state['valves']):
            if i != self.current_state['valves'][n]:
                valve.append(n)
                position.append(i)
        if self.current_state['h2o'] != new_state['h2o']:
            h2o = new_state['h2o']
        if self.current_state['ads'] != new_state['ads']:
            ads = new_state['ads']
        if self.current_state['pump'] != new_state['pump']:
            self.pump(new_state['pump'])
            
            
        # Execute commands
        if valve != []:
            self.valve(valve, position)
        if h2o != None:
            None #remove when implemented
#            self.h2o.set_point(h2o)
        if ads != None:
            None #remove when implemented
#            self.ads.set_point(ads)
        
        self.current_state = new_state
        return new_state['time']

    def run(self):
            print('Entering standby mode.')
            t = pc.state('standby')
            time.sleep(t)
            
            print('Entering cool down mode.')
            t = pc.state('cool down')
            time.sleep(t)
            
            print('Beginning sampling.')
            t = pc.state('sampling')
            time.sleep(t)
            
            print('Backflushing adsorbent trap.')
            t = pc.state('backflush')
            time.sleep(t)
            
            print('Flash heating trap.')
            t = pc.state('flash heat')
            time.sleep(t)
            
            print('Injecting sample to the GC.')
            t = pc.state('inject')
            time.sleep(t)
            
            print('Begin analysis - sample is on the GC.')
            t = pc.state('analysis')
            time.sleep(t)
            
            print('Beginning bake out of both traps.')
            t = pc.state('bake out')
            time.sleep(t)
            
            print('Purging ads and water trap.')
            t = pc.state('purge')
            time.sleep(t)
            
            
            print('Shutting off.')
            t = pc.state('off')
            time.sleep(t)

if __name__ == '__main__':
    pc = pre_con()
    #pc.valve(range(0,8),1)
    #ads = pc.h2o_trap
    

    ## Rotate valves
    
    # Perform a rotation individually
    #pc.valve(0,0)
    
    # Or do them all at once by passing a list or range
    #pc.valve([1,2],0)
    #pc.valve(range(3,8),0)
    
    # There is also a built in macro to home all of them
    # This is equivalent to .valve(range(0,8),0)
    #pc.home_valves()