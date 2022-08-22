from serial import Serial
from thermal_controller.omega_tc import omegatc
from uPy import uPy
import json

class pre_con:
    def __init__(self,
                 vc_port = '/dev/ttyACM0',
                 mfc_port = '/dev/ttyUSB2',
                 ads_trap_port = '/dev/ttyUSB0',
                 h2o_trap_port = '/dev/ttyUSB1'):
        
        # It is very important that the USB configuration matches the usb ports
        # Improvements should be made to automatically determine where each
        # device is actually located. The ESP32 & ESP8266 can easily be programmed
        # to respond some form of identifier.
        self.vc_port = vc_port
        self.mfc_port = mfc_port
        self.ads_trap_port = ads_trap_port
        self.h2o_trap_port = h2o_trap_port
        
        self.vc = uPy(vc_port)
        self.mfc = uPy(mfc_port)
        #self.ads = omegatc(ads_trap_port)
        #self.h2o = omegatc(h2o_trap_port)
        self.current_state = {'valves': [0,0,0,0,0,0],
                              'h2o':    25,
                              'ads':    25,
                              'time':   0}
        
############### Code for valve controller ###############
    def valve(self, V, position):
        if isinstance(V, int):
            self.vc.write(f'v[{V}]({position})\r')
        elif isinstance(V, list) or isinstance(V, range):
            for n, i in enumerate(V):
                if isinstance(position, int):
                    self.vc.write(f'v[{i}]({position})\r')
                else:
                    self.vc.write(f'v[{i}]({position[n]})\r')
        
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
            
    def state(self, name = None):
        # Import the file precon_states where each system state
        # is defined by the file.
        with open('precon_states') as f:
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
        elif name == 'print':
            position = ['off', 'on']
            string = 'Current state of the system: \n'
            for n, i in enumerate(self.current_state['valves']):
                string += 'Valve ' + str(n) + ': ' + position[i] + '\n'
            string += 'H2O Trap Temperature = ' + str(self.current_state['h2o']) + '\n'
            string += 'ADS Trap Temperature = ' + str(self.current_state['ads'])
            print(string)
            return
            
        
        try:
            new_state = states[name.lower()]
        except KeyError:
            print('State name does not exist!')
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
            h2o = new_state['ads']
            
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
        
        
if __name__ == '__main__':
    pc = pre_con()
    #pc.valve(range(0,8),1)
    #ads = pc.h2o_trap
    v = pc.vc
    pc.state('print')
    ## Rotate valves
    
    # Perform a rotation individually
    #pc.valve(0,0)
    
    # Or do them all at once by passing a list or range
    #pc.valve([1,2],0)
    #pc.valve(range(3,8),0)
    
    # There is also a built in macro to home all of them
    # This is equivalent to .valve(range(0,8),0)
    #pc.home_valves()