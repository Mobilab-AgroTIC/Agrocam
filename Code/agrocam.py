#!/usr/bin python3
import RPi.GPIO as GPIO
# from gpiozero import Servo
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

def prendre_photo(voltage):
    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y-%m-%dT%H-%M-%S")
    filepath = f'/home/pi/Agrocam/{timestamp_str}_{voltage}_pending{credentials["photo"]["extension"]}'
    
    # 1. La base de la commande
    cmd = ["rpicam-still", "-o", filepath]

    # 2. Gestion du timeout et de l'immédiat
    timeout_val = credentials["photo"].get("timeout", 1000) # 1000 par défaut si absent
    
    if timeout_val == 0:
        # Si l'utilisateur met 0, on considère qu'il veut l'instantané
        cmd.append("--immediate")
        cmd.extend(["-t", "1"]) # On met 1ms car -t 0 bloquerait le script
    else:
        cmd.extend(["-t", str(timeout_val)])

    # 3. Ajout des autres paramètres
    cmd.extend([
        "--width", str(credentials["photo"]["size"]["width"]),
        "--height", str(credentials["photo"]["size"]["height"]),
        "-q", str(credentials["photo"]["quality"])
    ])


    # Exécution
    print(cmd)
    subprocess.run(cmd)
    return filepath


def prendre_photo_legacy (camera,voltage):
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

def envoyer_http(filepath, voltage=None):
    url = credentials["general"]["url_api"]
    filename = os.path.basename(filepath)
    
    # 1. Séparer le nom de l'extension (ex: .png ou .jpg)
    name_part, extension = os.path.splitext(filename)
    
    # 2. Découper le nom par les underscores
    # Format attendu : "2025-08-12T14-30-00_4.79_pending"
    parts = name_part.split('_')
    
    # La date est toujours le premier élément avant le premier "_"
    date_acquisition_raw = parts[0] 
    
    # 3. Conversion de la date
    try:
        date_acquisition_dt = datetime.strptime(date_acquisition_raw, "%Y-%m-%dT%H-%M-%S")
        date_acquisition_iso = date_acquisition_dt.isoformat(timespec='seconds')
    except ValueError as e:
        print(f"Erreur format date dans le nom de fichier : {e}")
        return # On arrête si la date est illisible

    # 4. Dates d'envoi et métadonnées
    date_envoi = datetime.now(timezone.utc)
    date_envoi_str = date_envoi.strftime("%Y-%m-%dT%H:%M:%S")
    metadata_key = credentials["general"]["name"]

    # 5. Préparation du fichier pour l'envoi
    # On garde l'extension d'origine pour le serveur
    upload_filename = f"{metadata_key}_{date_acquisition_iso}_{date_envoi_str}_{voltage}{extension}"
    
    # Déterminer le type MIME dynamiquement
    mime_type = "image/jpeg" if extension.lower() in [".jpg", ".jpeg"] else "image/png"

    metadata = {
        'key': metadata_key,
        'power_level': voltage,
        'date_acquisition': date_acquisition_iso,
    }

    try:
        with open(filepath, 'rb') as f:
            files = {'photo': (upload_filename, f, mime_type)}
            print(f"Envoi de {filename} ({mime_type})...")
            
            response = requests.post(
                url, 
                files=files, 
                data=metadata, 
                timeout=credentials["general"].get("sending_timeout", 30)
            )
            print("Headers réponse :", response.headers)
            response.raise_for_status()
            
        if response.status_code in [200, 201]:
            print("Photo envoyée avec succès !")
            # On remplace "_pending" par "_sent" tout en gardant la bonne extension
            new_path = filepath.replace("_pending", "_sent")
            os.rename(filepath, new_path)
        
    except requests.exceptions.RequestException as e:
        print(f"Échec de la requête HTTP : {e}", file=sys.stderr)
    except requests.exceptions.HTTPError as e:
        response = e.response
        print("❌ Erreur HTTP", file=sys.stderr)
        print(f"Status code : {response.status_code}", file=sys.stderr)
        print("Headers réponse :", file=sys.stderr)
        print(response.headers, file=sys.stderr)
        print("Corps de la réponse :", file=sys.stderr)
        print(response.text, file=sys.stderr)

def envoyer_http_legacy(filepath,voltage=None):
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
    upload_filename = f"{metadata_key}_{date_acquisition_iso}_{date_envoi_str}_{voltage}_{credentials["general"]["extension"]}"

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
             # Ajout du timeout ici (en secondes)
             response = requests.post(url, files=files, data=data, timeout=credentials["general"]["sending_timeout"])
             
             # Vérifie si le serveur a répondu avec une erreur (4xx ou 5xx)
             response.raise_for_status()

             #response = requests.post(url, files=files, data=data)

         if response.status_code in [200, 201]:
             print("Photo and metadata sent successfully! Status:", response.status_code)
             new_path = filepath.replace("_pending", "_sent")
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

def clear_next_startup():
    print("Suppression du prochain déclenchement Witty Pi...")
    subprocess.run([
        'sudo', 'bash', '-c',
        'source /home/pi/wittypi/utilities.sh && clear_startup_time'],
        stdout=None,
        stderr=None)

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
    recovery_voltage=credentials["witty"]["recovery_voltage"] #0 for desactivating the recovery voltage
    threshold_voltage=credentials["witty"]["threshold_voltage"] #70 --> 7 volts
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

def is_connected():
    try:
        subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", "8.8.8.8"],
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False
    
def get_current_ssid():
    """Vérification instantanée du SSID actuel via le kernel."""
    try:
        # iwgetid est beaucoup plus léger que nmcli pour un Pi Zero
        res = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=2)
        return res.stdout.strip()
    except:
        return None

def connect_wifi(target_ssid, password):
    """Lance l'ordre de connexion sans poser de questions."""
    # On utilise Popen pour ne pas bloquer le script
    subprocess.run(["sudo","nmcli","con","del",target_ssid],
                   stdout=None,
                   stderr=None) # Pour éviter un bug régulier
    subprocess.run(["sudo", "nmcli" ,"dev" ,"wifi" ,"rescan"])
    subprocess.run(["sudo","nmcli", "device", "wifi", "connect", target_ssid, "password", password],
                   stdout=None,
                   stderr=None)

def connect_wifi_propposition_chatgpt(target_ssid, password):
    '''
    Pour éviter l'erreur 
    Error: 802-11-wireless-security.key-mgmt: property is missing.

    Qui vient du fait que lorsque qu'on essaye de se connecter à un ssid déjà connu, 
    nmcli réutilise la connexion existante MAIS si cette connexion est :
    incomplète et/ou corrompue et/ou créée sans sécurité explicite. 
    Il n’écrase pas les paramètres manquants, d’où key-mgmt missing
    '''
    # tentative avec une connexion existante
    result = subprocess.run(
        ["nmcli", "con", "up", "id", target_ssid],
        stdout=None,
        stderr=None
    )

    if result.returncode == 0:
        return  # succès

    # sinon on crée la connexion proprement
    subprocess.run(["nmcli", "dev", "wifi", "rescan"])
    subprocess.run(
        ["nmcli", "dev", "wifi", "connect", target_ssid, "password", password],
        stdout=None,
        stderr=None
    )


def wait_for_wifi(timeout=60):
    target = credentials["wifi"]["ssid"]
    password = credentials["wifi"]["password"]
    
    print(f"Objectif : Connexion à {target}...")
    start_time = datetime.now()
    
    # ÉTAPE 1 : On lance la connexion UNE SEULE FOIS au début
    # (connect_wifi utilise Popen, donc c'est instantané)
    #connect_wifi(target, password)

    # ÉTAPE 2 : On attend que DEUX conditions soient réunies :
    # 1. Être sur le bon SSID
    # 2. Avoir accès à Internet
    while datetime.now() - start_time < timedelta(seconds=timeout):
        current_ssid = get_current_ssid()
        
        if current_ssid == target:
            if is_connected():
                print(f"Succès : Connecté à {target} avec accès Internet.")
                return True
            else:
                print(f"Sur le bon SSID ({target}), attente de l'IP/Internet...")
        else:
            print(f"Mauvais SSID détecté ({current_ssid}). Tentative de bascule...")
            # On relance l'ordre de connexion au cas où NM aurait échoué
            connect_wifi(target, password)

        sleep(3) # On laisse 3s au Pi Zero pour respirer entre chaque check
    # Finalement si on n'arrive pas à se connecter au ssid souhaité mais qu'on a internet quand même c'est bon
    if is_connected():
        return True
    else:
        print(f"Échec : Cible {target} non rejointe après {timeout}s.")
        return False

def get_pending_files(folder):
    files = os.listdir(folder)
    return [os.path.join(folder, f) for f in files if "pending" in f]

def resend_pending_photos(voltage):
    """Renvoie toutes les photos non envoyées (_pending) si le Wi-Fi est disponible"""
    if not is_connected():
        print("Pas de Wi-Fi, impossible de renvoyer les anciennes photos.")
        return
    
    if voltage is not None:
        if voltage > 8 or voltage < 5:
            pending_files=get_pending_files("/home/pi/Agrocam")
            if not pending_files:
                print("Aucune photo en attente à renvoyer.")
                return
            
            print(f" {len(pending_files)} photo(s) en attente à renvoyer...")
            for filepath in pending_files:
                filename = os.path.basename(filepath)
                # date_part = filename.split("_pending.png")[0]
                try:
                    envoyer_http(filepath,voltage)
                except Exception as e:
                    print(f"Échec renvoi {filename} : {e}")
        else :
            print("Voltage de : ", voltage, " V insufisant pour envoyer les photos en attentes")
    else:
        print("Erreur : Impossible de lire le voltage, saut de la vérification.")
        return False
    
    


def main():
    try:
        setup_wittypi()
        initialize_GPIO()
        pwm = GPIO.PWM(pwm_gpio,50) #50 Hz
        pwm.start(0)
        voltage = get_voltage()
        print("Démarrage du script Agrocam...")
        pwm.ChangeDutyCycle(angle_to_percent(0))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        filepath = prendre_photo(voltage)
        print(f"Photo prise : {filepath}")
        pwm.ChangeDutyCycle(angle_to_percent(90))
        sleep(0.2)
        pwm.ChangeDutyCycle(0)
        sleep(0.1)
        pwm.stop()
        wifi_ok = wait_for_wifi(credentials["wifi"]["timeout"])
        
        # on n'envoie pas la photo tant que l'agrocam n'a pas de name
        if credentials["general"]["name"]!="":
            if wifi_ok:
                print("Envoi de la photo et des métadonnées via HTTP...")
                envoyer_http(filepath,voltage)
                resend_pending_photos(voltage)
            else:
                print("Envoi annulé (pas de Wi-Fi)")
        else :
            print("En attente d'un name d'agrocam")

    except KeyboardInterrupt:
        pass

    finally:
        # Configuration WittyPi
        if voltage >= (credentials["witty"]["threshold_voltage"]/10)+0.5:
            print("Tension suffisante, programmation du prochain déclenchement")
            day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
            set_startup_time(day, hour, minute, second)
        elif voltage < 5 :
            print("Alimentation par USB, programmation du prochain déclenchement")
            day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
            set_startup_time(day, hour, minute, second)
        else :
            print("Tension insuffisante, pas de reprogrammation")
            clear_next_startup()
            
        # Mode Maintenance
        if GPIO.input(controlPin) == 1:
            print("Mode maintenance activé. Lancement de l'interface Flask...")
            # On lance Flask en arrière-plan
            subprocess.run(['sudo', 'systemctl', 'start', 'agrocam-flask.service'])
            
            # On attend que l'utilisateur relâche le bouton/switch
            while GPIO.input(controlPin) == 1:
                print("... En attente de la fin de maintenance ...")
                sleep(10) # 10s suffit largement et sollicite moins le CPU
            
            print("Mode maintenance terminé.")
        # Extinction finale
        subprocess.run(['sudo', 'systemctl', 'stop', 'agrocam-flask.service'])
        print("Extinction du système...")
        GPIO.cleanup()
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])


if __name__ == "__main__":
    main()
