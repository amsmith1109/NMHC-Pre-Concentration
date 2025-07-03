import signal
import sys
import RPi.GPIO as GPIO


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


class switch:
    def switch_detected(self, channel):
        idx = self.pin_list.index(channel)
        name = self.keys[idx]
        new_value = GPIO.input(channel)
        self.state[name] = new_value
        if self.connected_obj is not None:
            self.connected_obj.switch_state = self.state

    def __init__(self,
                 enable=6,   # Pin 31
                 v0=13,      # Pin 33
                 v1=19,      # Pin 35
                 v2=26,      # Pin 37
                 v3=12,      # Pin 32
                 v4=16,      # Pin 36
                 pump=20,    # Pin 38
                 debug=21,   # Pin 40
                 connected_obj=None):
        pins = {'enable': enable, 'V0': v0, 'V1': v1, 'V2': v2,
                'V3': v3, 'V4': v4, 'pump': pump, 'debug': debug}
        self.pins = pins
        self.keys = [x for x in pins.keys()]
        self.pin_list = [x for x in pins.values()]
        self.state = {}
        self.connected_obj = connected_obj

        GPIO.setmode(GPIO.BCM)
        for n, i in enumerate(self.pin_list):
            GPIO.setup(i, GPIO.IN)
            GPIO.add_event_detect(i,
                                  GPIO.BOTH,
                                  callback=self.switch_detected,
                                  bouncetime=20)
            self.state[self.keys[n]] = GPIO.input(i)

        signal.signal(signal.SIGINT, signal_handler)

    def poll(self, pin):
        if isinstance(pin, str):
            name = pin
            pin = self.keys.index(pin)
        if isinstance(pin, int):
            name = self.keys[pin]
            pin = self.pin_list[pin]
        else:
            raise TypeError('Invalid pin input, must be pin name (str) or index (int)')
        self.switch_detected(pin)
        return self.state[name]

if __name__ == '__main__':
    sw = switch()
