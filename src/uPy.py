from serial import Serial
import time
import signal


class uPy:
    def __init__(self,
                 port,
                 baudrate=115200,
                 timeout=0.2):
        self.serial = Serial(port, baudrate=baudrate, timeout=timeout)
        self.port = port
        # Enter normal REPL mode
        self.connect()
        signal.signal(signal.SIGINT, self.signal_handler)

    def connect(self):
        if(self.serial.isOpen() == False):
            self.serial.open()
        self.interrupt()
        self.normal_mode()

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
        result = self.read(message.__len__())
        if result == message:
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


    def readline(self, timeout=None):
        if timeout==None:
            timeout = self.serial.timeout
        result = ''
        t = time.time()
        while True:
            if self.serial.in_waiting > 0:
                result += self.read(1)
                t = time.time()
                if result[-2:] == '\r\n':
                    break
            else:
                if (time.time()) > (t + timeout):
                    return False
        return result


    def echo(self, msg, timeout=None):
        if timeout==None:
            timeout = self.serial.timeout
        self.write(msg)
#         try:
#             self.write(msg)
#         except Exception as x:
#             if type(x)
        result = ''
        t = time.time()
        while True:
            if self.serial.in_waiting > 0:
                result += self.read(1)
                t = time.time()
                if result[-4:]  == '>>> ': #check for repl terminator
                    break
            else:
                if (time.time()) > (t + timeout):
                    raise TimeoutError('Device timed out.')
        error_check = [x for x in error_types if (x in result)]
        if len(error_check) > 0:
            index = result.find(error_check[0]) + len(error_check[0]) + 2
            result = result[index:]
            result = result.strip('\r\n')
            raise eval(error_check[0])(f'{result} (from uPy device)')
        result = result[1:]
        result = result.strip('\r\n')
        result = result.strip('>>> ')
        try:
            if result == '':
                return
            return eval(result)
        except:
            return result

    def close(self):
        self.write('\x01')
        self.serial.close()

    def normal_mode(self):
        self.write('\x02')

    def interrupt(self):
        self.write('\x03')

    # Software reboot. Note that this only works IF the device is accepting
    # commands over serial.
    def reboot(self):
        self.read()
        self.write('\x04')
        t = time.time()
        timeout = 5
        while self.serial.in_waiting==0:
            if time.time() > t + timeout:
                raise SystemError('Device unresponsive.')
        result = ''
        t = time.time()
        while True:
            if self.serial.in_waiting > 0:
                result += self.read(1)
                t = time.time()
                if result[-13:]  == 'soft reboot\r\n': #check for repl terminator
                    break
            else:
                if (time.time()) > (t + timeout):
                    raise SystemError('Device timed out.')

    def escape(self):
        self.write('\x1b')

    def signal_handler(sig, frame):
        self.close()
        sys.exit(0)

    def timeout_handler(self):
        try:
            self.echo('dir()')
        except:
            raise SystemError('Device timed out.')

error_types = ('TypeError', 'SyntaxError', 'NameError', 'ValueError',
               'AttributeError', 'IndexError', 'ZeroDivisionError',
               'KeyError', 'RuntimeError', 'AssertionError', 'EOFError',
               'IndentationError', 'MemoryError', 'SystemError', 'OSError',
               'ArithmeticError', 'OverflowError', 'FloatingPointError',
               'NotImplementedError', 'UnicodeDecodeError', 'ReferenceError',
               'IOError')

if __name__=='__main__':
    port = '/dev/ttyACM0'
    dev = uPy(port)
    dev.echo('dir()')
