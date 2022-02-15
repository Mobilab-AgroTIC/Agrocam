#!/bin/bash

echo "hello World !";

# Shtudown HDMI port (battery saver)
sudo tvservice --off

# Activate servo motor and open cache
gpio -g mode 18 pwm
gpio pwm-ms
gpio pwmc 192
gpio pwmr 2000
gpio -g pwm 18 90

#take picture
mkdir -p Viticam
libcamera-jpeg -o /home/pi/Viticam/temp.jpg

echo "shooting done.";
sleep 2

# Closing cache
gpio -g pwm 18 180

# Connection check. Turn off after 1min if no connection.
STATE="error";
COUNTER=0;
while [  $STATE == "error" ]; do
    STATE=$(ping -q -w 1 -c 1 `ip r | grep default | cut -d ' ' -f 3` > /dev/null && echo ok || echo error)
    sleep 2
		COUNTER+=1;
		echo "connection try : " $COUNTER "/30";
		if [[ $COUNTER > 30 ]]; then
			echo "No connection. shutdown...";
			sudo shutdown -h now
		fi
 done

# Rename and send image
python << END_OF_PYTHON
import ftplib
import RPi.GPIO as GPIO
import os
from datetime import datetime
from dotenv import load_dotenv

now = datetime.now()
current_date = now.strftime("%Y-%m-%d_%H%M%S")

print("date and time =", current_date)

load_dotenv("/home/pi/.env")
hostname=os.environ.get('hostname")
user=os.environ.get('user')
password=os.environ.get('password')

session = ftplib.FTP(hostname,user,password)
file = open('/home/pi/Viticam/temp.jpg','rb')
session.storbinary('STOR /img/dev1_'+ current_date +'.jpg', file)
file.close()
session.quit()

END_OF_PYTHON

DATE=$(date +"%Y-%m-%d_%H%M")
echo "Sending done. Archiving..."
mkdir -p Viticam/images
sudo mv /home/pi/Viticam/temp.jpg /home/pi/Viticam/images/$DATE.jpg
echo "Finished!";

python << END_OF_PYTHON

import time
import RPi.GPIO as GPIO

controlPin=23
GPIO.setmode(GPIO.BCM)
GPIO.setup(controlPin, GPIO.IN)

i=1
while (GPIO.input(controlPin) == 1) :
	time.sleep(5)
	print("ControlPin is not LOW. i = ", i)
	i += 1

END_OF_PYTHON

echo "controlPin is LOW : shutdown";
sudo shutdown -h now
