#!/usr/bin python3
import RPi.GPIO as GPIO
from gpiozero import Servo
from picamera2 import Picamera2, Preview
# from libcamera import Transform
from time import sleep
from ftplib import FTP
from datetime import datetime, timedelta
import os
import credentials as credentials
import smbus


# Numéro de la broche GPIO à utiliser pour le servo moteur
pwm_gpio = 18

# Numéro de la broche de debogage
controlPin = 24

# Configuration de la caméra
camera = Picamera2()

# Configuration for rotating picture
# Ci-dessous d'anciennes config qui ne minimise la taille des images (<500 ko)
# camera_config = camera.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores",transform=Transform(180))
# camera_config = camera.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
# La config ci-dessous maximise la taille et donc la qualité de l'image
camera_config = camera.create_still_configuration(main={"size": (4608, 2592)}, lores={"size": (640, 480)}, display="lores")
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

def prendre_photo(date):
    camera.start_preview()
    camera.start()
    camera.set_controls({"AfMode": 1}) 
    sleep(1)
    camera.capture_file('/home/pi/Agrocam/photo'+date+'.png')
    camera.stop_preview()
    camera.close()

def envoyer_sur_ftp(date):
    ftp = FTP(credentials.ftp_server)
    ftp.login(credentials.ftp_username, credentials.ftp_password)
    
    bus = smbus.SMBus(1)
    voltageInt=str(bus.read_byte_data(0x08,1))
    voltageDec=str(bus.read_byte_data(0x08,2))
    with open('/home/pi/Agrocam/photo'+date+'.png', 'rb') as fichier:
        ftp.storbinary('STOR /data/'+ credentials.name +'/'+credentials.name+'_'  + date + '_' + voltageInt + '_' + voltageDec + '.png',fichier)
    ftp.quit()
    dest_path="sudo mv /home/pi/Agrocam/photo"+date+".png /home/pi/Agrocam/"+credentials.name+"_"  + date + "_" + voltageInt + "_" + voltageDec + ".png"
    os.system(dest_path)

def set_startup_time(date, hour, minute, second):
    command_set_startup = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && set_startup_time {date} {hour} {minute} {second}'"
    command_net_to_system = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && net_to_system'"
    command_system_to_rtc = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && system_to_rtc'"
    print(command_set_startup)
    os.system(command_net_to_system)
    os.system(command_system_to_rtc)
    os.system(command_set_startup)

def calculate_next_startup_time(trigger_times):
    now = datetime.now()
    today = now.date()

    # Créer des objets datetime pour chaque heure de déclenchement aujourd'hui
    trigger_datetimes_today = [datetime.combine(today, t) for t in trigger_times]

    # Filtrer pour trouver les déclenchements encore à venir aujourd'hui
    upcoming_triggers = [t for t in trigger_datetimes_today if t > now]

    # Si un déclenchement est encore à venir aujourd'hui, prendre le prochain ; sinon, prendre le premier de demain
    if upcoming_triggers:
        next_startup = upcoming_triggers[0]
    else:
        # Si tous les déclenchements sont passés pour aujourd'hui, prendre le premier déclenchement de demain
        next_startup = trigger_datetimes_today[0] + timedelta(days=1)

    # Extraire les valeurs pour `date`, `hour`, `minute`, `second`
    day = next_startup.day
    hour = next_startup.hour
    minute = next_startup.minute
    second = next_startup.second

    return day, hour, minute, second

def main():
    sleep(30) # waiting for wifi
    initialize_GPIO()
    pwm = GPIO.PWM(pwm_gpio,frequence)
    pwm.start(0)
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d_%H%M%S")
    try:
        pwm.ChangeDutyCycle(angle_to_percent(0))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        prendre_photo(current_date)
        print("photo prise")
        pwm.ChangeDutyCycle(angle_to_percent(90))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        envoyer_sur_ftp(current_date)
        print("Envoi sur FTP terminé")
        sleep(1)  # Attendre avant de répéter le traitement

    except KeyboardInterrupt:
        pass

    finally:
        pwm.stop()
        camera.close()
        # Calcul de la prochaine date de déclenchement et enregistrement dans Wittypi
        day, hour, minute, second = calculate_next_startup_time(credentials.trigger_times)
        set_startup_time(day, hour, minute, second)
        i=1
        while (GPIO.input(controlPin) == 1) :
            sleep(5)
            print("ControlPin is not LOW. i = ", i)
            i += 1
        GPIO.cleanup()
        os.system("sudo shutdown -h now")

if __name__ == "__main__":
    main()
