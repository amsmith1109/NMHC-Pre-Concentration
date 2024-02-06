# esptool -p COM8 erase_flash
# esptool --port COM8 --baud 460800 write_flash --flash_size=detect -fm dout 0 ESP8266_GENERIC-20240105-v1.22.1.bin

from machine import Pin, PWM, ADC
from math import floor

def main():
    led = Pin(2, Pin.OUT, value=1)      # D4
    debug = Pin(4, Pin.IN, Pin.PULL_UP) # D2
    out_pin = Pin(14, Pin.OUT, value=0) # D5
    enable = Pin(12, Pin.OUT, value=1)  # D6
    in_pin = ADC(0)                     # A0
    pwm = PWM(out_pin, freq=200, duty=0)
    print('Ground GPIO4 (D2) on startup to enter debug mode.')
    if not debug.value():
        print('Debugging.')
    else:
        print('Running PWM.')
        enable(0)
        while True:
            v = in_pin.read()
            if v > 50:
                pwm.duty(floor(v/2))
            else:
                pwm.duty(0)
            if v > 1000:
                led(0)
            else:
                led(1)

if __name__ == '__main__':
    main()