from machine import Pin, SPI, I2C
from ADS1X15 import ADS1115
from MAX5134 import MAX5134
from mfc import massFlowController
i2c = I2C(scl=Pin(5), sda=Pin(4))
addr = i2c.scan() # Assuming only ADS1115 is connected, otherwise specify the address
adc = ADS1115(i2c, addr[0])
adc.gain = 0
spi = SPI(1, baudrate=400000)
dac = MAX5134(Pin(15, Pin.OUT), spi)

sampleMFC = massFlowController(DAC=dac,
                             ADC=adc,
                             maxFlow=1000,
                             units='SCCM',
                             port=0)

carrierMFC = massFlowController(DAC=dac,
                                ADC=adc,
                                maxFlow=500,
                                units='SCCM',
                                port=1)
