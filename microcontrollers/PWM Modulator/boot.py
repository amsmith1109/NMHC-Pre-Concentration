''' Simple PWM modulator for controlling the battery output.
Input voltage is provided by analog PID controller (0 - 12 V)
Output voltage activates a 40 A Solid-state relay (SSR)

The program uses a while True loop to run continuously and is
not meant to be interrupted while powered. Use the keyboard
interrupt Ctrl+C in REPL to interrupt the program.

Created by: Alex Smith
Last revised: Jul-4th-2023
email: alsmit2@pdx.edu
'''

import machine

Vin = machine.ADC(0)               # Pin A0, 0 - 3.3 V, 0 - 1023
pwm = machine.PWM(machine.Pin(5))  # Pin D1, Across from A0
pwm.freq(100)                      # 100 Hz
while True:
    v = Vin.read()
    if v > 100: # 0.1V Threshold, approx 0.35 from source
        pwm.duty(v//2)
    else:
        pwm.duty(0)
    
