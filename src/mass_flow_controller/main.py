from machine import Pin, SPI, I2C
from ADS1X15 import ADS1115
from MAX5134 import MAX513X
from mfc import massFlowController
i2c = I2C(scl=Pin(5), sda=Pin(4))
addr = i2c.scan() # Assuming only ADS1115 is connected, otherwise specify the address
adc = ADS1115(i2c, addr[0])
adc.gain = 0
spi = SPI(1, baudrate=400000)
dac = MAX513X(Pin(15, Pin.OUT), spi, device=5137)
timeout = 20

# Both MFCs are limited to 200/100 sccm to save gas. This is ~ 1/3 of their total range.
MFC = [massFlowController(DAC = dac,
                          ADC = adc,
                          port = 0,
                          maxFlow = 200,
                          timeout = timeout,
                          cal_file = 'cal_sample.txt'),
       massFlowController(DAC = dac,
                          ADC = adc,
                          port = 1,
                          maxFlow = 100,
                          timeout = timeout,
                          cal_file = 'cal_backflush.txt')
    ]
