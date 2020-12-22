counter=1
Path=/home/pi/face_images/Jay/
name=Jay_6pm
fileType=.jpg
while [ $counter -le 50 ]
    do
        fswebcam -r 1280x720 --no-banner $Path$name$counter$fileType
        echo $Path$name$counter$fileType 

        ((counter++))
    done
