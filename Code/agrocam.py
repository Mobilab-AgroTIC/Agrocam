#!/usr/bin python3
import RPi.GPIO as GPIO
from gpiozero import Servo
from picamera2 import Picamera2, Preview
# from libcamera import Transform
from time import sleep
from ftplib import FTP
from datetime import datetime
import os
import credentials
import smbus


# Numéro de la broche GPIO à utiliser pour le servo moteur
pwm_gpio = 18

# Numéro de la broche de debogage
controlPin = 24

# Configuration de la caméra
camera = Picamera2()
# Configuration for rotating picture
# camera_config = camera.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores",transform=Transform(180))
camera_config = camera.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")

camera.configure(camera_config)
# Configuration du servo
frequence = 50

def initialize_GPIO() :
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pwm_gpio, GPIO.OUT)
    GPIO.setup(controlPin, GPIO.IN)

def angle_to_percent (angle) :
    if angle > 180 or angle < 0 :
        return False
    start = 4
    end = 12.5
    ratio = (end - start)/180 #Calcul ratio from angle to percent

    angle_as_percent = angle * ratio

    return start + angle_as_percent

def prendre_photo():
    camera.start_preview()
    camera.start()
    sleep(2)
    camera.capture_file('/home/pi/Agrocam/photo.jpg')
    camera.stop_preview()
    camera.close()

def envoyer_sur_ftp():
    ftp = FTP(credentials.ftp_server)
    ftp.login(credentials.ftp_username, credentials.ftp_password)
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d_%H%M%S")
    bus = smbus.SMBus(1)
    voltageInt=str(bus.read_byte_data(0x08,1))
    voltageDec=str(bus.read_byte_data(0x08,2))
    with open('/home/pi/Agrocam/photo.jpg', 'rb') as fichier:
        ftp.storbinary('STOR /data/'+ credentials.name +'/'+credentials.name+'_'  + current_date + '_' + voltageInt + '_' + voltageDec + '.jpg',fichier)
    ftp.quit()

def main():
    initialize_GPIO()
    pwm = GPIO.PWM(pwm_gpio,frequence)
    pwm.start(0)
    try:
        pwm.ChangeDutyCycle(angle_to_percent(90))
        sleep(0.1)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        prendre_photo()
        pwm.ChangeDutyCycle(angle_to_percent(180))
        sleep(0.1)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        envoyer_sur_ftp()
        print("Traitement terminé.")
        sleep(1)  # Attendre avant de répéter le traitement

    except KeyboardInterrupt:
        pass

    finally:
        pwm.stop()
        camera.close()
        i=1
        while (GPIO.input(controlPin) == 1) :
            sleep(5)
            print("ControlPin is not LOW. i = ", i)
            i += 1
        GPIO.cleanup()
        os.system("sudo shutdown -h now")

if __name__ == "__main__":
    main()
