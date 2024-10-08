import RPi.GPIO as GPIO
from gpiozero import Servo
from time import sleep

frequence = 50
pwm_gpio = 18
def angle_to_percent (angle) :
    if angle > 180 or angle < 0 :
        return False
    start = 4
    end = 12.5
    ratio = (end - start)/180 #Calcul ratio from angle to percent

    angle_as_percent = angle * ratio

    return start + angle_as_percent
GPIO.setmode(GPIO.BCM)
GPIO.setup(pwm_gpio, GPIO.OUT)

pwm = GPIO.PWM(pwm_gpio,frequence)
pwm.start(0)
pwm.ChangeDutyCycle(angle_to_percent(0))
sleep(0.2)
pwm.ChangeDutyCycle(0)
sleep(0.1)
sleep(5)
pwm.ChangeDutyCycle(angle_to_percent(90))
sleep(0.2)
pwm.ChangeDutyCycle(0)
sleep(0.1)
pwm.stop()
GPIO.cleanup()

