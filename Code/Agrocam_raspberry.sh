#!/bin/bash

echo "hello World !";
echo "Today is $(date)"
# Shtudown HDMI port (battery saver)
sudo tvservice --off

# Activate servo motor and open cache
gpio -g mode 18 pwm
gpio pwm-ms
gpio pwmc 192
gpio pwmr 2000
gpio -g pwm 18 90

#take picture
mkdir -p /home/pi/Agrocam
sudo chmod 777 Agrocam
sleep 10
libcamera-jpeg -o /home/pi/Agrocam/temp.jpg

echo "shooting done.";
sleep 2

# Closing cache
gpio -g pwm 18 180

# Connection check. Turn off after 1min if no connection.
# STATE="error";
# COUNTER=0;
# while [  $STATE == "error" ]; do
#    STATE=$(ping -q -w 1 -c 1 `ip r | grep default | cut -d ' ' -f 3` > /dev/null && echo ok || echo error)
#    sleep 2
#		COUNTER+=1;
#		echo "connection try : " $COUNTER "/30";
#		if [[ $COUNTER > 30 ]]; then
#			echo "No connection. shutdown...";
#			sudo shutdown -h now
#		fi
# done
# Rename and send image
python << END_OF_PYTHON
import ftplib
import RPi.GPIO as GPIO
import os
from datetime import datetime
from dotenv import load_dotenv

#getting environnement data
load_dotenv("/home/pi/.env")
hostname=os.environ.get('hostname')
user=os.environ.get('user')
password=os.environ.get('password')
url=os.environ.get('url')

import smbus
bus = smbus.SMBus(1)
voltageInt=str(bus.read_byte_data(0x08,1))
voltageDec=str(bus.read_byte_data(0x08,2))

now = datetime.now()
current_date = now.strftime("%Y-%m-%d_%H%M%S")

print("date and time =", current_date)

session = ftplib.FTP(hostname,user,password)
file = open('/home/pi/Agrocam/temp.jpg','rb')
session.storbinary(url+'_'+ current_date +'_'+voltageInt+'_'+voltageDec+'.jpg', file)
file.close()
session.quit()

END_OF_PYTHON

DATE=$(date +"%Y-%m-%d_%H%M")
echo "Sending done. Archiving..."
mkdir -p Agrocam/images
sudo mv /home/pi/Agrocam/temp.jpg /home/pi/Agrocam/images/$DATE.jpg
echo "Finished!";

python << END_OF_PYTHON

import time
import RPi.GPIO as GPIO

controlPin=24
GPIO.setmode(GPIO.BCM)
GPIO.setup(controlPin, GPIO.IN)

i=1
while (GPIO.input(controlPin) == 1) :
	time.sleep(5)
	print("ControlPin is not LOW. i = ", i)
	i += 1

END_OF_PYTHON

echo "controlPin is LOW : shutdown";
# Comment line bellow for debugging script, otherwise raspi will sutdown
sudo shutdown -h now 
