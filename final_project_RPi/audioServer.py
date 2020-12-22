from subprocess import call

def audioServer():
    call("sudo bash /home/pi/darkice.sh", shell=True)
    print("-----audio server----")