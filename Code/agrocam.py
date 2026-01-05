#!/usr/bin/python3
import RPi.GPIO as GPIO
from gpiozero import Servo
from picamera2 import Picamera2, Preview

from time import sleep
from datetime import datetime, timedelta
import os
import subprocess

# Numéro de la broche GPIO à utiliser pour le servo moteur
pwm_gpio = 18

# Numéro de la broche de debogage
controlPin = 24

# Configuration de la caméra
camera = Picamera2()

# Configuration for rotating picture
camera_config = camera.create_still_configuration(
    main={"size": (4608, 2592)}, lores={"size": (640, 480)}, display="main"
)
camera.configure(camera_config)

camera.set_controls({"AfMode": 2})  # Autofocus

frequence = 50


def initialize_GPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pwm_gpio, GPIO.OUT)
    GPIO.setup(controlPin, GPIO.IN)


def angle_to_percent(angle):
    if angle > 180 or angle < 0:
        return False
    start = 4
    end = 12.5
    ratio = (end - start) / 180  # Calcul ratio from angle to percent
    angle_as_percent = angle * ratio
    return start + angle_as_percent


def prendre_photo(date):
    sleep(1)  # laisse le temps à la caméra de stabiliser exposition/focus
    camera.capture_file("/mnt/usb/photo" + date + ".png")


def set_startup_time(date, hour, minute, second):
    command_set_startup = f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && set_startup_time {date} {hour} {minute} {second}'"
    command_net_to_system = (
        f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && net_to_system'"
    )
    command_system_to_rtc = (
        f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && system_to_rtc'"
    )
    os.system(command_net_to_system)
    os.system(command_system_to_rtc)
    os.system(command_set_startup)


def calculate_next_startup_time(trigger_times):
    now = datetime.now()
    today = now.date()
    trigger_datetimes_today = [datetime.combine(today, t) for t in trigger_times]
    upcoming_triggers = [t for t in trigger_datetimes_today if t > now]
    if upcoming_triggers:
        next_startup = upcoming_triggers[0]
    else:
        next_startup = trigger_datetimes_today[0] + timedelta(days=1)
    day = next_startup.day
    hour = next_startup.hour
    minute = next_startup.minute
    second = next_startup.second
    return day, hour, minute, second



def main():
    os.system("sudo umount /mnt/usb")
    initialize_GPIO()
    pwm = GPIO.PWM(pwm_gpio, frequence)

    # Vérification de connexion internet et réglage heure
    r = subprocess.run(
        ["nmcli con | grep ethernet"], shell=True, stdout=subprocess.PIPE
    ).stdout.decode("UTF-8")
    if len(r) > 0:
        r2 = subprocess.run(
            ["ping -c 1 -W 1 8.8.8.8 | grep icmp_seq"],
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.decode("UTF-8")
        if len(r2) > 0:
            print("mise a l'heure depuis internet")
            command_net_to_system = f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && net_to_system'"
            os.system(command_net_to_system)
            print("reglage de l'heure RTC depuis system")
            command_system_to_rtc = f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && system_to_rtc'"
            os.system(command_system_to_rtc)
        else:
            print("mise a l'heure systeme depuis rtc")
            command_rtc_to_system = f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && rtc_to_system'"
            os.system(command_rtc_to_system)
    else:
        print("mise a l'heure systeme depuis rtc")
        command_rtc_to_system = f"sudo bash -c 'source /home/localadmin/wittypi/utilities.sh && rtc_to_system'"
        os.system(command_rtc_to_system)

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d_%H%M%S")

    iteration = 0
    while (
        iteration < 10
        and len(
            subprocess.run(
                ["mount | grep /mnt/"], shell=True, stdout=subprocess.PIPE
            ).stdout.decode("UTF-8")
        ) == 0
    ):
        retour = subprocess.run(
            ["ls /dev/sd*1"], shell=True, stdout=subprocess.PIPE
        ).stdout.decode("UTF-8")
        os.system(
            "sudo mount " + retour[:-1] + " /mnt/usb -o uid=localadmin,gid=localadmin"
        )

        try:
            # Démarrage de la caméra (une seule fois)
            camera.start_preview()
            camera.start()

            # Servo à 0°
            print("volet a 0°")
            prendre_photo(current_date)
            print("photo prise...")



            # Servo à 105°
            print("volet a 105°")
            pwm.start(angle_to_percent(105))
            sleep(0.3)
            pwm.stop()

            prendre_photo(current_date + "_98deg")
            print("photo2 prise...")

            camera.stop_preview()
            camera.close()

            pwm.start(angle_to_percent(0))
            print("volet a 0°")
            sleep(0.3)
            pwm.stop()
            sleep(0.2)


        except KeyboardInterrupt:
            pass

        finally:
            iteration += 1
            pwm.stop()

            # Calcul de la prochaine date de déclenchement et enregistrement dans Wittypi
            os.system("sudo cp /mnt/usb/next.py ~/")
            from next import trigger_times

            day, hour, minute, second = calculate_next_startup_time(trigger_times)
            set_startup_time(day, hour, minute, second)

            i = 1
            while GPIO.input(controlPin) == 1:
                sleep(5)
                print("ControlPin is not LOW. i = ", i)
                i += 1

            GPIO.cleanup()
            os.system("sudo umount /mnt/usb")
            os.system("sudo shutdown -h now")


if __name__ == "__main__":
    main()
