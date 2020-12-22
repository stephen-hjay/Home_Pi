import subprocess 
def checkPIcam(device):

    cmd = ['v4l2-ctl', '-d', '/dev/'+device, '-D']
    wordtofind="bm2835"
    isfound=executeandsearch(cmd,wordtofind)
    return isfound

def executeandsearch(cmd,wordtofind):
    try:
        scanoutput = subprocess.check_output(cmd).decode('utf-8')
    except:
        #print "error to execute the command" , cmd
        #logger.error("errorxecute the command %s",cmd)
        return False

    for line in scanoutput.split('\n'):
        strstart=line.find(wordtofind)
        if strstart>-1:
            #found
            return True
    return False




#print(checkPIcam('video0'))
#print(checkPIcam('video1'))
