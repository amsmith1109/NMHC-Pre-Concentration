# esptool -p COM8 erase_flash
# esptool --port COM8 --baud 460800 write_flash --flash_size=detect -fm dout 0 ESP8266_GENERIC-20240105-v1.22.1.bin

from machine import Pin, PWM, ADC
from math import floor
import time

_timeout = 150 # 2.5 minutes to timeout
_dt = 0.1
_threshold = 30
led = Pin(2, Pin.OUT, value=1)      # D4
debug = Pin(4, Pin.IN, Pin.PULL_UP) # D2
out_pin = Pin(14, Pin.OUT, value=0) # D5
enable = Pin(12, Pin.OUT, value=1)  # D6
in_pin = ADC(0)                     # A0
pwm = PWM(out_pin, freq=200, duty=0)

def main():
    print('Ground GPIO4 (D2) on startup to enter debug mode.')
    if not debug.value():
        print('Debugging.')
    else:
        print('Running PWM.')
        enable(0)
        led(0)
        runtime = 0
        while True:
            v = in_pin.read()
            if v > _threshold:
                runtime += _dt
                pwm.duty(floor(v/2))
            else:
                pwm.duty(0)
                runtime -= _dt
                if runtime < 0:
                    runtime = 0
            if runtime > _timeout:
                enable(1)
                led(1)
                system_timeout()
                print('returned')
                runtime = 0
            time.sleep(_dt)

def system_timeout():
    print('timed out')
    time.sleep(_timeout)
    led(0)
    print('wait finished')
    while in_pin.read() > _threshold:
        pass
    print('reset')
    enable(0)

if __name__ == '__main__':
    main()
