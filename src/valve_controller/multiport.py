from machine import Pin
import time

class multiport:
    def __init__(self, maxPosition=None, inPins = None, outPins = None, enPin = None):
        if maxPosition is None:
            self.maxPosition = 16
        self.o = []
        self.i = []
        if inPins is None:
            self.inPins = [35, 34, 39, 36, 18] # 1s, 2s, 4s, 8s, 10s
        for i in self.inPins:
            self.i.append(Pin(i, Pin.IN))        
        if outPins is None:
            self.outPins = [2, 15, 16, 4, 5] # 1s, 2s, 4s, 8s, 10s
        for i in self.outPins:
            if i==2:
                self.o.append(Pin(i, Pin.OUT, value = 1))
            else:
                self.o.append(Pin(i, Pin.OUT, value = 0))
        if enPin is None:
            self.enPin = Pin(17, Pin.OUT, value = 0)
        else:
            self.enPin = Pin(enPin, Pin.OUT, value = 0)
        #self.step()

    def actuate(self, val):
        if (val<1 or val>self.maxPosition): #Error checking for values outside of the range
            print('Input outside of range.')
            return
        self.enPin(0)
        self.setpos(val)
        self.enPin(1)
        
        pos = self.readpos()
        start_time = time.time()
        while pos!=val:
            pos = self.readpos()
            time.sleep(0.1)
            if (time.time()-start_time)>10:
                print('Failed to reach position in time')
                break
        self.enPin(0)
        self.setpos(1)
  
    def readpos(self): #Reads the position and returns it as an output
        pos = 0
        multiplier = [1, 2, 4, 8, 10]
        for i, p in enumerate(self.i):
            pos = pos + float(not(p.value()))*multiplier[i]
        return pos
    
    def step(self, stepSize = 1):
        val = self.readpos()
        if (val+stepSize) > self.maxPosition:
            target = 1
        else:
            target = val + stepSize
        print(target)
        self.actuate(target)
        
    def home(self):
        self.actuate(1)

    def setpos(self, val):
        multiplier = [10, 8, 4, 2, 1]
        tempVal = val
        for idx, i in enumerate(multiplier):
            if tempVal>=i:
                self.o[4-idx](1)
                tempVal = tempVal - i
            else:
                self.o[4-idx](0)
                