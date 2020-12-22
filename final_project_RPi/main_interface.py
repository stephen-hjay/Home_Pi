import pygame
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP
import os
import time
import numpy as np
import RPi.GPIO as GPIO
import traceback
import threading
from multiprocessing import Process, Queue
from subprocess import call
import subprocess
import socket
import time
from threading import Thread
import base64
import cv2
import zmq
from video_stream import Classify_and_Stream
from servoControl import ServoControl
import os
from flask import Flask, render_template, Response

app = Flask(__name__)

# Display on piTFT
# need sudo ti be effective
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')

# Track mouse clicks on piTFT
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

GPIO.setmode(GPIO.BCM)  # Use broadcom numbering
# Setup two output pins
global state, success

global systemOn
systemOn = True

global detected
detected = False

global prediction
prediction = ''

global frameQueue
frameQueue = Queue()

# for flask semantic segmentation stream
def gen_frames(frameQueue:Queue):  # generate frame by frame from camera
    while True:
        # Capture frame-by-frame
        #frame = frameQueue.get(True) # read the camera frame
        if not frameQueue.empty():
            frame = frameQueue.get(True)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    global frameQueue
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(frameQueue), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')




def init_CCTV_video_audio():
    call("sudo bash /home/pi/final_project/init_video_audio", shell=True)



def getLocalIp():
    '''Get the local ip'''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

listensocket = socket.socket()
Port = 7000
maxConnections = 999
IP = socket.gethostname()

listensocket.bind((getLocalIp(),Port))


listensocket.listen(maxConnections)
print("Server started at " + IP + " on port " + str(Port))

running = True


def openDoor():
    # servo to open and pin number
    servo = ServoControl(13)
    servo.openDoor()
    time.sleep(1)
    servo.closeDoor()
    # print("stop")
    pass

# load the user info database
users = {"123": "123",
         "jh2735": "1234",
         "ycg534": "3456"}

def connectonProcess(clientsocket,queueLogin:Queue):
    message = clientsocket.recv(1024).decode()  # Receives Message
    # Prints Message
    print(message)
    if message != "":
        if message.startswith("Check:"):
            str_list = message.split(":")
            if str_list[1] in users:
                success = str_list[2] == users[str_list[1]]
                if success:
                    clientsocket.sendall(b"Success")
                    print("user login success")
                    queueLogin.put(str_list[1])
                else:
                    clientsocket.sendall(b"Failure")
                    print("user login failed")
            else:
                clientsocket.sendall(b"Failure")
                print("user login failed")
        elif message == "Door Open":
            print("Door Open")
            clientsocket.sendall(b"Success")
            openDoor()

    clientsocket.close()

# TCP server
def rpi_TCPServer(queueLogin:Queue):
    while running:
        clientsocket, address = listensocket.accept()
        threading.Thread(target=connectonProcess(clientsocket, queueLogin), name="userName").start()



# face recognition
def faceRecognition(q:Queue,frameQueue:Queue):
    classify = Classify_and_Stream()
    classify.classify_and_stream(detected, prediction, q, frameQueue,5)


# main interface function
def mainInterface(q: Queue, queueLogin: Queue):

    '''
      GPIO four buttons callback functions and registration
    '''
    global state, success
    # default state
    state = "MAIN"

    # GPIO 17 - user login on phone
    def GPIO17_userMain(channel):
        global state
        print("----user login----")
        if state == "MAIN":
            state = "USER"
        elif state == "FACE":
            state = "CHECK"

    # GPIO 22 user face login
    def GPIO22_userFaceLogin(channel):
        global state
        print("----userFaceLogin----")
        if state == "MAIN":
            state = "FACE"

    # GPIO 23 user face registration
    def GPIO23_userCancel(channel):
        global state
        tuple_choice =  ("REGISTRATION","USER","FACE","CHECK","Login")
        print("----user cancel----")
        if state == "MAIN":
            state = "REGISTRATION"
        elif state in tuple_choice:
            state = "MAIN"

    # system exit
    def GPIO27_close(channel):
        print("----system off process begin----")
        # state = "close"
        global systemOn
        systemOn = False
        GPIO.cleanup()
        # shutdown the RPi
        call("sudo reboot", shell=True)

    # GPIO set up
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(17, GPIO.FALLING, callback=GPIO17_userMain, bouncetime=300)
    GPIO.add_event_detect(22, GPIO.FALLING, callback=GPIO22_userFaceLogin, bouncetime=300)
    GPIO.add_event_detect(23, GPIO.FALLING, callback=GPIO23_userCancel, bouncetime=300)
    GPIO.add_event_detect(27, GPIO.FALLING, callback=GPIO27_close, bouncetime=300)

    '''
    state machine control thread functions
    '''

    

    def checkResult(q: Queue):
        global success
        print("read date from queue")
        # ten positive result in 3 secs
        val = q.get(True)
        success = val
        pass

    # door open
    def openDoor():
        # servo to open and pin number
        servo = ServoControl(13)
        servo.openDoor()
        time.sleep(1)
        servo.closeDoor()
        # print("stop")
        
        pass

    # registration
    

    def registration():
        print("registration")
        # save photos in local file system
        call("sudo bash take_photo.sh", shell=True)
        time.sleep(50)
        print("registration finish")
        stateChange('Cancel')
        pass

    def backToMain():
        print("back to main")
        time.sleep(5)
        if state == "FINISH" or state == "CHECK" or state == "Login":
            stateChange('Cancel')

    '''
      state machine related functions
    '''
    
    def loginCheck(queueLogin:Queue):
        global state
        if not queueLogin.empty():
            gloabal userName
            userName = queueLogin.get(True)
            if state == "USER":
                state = "Login"

    # state machine
    stateMachine = {
        "Admin Login": "USER",
        "Face Login": "FACE",
        "Face Registration": "REGISTRATION",
        "Cancel": "MAIN",
        'Confirm': 'CHECK',
        "Finish": "FINISH"
    }

    # button trigger state machine state change
    def stateChange(input):
        global state
        print(input)
        state = stateMachine[input]

    '''
    Pygame related functions
    '''

    # pygame initialization
    pygame.init()
    pygame.mouse.set_visible(False)

    # screen initialization
    size  = 320, 240
    screen = pygame.display.set_mode(size)
    fontUsed = pygame.font.Font(None, 30)

    # draw a button on screen
    def draw_button(button, screen):
        # Draw the button rect and the text surface
        pygame.draw.rect(screen, button['color'], button['rect'])
        screen.blit(button['text'], button['text rect'])

    # create a button object: color, background, callback function, text, rect for collide detection
    def create_button(x, y, w, h, bg, text, textColor, callback):
        # Create a buttondictionary of the rect, text,
        # text rect, color and the callback function.
        FONT = pygame.font.Font(None, 24)
        text_surface = FONT.render(text, True, textColor)
        button_rect = pygame.Rect(x, y, w, h)
        text_rect = text_surface.get_rect(center=button_rect.center)
        button = {
            'rect': button_rect,  # rect to detect button detection
            'text': text_surface,
            'text rect': text_rect,
            'color': bg,
            'callback': callback,
            'text_text': text
        }
        return button

    def drawText(x: int, y: int, text: str, color: tuple):
        text_surface = fontUsed.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)

    # color setting
    SHADOW = (192, 192, 192)
    WHITE = (255, 255, 255)
    LIGHTGREEN = (0, 255, 0)
    GREEN = (0, 200, 0)
    BLUE = (0, 0, 128)
    LIGHTBLUE = (0, 0, 255)
    RED = (200, 0, 0)
    LIGHTRED = (255, 100, 100)
    PURPLE = (102, 0, 102)
    LIGHTPURPLE = (153, 0, 153)
    BLACK = (0, 0, 0)

    '''
    interface elements
    '''

    # options buttons
    userLogin = create_button(170, 10, 140, 60, LIGHTGREEN, 'Admin Login', BLACK, lambda: stateChange('Admin Login'))
    faceRecognition = create_button(170, 85, 140, 60, LIGHTBLUE, 'Face Login', BLACK, lambda: stateChange('Face Login'))
    faceRegistration = create_button(170, 160, 140, 60, LIGHTRED, 'Face Registration', BLACK, lambda: stateChange('Face Registration'))

    # confirm cancel
    cancel = create_button(200, 200, 120, 40, RED, 'Back To Main', BLACK, lambda: stateChange('Cancel'))
    confirm = create_button(170, 90, 100, 50, SHADOW, 'Confirm', BLACK, lambda: stateChange('Confirm'))

    # welcome interface
    text_left = {
        "welcome": (60, 40, "Welcome"),
        "to":(60,80,"To"),
        "home": (60, 120, "Home"),

        "pi": (60, 180, "Pi")
    }
    text_left_list = ['welcome', 'to','home', 'pi']

    '''
    text for user / face / check / registration / finish
    '''
    # user login
    text_user = (220, 70, "Login on App")
    
    # user_success
    text_success1 =  (220,70,"Welcome")
    text_success2 = (220,120,"jh2735")

    # face
    text_face1 = (220, 40, "Face camera")
    text_face2 = (220, 60,"press Confirm")

    # check
    text_success = (220, 60, "Welcome!")
    text_Fail = (220, 60, "Face Fail")

    # registration
    text_reg1 = (220, 60, "Registration")
    text_reg2 = (220, 120, "Be patient")

    # draw finish
    text_finish = (220, 80, "Please Back to Main")

    # A list that contains all buttons for main interface.
    button_list_main = [userLogin, faceRecognition, faceRegistration]

    # a list that contains all buttons for other interfaces
    button_list_else = [cancel, confirm]

   

    '''
    thread
    '''
    threadOpen = None
    threadCheck = None
    threadRegistration = None
    threadFinish = None

    while systemOn:
        time.sleep(0.04)
        # make white screen
        screen.fill(pygame.Color('white'))  # Flush screen
        if state == "MAIN":
            for button in button_list_main:
                draw_button(button, screen)
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)
            success = False
            threadOpen = None
            threadCheck = None
            threadRegistration = None
            threadFinish = None
            threadLogin = None

        elif state == "USER":
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)
            drawText(text_user[0], text_user[1], text_user[2], BLACK)
            draw_button(cancel, screen)
            if not threadLogin:
                threadLogin = threading.Thread(target=loginCheck, name="loginCheck")
                threadLogin.start()
        
        elif state == "Login":
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)
            drawText(text_success1[0], text_success1[1], text_success1[2], BLACK)
            text_success2 = (220,120,userName)
            drawText(text_success2[0], text_success2[1], text_success2[2], BLACK)
            
            draw_button(cancel, screen)
            if not threadFinish:
                threadFinish = threading.Thread(target=backToMain, name="backToMain")
                threadFinish.start()
            
        elif state == "FACE":
            #print("FACE:"+str(success))
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)
            draw_button(cancel, screen)
            draw_button(confirm, screen)
            drawText(text_face1[0], text_face1[1], text_face1[2], BLACK)
        
            drawText(text_face2[0], text_face2[1], text_face2[2], BLACK)

            if not threadCheck:
                # read the value of face recognition and copy it to success
                threadCheck = threading.Thread(target=checkResult(q), name="checkResult")
                threadCheck.start()

        elif state == "CHECK":
        
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)
            # check the result of face recognition
            draw_button(cancel, screen)

            if success:
                drawText(text_success[0], text_success[1], text_success[2], BLACK)
                if not threadOpen:
                    threadOpen = threading.Thread(target=openDoor(), name="openDoor")
                    threadOpen.start()

            else:
                # refuse word
                drawText(text_Fail[0], text_Fail[1], text_Fail[2], BLACK)

                if not threadFinish:
                    threadFinish = threading.Thread(target=backToMain, name="backToMain")
                    threadFinish.start()
                pass

        elif state == "REGISTRATION":
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)
            draw_button(cancel, screen)
            drawText(text_reg1[0], text_reg1[1], text_reg1[2], BLACK)
            drawText(text_reg2[0], text_reg2[1], text_reg2[2], BLACK)
            if not threadRegistration:
                # read the value of face recognition and copy it to success
                threadRegistration = threading.Thread(target=registration, name="registration")
                threadRegistration.start()

        elif state == "FINISH":
            pygame.draw.rect(screen, SHADOW, [0, 0, 120, 240])
            for text in text_left_list:
                itemText = text_left[text]
                drawText(itemText[0], itemText[1], itemText[2], BLACK)

            draw_button(cancel, screen)
            drawText(text_finish[0], text_finish[1], text_finish[2], BLACK)

            if not threadFinish:
                # read the value of face recognition and copy it to success
                threadFinish = threading.Thread(target=backToMain, name="backToMain")
                threadFinish.start()

        pygame.display.flip()


if __name__ == '__main__':
    try:
        q = Queue()
        queueLogin = Queue()
        print("init video and audio")
        process_CCTV = Process(target=init_CCTV_video_audio)
        print("user interface")
        process_interface = Process(target=mainInterface, args=(q,queueLogin,))
        print("TCP Server")
        process_TCP_Server = Process(target=rpi_TCPServer, args(queueLogin,))
        process_Face_Recognition = Process(target=faceRecognition,args=(q,frameQueue))
        process_Face_Recognition.start()
        process_TCP_Server.start()
        process_CCTV.start()
        process_interface.start()
      
        # running flask stream server
        app.run(host="0.0.0.0")


    except BaseException:
        traceback.print_exc()

