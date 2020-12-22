import RPi.GPIO as GPIO
import time

class ServoControl:
    def __init__(self, servoPIN):
        self.servoPIN = servoPIN
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(servoPIN, GPIO.OUT)
        self.p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz
        self.p.start(7.5) # Initialization

    def openDoor(self):
        self.p.ChangeDutyCycle(10)
        time.sleep(1)
        self.p.ChangeDutyCycle(7.5)
        print('Door opened')

    def closeDoor(self):
        self.p.ChangeDutyCycle(5)
        time.sleep(1)
        self.p.ChangeDutyCycle(7.5)
        print('Door closed')
    
    def cleanup(self):
        GPIO.cleanup()

