from time import sleep
import RPi.GPIO as GPIO

class ServoManager:
    def __init__(self, pin_shutter, pin_filter):
        self.pin_shutter = pin_shutter
        self.pin_filter = pin_filter

    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_shutter, GPIO.OUT)
        GPIO.setup(self.pin_filter, GPIO.OUT)
        self.shutter = GPIO.PWM(self.pin_shutter, 50)
        self.filter  = GPIO.PWM(self.pin_filter,  50)
        self.shutter.start(0)
        self.filter.start(0)
        return self

    def __exit__(self, *_):
        self.shutter.stop()
        self.filter.stop()
        GPIO.cleanup([self.pin_shutter, self.pin_filter])  # uniquement les pins servo


def angle_to_percent(angle):
    if angle > 180 or angle < 0:
        return False
    start = 4
    end = 12.5
    ratio = (end - start) / 180
    angle_as_percent = angle * ratio
    return start + angle_as_percent


def move_servo(pwm_instance, angle):
    """Déplace un servo à l'angle indiqué (0-180)."""
    duty = angle_to_percent(angle)
    if duty is False:
        raise ValueError(f"Angle servo invalide : {angle}")
    pwm_instance.ChangeDutyCycle(duty)
    sleep(0.2)
    pwm_instance.ChangeDutyCycle(0)
    sleep(0.1)

def move_step_motor(pin, angle):
    """
    Fonction à développer pour intégrer la rotation des filtres et obturateur avec un step motor
    """

def hello_world_servo(pwm_instance):
    """
    Fait tourner le servo moteur aller retour jusqu'à 90°.
    Permet de vérifier si le servomoteur fonctionne bien
    """
    move_servo(pwm_instance,90)
    sleep(0.5)
    move_servo(pwm_instance,0)
