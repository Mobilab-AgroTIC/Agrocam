#!/usr/bin python3
import RPi.GPIO as GPIO
# from gpiozero import Servo
from picamera2 import Picamera2, Preview
# from libcamera import Transform
from time import sleep
import requests
from datetime import datetime, timedelta, timezone, time
import subprocess
import os
import sys
import json

CREDENTIALS_FILE = "credentials.json"

with open(CREDENTIALS_FILE, "r") as f:
    credentials = json.load(f)

# Numéro de la broche GPIO à utiliser pour le servo moteur
pwm_gpio = 18

# Numéro de la broche de debogage
controlPin = 24


def initialize_camera(timeout=10):
    print("Initialisation de la caméra...")
    start_time = datetime.now()
    
    while True:
        try:
            cam = Picamera2()
            camera_config = cam.create_still_configuration(
                main={"size": (credentials["photo"]["size"]["width"], credentials["photo"]["size"]["height"])},
                lores={"size": (640, 480)},
                display="main"
            )
            cam.configure(camera_config)
            cam.set_controls({"AfMode": 2})
            print("Caméra initialisée.")
            return cam
        except Exception as e:
            if datetime.now() - start_time > timeout:
                print(f"Timeout ({timeout}s) : impossible d'initialiser la caméra.")
                return None
            print("Erreur initialisation caméra, nouvelle tentative...")
            sleep(1)

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

def prendre_photo(camera,voltage):
    camera.start_preview()
    camera.start() 
    sleep(1)
    now_utc=datetime.now(timezone.utc)  # date acquisition en UTC, objet datetime
    # Format sans ':' pour nom fichier
    timestamp_str = now_utc.strftime("%Y-%m-%dT%H-%M-%S")
    os.makedirs(os.path.dirname("/home/pi/Agrocam"), exist_ok=True)
    filepath = f'/home/pi/Agrocam/{timestamp_str}_{voltage}_pending.png'
    camera.capture_file(filepath)
    camera.stop_preview()
    camera.close()
    return filepath  # On retourne le chemin pour savoir où est la photo

def envoyer_http(filepath,voltage=None):
    # URL of the API endpoint
    #url = f'https://agrocam.agrotic-dev.org/api/upload'
    url=credentials["general"]["url_api"]

    ## Récupération de la date d'acquisition depuis le nom du fichier
    # On suppose que le nom du fichier est au format "2025-08-12T14-30-00.png"
    # On enlève l'extension pour obtenir "2025-08-12T14-30-00"
    # On utilise datetime.strptime pour convertir en objet datetime
    filename = os.path.basename(filepath)
    # Le nom est "2025-08-12T14-30-00_4.79_pending.png", on récupère la date
    # On enlève la partie "_pending.png" pour obtenir juste la date
    filename_without_extension = filename.replace("_pending.png", "")
    # On enlève la partie "_4.79" pour obtenir juste la date
    if "_" in filename_without_extension:
        filename_without_extension = filename_without_extension.split("_")[0]
    # Recréer datetime UTC depuis le nom de fichier
    date_acquisition_str = datetime.strptime(filename_without_extension, "%Y-%m-%dT%H-%M-%S")
    # Convertir en date ISO pour l'API
    date_acquisition_iso = date_acquisition_str.isoformat(timespec='seconds')

    ## Récupération de la date d'envoi
    # On utilise datetime.now() pour obtenir la date actuelle en UTC
    # et on la formate en chaîne ISO 8601
    date_envoi = datetime.now(timezone.utc)
    date_envoi_str = date_envoi.strftime("%Y-%m-%dT%H:%M:%S")


    # On formate la tension pour le nom de fichier
    print(f"Successfully obtained voltage: {voltage} V")
    
    # Define the key used in metadata and filename
    metadata_key = credentials["general"]["name"] # Replace with actual key variable if dynamic

    # Construct the desired filename for the upload, including key, date, and voltage
    upload_filename = f"{metadata_key}_{date_acquisition_iso}_{date_envoi_str}_{voltage}.png"

    # Populate metadata
    metadata = {
        'key': metadata_key,
        'power_level': voltage, # Use the float voltage (will be None if conversion failed)
        'date_acquisition': date_acquisition_iso,
    }

    try:
         # Open the image file and prepare for upload
         with open(filepath, 'rb') as f:
             # 'files' dictionary format: {'field_name': ('filename_for_server', file_object, 'content_type')}
             files = {'photo': (upload_filename, f, 'image/png')}
             data = metadata # Metadata is sent as form fields

             print(f"Sending data via HTTP POST...")

             response = requests.post(url, files=files, data=data)

         if response.status_code in [200, 201]:
             print("Photo and metadata sent successfully! Status:", response.status_code)
             new_path = filepath.replace("_pending.png", "_sent.png")
             os.rename(filepath, new_path)
         else:
             print(f"Error sending data. Status code: {response.status_code}", file=sys.stderr)
             print("Response body:", response.text, file=sys.stderr)

    except FileNotFoundError:
         print(f"Error: Image file not found at {filepath}.", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}", file=sys.stderr)
    except Exception as e:
         print(f"An unexpected error occurred during HTTP request or file handling: {e}", file=sys.stderr)


def set_startup_time(date, hour, minute, second):
    print("Configuration de l'heure de démarrage...")
    command_set_startup = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && set_startup_time {date} {hour} {minute} {second}'"    
    command_net_to_system = subprocess.run(['sudo','bash', '-c', 'source /home/pi/wittypi/utilities.sh && net_to_system'],capture_output=True,text=True)
    command_system_to_rtc = subprocess.run(['sudo','bash', '-c', 'source /home/pi/wittypi/utilities.sh && system_to_rtc'],capture_output=True,text=True)
    subprocess.run(['bash', '-c',command_set_startup ],capture_output=True,text=True)
    
    print(command_set_startup)

def calculate_next_startup_time(trigger_times):
    now = datetime.now()
    today = now.date()

    # Convertir chaînes en objets time si nécessaire
    times = []
    for t in trigger_times:
        if isinstance(t, str):
            h, m, s = map(int, t.split(":"))
            times.append(time(h, m, s))
        else:
            times.append(t)

    # Créer des datetime pour aujourd'hui
    trigger_datetimes_today = [datetime.combine(today, t) for t in times]

    # Filtrer pour les déclenchements à venir
    upcoming_triggers = [t for t in trigger_datetimes_today if t > now]

    # Prochain déclenchement
    if upcoming_triggers:
        next_startup = upcoming_triggers[0]
    else:
        next_startup = trigger_datetimes_today[0] + timedelta(days=1)

    print("next startup : ", next_startup)

    return next_startup.day, next_startup.hour, next_startup.minute, next_startup.second
    
def setup_wittypi():
    pulsing_interval = credentials["witty"]["pulsing_interval"] #13
    white_led_duration=credentials["witty"]["white_led_duration"] #0
    recovery_voltage=credentials["witty"]["recovery_voltage"] #20
    threshold_voltage=credentials["witty"]["threshold_voltage"] #70
    cmd_pulse = f"""sudo bash -c 'I2C_BUS=1;  source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_PULSE_INTERVAL {credentials["witty"]["pulsing_interval"]}'"""
    cmd_led = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_BLINK_LED {credentials["witty"]["white_led_duration"]}'"""
    cmd_recovery_voltage=f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS  $I2C_CONF_RECOVERY_VOLTAGE {credentials["witty"]["recovery_voltage"]}'"""
    cmd_threshold_voltage = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_LOW_VOLTAGE {credentials["witty"]["threshold_voltage"]}'"""

    subprocess.run(cmd_led, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_pulse, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_recovery_voltage, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_threshold_voltage, shell=True, capture_output=True, text=True)

def get_voltage():
    """Récupère la tension d'entrée via le script WittyPi"""
    try:
        command = subprocess.run(
            ['sudo','bash', '-c', 'source /home/pi/wittypi/utilities.sh && get_input_voltage'],
            capture_output=True,
            text=True,
            check=True
        )
        voltage_str = command.stdout.strip()
        voltage = float(voltage_str)
        print(f"Tension d'entrée : {voltage} V")
        return voltage
    except FileNotFoundError:
        print("Erreur : le script 'get_input_voltage' n'a pas été trouvé.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution du script : {e}", file=sys.stderr)
        print(f"Stderr : {e.stderr}", file=sys.stderr)
    except ValueError:
        print(f"Erreur de conversion de la lecture de tension '{voltage_str}' en float. Sortie inattendue.", file=sys.stderr)   

""" 
def connect_wifi(ssid, password):
    # Vérifie si la connexion existe déjà
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME", "connection", "show"],
        capture_output=True, text=True
    )
    connections = result.stdout.splitlines()
    
    if ssid in connections:
        print(f"Connexion {ssid} déjà configurée, pas de nouvelle tentative.")
        return
    
    # Sinon, on se connecte
    try:
        subprocess.run(
            ["nmcli", "device", "wifi", "connect", ssid, "password", password],
            check=True
        )
        print(f"Tentative de connexion à {ssid}...")
    except subprocess.CalledProcessError:
        print(f"Impossible de se connecter à {ssid}")

"""

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
    start_time = datetime.now()
    while True:
        if is_connected():
            print("Wi-Fi connecté.")
            return True
        if datetime.now() - start_time > timedelta(seconds=timeout):
            print(f"Pas de connexion après {timeout} secondes.")
            return False
             
        sleep(1)

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
        date_part = filename.split("_pending.png")[0]
        try:
            envoyer_http(filepath)
            return True
        except Exception as e:
            print(f"Échec renvoi {filename} : {e}")


def main():
    try:
        setup_wittypi()
        #sleep(30) # waiting for wifi
        camera = initialize_camera(timeout=10)
        if camera is None:
            print("Caméra non disponible, on saute la prise de photo et l'envoi HTPP.")
            return  # Sort directement du main → passe dans le finally
        initialize_GPIO()
        pwm = GPIO.PWM(pwm_gpio,50) #50 Hz
        pwm.start(0)
        voltage = get_voltage()
        print("Démarrage du script Agrocam...")
        pwm.ChangeDutyCycle(angle_to_percent(0))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        filepath = prendre_photo(camera,voltage)
        print(f"Photo prise : {filepath}")
        pwm.ChangeDutyCycle(angle_to_percent(90))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        pwm.stop()
        camera.close()
        wifi_ok = wait_for_wifi(credentials["wifi"]["timeout"])
        
        if wifi_ok:
            print("Envoi de la photo et des métadonnées via HTTP...")
            envoyer_http(filepath,voltage)
            resend_pending_photos()
            print("Envoi terminé")
        else:
            print("Envoi annulé (pas de Wi-Fi)")

    except KeyboardInterrupt:
        pass

    finally:
        # Calcul de la prochaine date de déclenchement et enregistrement dans Wittypi
        day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
        set_startup_time(day, hour, minute, second)
        i=1
        activation_hostpot = False
        while (GPIO.input(controlPin) == 1) :
            sleep(5)
            print("ControlPin is not LOW. i = ", i)
            i += 1

        GPIO.cleanup()
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])

if __name__ == "__main__":
    main()
