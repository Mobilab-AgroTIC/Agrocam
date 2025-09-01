#!/usr/bin python3
import RPi.GPIO as GPIO
from gpiozero import Servo
from picamera2 import Picamera2, Preview
# from libcamera import Transform
import time
from time import sleep
from ftplib import FTP
import requests
from datetime import datetime, timedelta, timezone
import subprocess
import credentials as credentials
import os


# Numéro de la broche GPIO à utiliser pour le servo moteur
pwm_gpio = 18

# Numéro de la broche de debogage
controlPin = 24


def initialize_camera(timeout=10):
    print("Initialisation de la caméra...")
    start_time = time.time()
    
    while True:
        try:
            cam = Picamera2()
            camera_config = cam.create_still_configuration(
                main={"size": (4608, 2592)},
                lores={"size": (640, 480)},
                display="main"
            )
            cam.configure(camera_config)
            cam.set_controls({"AfMode": 2})
            print("Caméra initialisée.")
            return cam
        except Exception as e:
            if time.time() - start_time > timeout:
                print(f"Timeout ({timeout}s) : impossible d'initialiser la caméra.")
                return None
            print("Erreur initialisation caméra, nouvelle tentative...")
            time.sleep(1)

def initialize_GPIO() :
    print("Initialisation des GPIO...")
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

def prendre_photo(camera,date):
    camera.start_preview()
    camera.start() 
    sleep(1)
    filepath = f'/home/pi/Agrocam/photo{date}_pending.png'
    camera.capture_file(filepath)
    camera.stop_preview()
    camera.close()
    return filepath  # On retourne le chemin pour savoir où est la photo

def envoyer_http(image_path):
    print("Envoi de la photo et des métadonnées via HTTP...")
    url = 'https://agrocam.agrotic.org/api/upload'
    # Préparez les métadonnées à envoyer
    metadata = {
        'key': 'your_key_value',
        'power_level': 'battery_percentage',
        'comment': 'optional_comment',
        'date_acquisition': ' acquisition_date_string',
        'date_reception': 'reception_date_string',
        'longitude': 'longitude_value',
        'latitude': 'latitude_value',
        'temperature_device': 'temperature_value'
    }
    # Ouvrez le fichier image et envoyez-le avec les métadonnées
    print(f"Envoi de l'image : {image_path}")
    if not os.path.exists(image_path):
        print(f"Erreur : le fichier {image_path} n'existe pas.")
        return
    with open(image_path, 'rb') as f:
        files = {'photo': ( 'photo.jpg', f, 'image/jpeg')} # 'photo.jpg' is the filename, f is the file object, 'image/jpeg' is the content type
        data = metadata # The metadata is sent as form fields

             response = requests.post(url, files=files, data=data)

         if response.status_code == 200:
             print("Photo and metadata sent successfully! Status:", response.status_code)
         else:
             print(f"Error sending data. Status code: {response.status_code}", file=sys.stderr)
             print("Response body:", response.text, file=sys.stderr)

def envoyer_sur_ftp(date):
    ftp = FTP(credentials.ftp_server)
    ftp.login(credentials.ftp_username, credentials.ftp_password)
    
    command = subprocess.run(['bash', '-c', 'source /home/pi/wittypi/utilities.sh && get_input_voltage'],capture_output=True,text=True)
    voltage = command.stdout.strip()
    with open('/home/pi/Agrocam/photo'+date+'.png', 'rb') as fichier:
        ftp.storbinary('STOR /data/'+ credentials.name +'/'+credentials.name+'_'  + date + '_' + voltage + '.png',fichier)
    ftp.quit()
    cmd="sudo mv /home/pi/Agrocam/photo"+date+".png /home/pi/Agrocam/"+credentials.name+"_"  + date + "_" + voltage + ".png"
    subprocess.run(['bash', '-c', cmd],capture_output=True,text=True)

def set_startup_time(date, hour, minute, second):
    print("Configuration de l'heure de démarrage...")
    command_set_startup = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && set_startup_time {date} {hour} {minute} {second}'"    
    command_net_to_system = subprocess.run(['bash', '-c', 'source /home/pi/wittypi/utilities.sh && net_to_system'],capture_output=True,text=True)
    command_system_to_rtc = subprocess.run(['bash', '-c', 'source /home/pi/wittypi/utilities.sh && system_to_rtc'],capture_output=True,text=True)
    subprocess.run(['bash', '-c',command_set_startup ],capture_output=True,text=True)
    
    print(command_set_startup)

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
    
def setup_wittypi():
    pulsing_interval = 13
    white_led_duration=7
    recovery_voltage=20
    threshold_voltage=70
    cmd_pulse = f"""sudo bash -c 'I2C_BUS=1;  source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_PULSE_INTERVAL {credentials.pulsing_interval}'"""
    cmd_led = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_BLINK_LED {credentials.white_led_duration}'"""
    cmd_recovery_voltage=f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS  $I2C_CONF_RECOVERY_VOLTAGE {credentials.recovery_voltage}'"""
    cmd_threshold_voltage = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_LOW_VOLTAGE {credentials.threshold_voltage}'"""

    subprocess.run(cmd_led, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_pulse, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_recovery_voltage, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_threshold_voltage, shell=True, capture_output=True, text=True)

def is_connected():
    try:
        subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", "8.8.8.8"],
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def wait_for_wifi(timeout=60):
    print("Attente de connexion Wi-Fi...")
    start_time = time.time()
    while True:
        if is_connected():
            print("Wi-Fi connecté.")
            return True
        if time.time() - start_time > timeout:
            print(f"Pas de connexion après {timeout} secondes.")
            return False
        time.sleep(1)

def get_pending_files(folder):
    files = os.listdir(folder)
    return [os.path.join(folder, f) for f in files if f.endswith("_pending.png")]

def resend_pending_photos():
    """Renvoie toutes les photos non envoyées (_pending) si le Wi-Fi est disponible"""
    if not is_connected():
        print("Pas de Wi-Fi, impossible de renvoyer les anciennes photos.")
        return
    
    pending_files=get_pending_files("/home/pi/Agrocam")
    if not pending_files:
        print("Aucune photo en attente à renvoyer.")
        return
    
    print(f" {len(pending_files)} photo(s) en attente à renvoyer...")
    for filepath in pending_files:
        filename = os.path.basename(filepath)
        date_part = filename.split("_pending.png")[0].replace("photo", "")
        try:
            envoyer_sur_ftp(date_part)  # réutilise ta fonction d'envoi
            new_path = filepath.replace("_pending.png", "_sent.png")
            os.rename(filepath, new_path)
            print(f"Photo renvoyée et renommée : {new_path}")
            return True
        except Exception as e:
            print(f"Échec renvoi {filename} : {e}")

def main():
    setup_wittypi()
    #sleep(30) # waiting for wifi
    camera = initialize_camera(timeout=10)
    if camera is None:
        print("Caméra non disponible, on saute la prise de photo et l'envoi FTP.")
        return  # Sort directement du main → passe dans le finally
    initialize_GPIO()
    pwm = GPIO.PWM(pwm_gpio,50) #50 Hz
    pwm.start(0)
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d_%H%M%S")
    try:
        print("Démarrage du script Agrocam...")
        pwm.ChangeDutyCycle(angle_to_percent(0))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        filepath = prendre_photo(camera,current_date)
        print("photo prise")
        pwm.ChangeDutyCycle(angle_to_percent(90))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        print("Envoi de la photo et des métadonnées via HTTP...")
        wifi_ok = wait_for_wifi(timeout=60)
        
        if wifi_ok:
            envoyer_http(filepath)
            resend_pending_photos()
            print("Envoi sur FTP terminé")
        else:
            print("Envoi FTP annulé (pas de Wi-Fi)")

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
        #subprocess.run(['sudo', 'shutdown', '-h', 'now'])

if __name__ == "__main__":
    main()
