import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(13, GPIO.OUT)

p = GPIO.PWM(13, 50)  # channel=12 frequency=50Hz
p.start(7.5)

try:
    while True:
        p.ChangeDutyCycle(7.5)
        print('one loop')
        time.sleep(0.5)
except KeyboardInterrupt:
    GPIO.cleanup()
