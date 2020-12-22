from servoControl import ServoControl
import time
#from RPi.GPIO import GPIO

servo = ServoControl(13)

try:
    while True:
        servo.openDoor()
       # print('Door opened')
        time.sleep(15)
        servo.closeDoor()
        time.sleep(15)
       # print('Door closed')
except KeyboardInterrupt:
    servo.cleanup()
