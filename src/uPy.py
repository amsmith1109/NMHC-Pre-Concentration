from serial import Serial
import time

class uPy:
    def __init__(self,
                 port,
                 baudrate=115200,
                 timeout=0.05):
        self.serial = Serial(port, baudrate=baudrate, timeout=timeout)
        if(self.serial.isOpen() == False):
            self.serial.open()
        
    def write(self, message):
        # convert input to byte string
        
        if isinstance(message, str):
            msg = message.encode('utf-8')
        elif isinstance(message, bytes):
            msg = message
        elif isinstance(message, float) or isinstance(message, int):
            msg = str(message).encode('utf-8')
        else:
            print('Invalid input variable type.')
        
        # add carriage return if it doesn't exist
        if msg[-1] != b'\r': 
            msg = msg + b'\r'
        
        #clear serial buffer
        self.read() 
        # Write to serial
        self.serial.write(msg)
        t = time.time()
        while self.serial.in_waiting < msg.__len__():
            if time.time() > t + self.serial.timeout:
                break
        check = self.read(message.__len__())
        if message==check:
            return True
        else:
            return False
        
        
    def read(self, n=None):
        if n==None:
            msg = self.serial.readall()
        elif isinstance(n,int):
            msg = self.serial.read(n)
        msg = msg.decode('utf-8')
        return msg
    
    def echo(self, msg, timeout=None):
        if timeout==None:
            timeout = self.serial.timeout
        self.write(msg)
        check = ''
        t = time.time()
        while True:
            if self.serial.in_waiting > 0:
                check += self.read(1)
                t = time.time()
                if check[-4:]  == '>>> ': #check for repl terminator
                    break
            else:
                if (time.time()) > (t + timeout):
                    return False
        check = check[2:]
        stop = check.find('\r>>>')
        try:
            return eval(check[:stop])
        except:
            print(check[:-4])
            return(check[:-4])
            
    
    # Software reboot. Note that this only works IF the device is accepting
    # commands over serial.
    def reboot(self):
        self.write('\x04')
    
    def escape(self):
        self.write('\x1b')
        
if __name__=='__main__':
    vc = uPy('/dev/ttyACM0')
    vc.write('b = 2**16')
    a = vc.echo('b')
    print(a)