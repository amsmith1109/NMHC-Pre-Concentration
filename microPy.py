from serial import Serial

class uPy:
    def __init__(self, obj):
        serial = obj
        
    def write(self, message):
        message = str(message)
        self.serial.write(message + '\n\r')