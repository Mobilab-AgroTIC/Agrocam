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
import piexif
from PIL import Image
from usb_storage import setup_storage_path
CREDENTIALS_FILE = "credentials.json"

with open(CREDENTIALS_FILE, "r") as f:
    credentials = json.load(f)


IMMICH_SERVER = credentials["upload"]["immich"]["url"]  # ex: "https://immich.example.com"
API_KEY = credentials["upload"]["immich"]["api_key"]              # Bearer token
ALBUM_ID = credentials["upload"]["immich"]["album_id"]            # Album cible
TIMEOUT = credentials["general"]["sending_timeout"]                                      # (connexion, lecture)
AGROCAM_SERVER = credentials["upload"]["agrocam"]["url"]
AGROCAM_NAME = credentials["upload"]["agrocam"]["name"]

# Numéro de la broche GPIO à utiliser pour le servo moteur principal
pwm_gpio = 18
# Numéro de la broche GPIO à utiliser pour le servo de filtre
filter_pwm_gpio = 19


# Numéro de la broche de debogage
controlPin = 24


def initialize_GPIO() :
    print("Initialisation des GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pwm_gpio, GPIO.OUT)
    GPIO.setup(filter_pwm_gpio, GPIO.OUT)
    GPIO.setup(controlPin, GPIO.IN)

def angle_to_percent (angle) :
    if angle > 180 or angle < 0 :
        return False
    start = 4
    end = 12.5
    ratio = (end - start)/180 #Calcul ratio from angle to percent

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

def move_step_motor(pin,angle):
    """
    Fonction à développer pour intégrer la rotation des filtres et obturateur avec un step motor
    """
def prendre_photo(voltage, extension="jpg", tag="",dir_path="/home/pi/Agrocam"):
    """
    Prend une photo et enregistre les métadonnées EXIF.
    
    :param voltage: Tension de la batterie (peut être None)
    :param extension: Extension du fichier avec point (ex: ".jpg" ou ".png")
    """
    # 🔧 FIX 1: Normaliser l'extension (toujours avec le point)
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%dT%H-%M-%S")
    timestamp_exif = now.strftime("%Y:%m:%d %H:%M:%S")
    
    # 🔧 FIX 2: Utiliser voltage "unknown" si None
    voltage_str = f"{voltage:.2f}" if voltage is not None else "unknown"

    filepath = f'{dir_path}/{timestamp_str}_{voltage_str}_{tag}_pending{extension}'
    
    # 1. La base de la commande
    cmd = ["sudo","rpicam-still", "-o", filepath]
 
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
        "--awb", "auto"
    ])
    if extension.lower() in [".jpg", ".jpeg"]:
        cmd.extend(["-q", str(credentials["photo"]["quality"])])
    if extension.lower() == ".png":
        cmd.extend(["--encoding", "png"])
 
    # Exécution
    print(cmd)
    subprocess.run(cmd)
    subprocess.run(["sudo", "chmod", "777", filepath],capture_output=True,text=True,timeout=5,check=True)
    
    # 3. Ajout de la localisation dans les EXIF
    try:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}
 
        # --- DATE ---
        exif_dict["0th"][piexif.ImageIFD.DateTime] = timestamp_exif.encode('ascii')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = timestamp_exif.encode('ascii')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = timestamp_exif.encode('ascii')
 
        # --- VOLTAGE ---
        # 🔧 FIX 3: Gérer voltage None dans la création du commentaire EXIF
        if voltage is not None:
            user_comment = f"BatteryVoltage={voltage:.2f}V"
        else:
            user_comment = "BatteryVoltage=unknown"
            
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
            b"ASCII\x00\x00\x00" + user_comment.encode("ascii")
        )
 
        # --- GPS ---
        latitude = float(credentials["photo"]["location"]["latitude"]) if credentials["photo"]["location"]["latitude"] else None
        longitude = float(credentials["photo"]["location"]["longitude"]) if credentials["photo"]["location"]["longitude"] else None
 
        if latitude is not None and longitude is not None:
            def to_deg(value):
                abs_value = abs(value)
                deg = int(abs_value)
                min_float = (abs_value - deg) * 60
                min_int = int(min_float)
                sec_float = (min_float - min_int) * 60
                # On utilise 10000 pour plus de précision sur les secondes
                return ((deg, 1), (min_int, 1), (int(sec_float * 10000), 10000))
 
            lat_ref = "N" if latitude >= 0 else "S"
            lon_ref = "E" if longitude >= 0 else "W"
 
            # On récupère les tuples (num, den) directement
            lat_deg = to_deg(latitude)
            lon_deg = to_deg(longitude)
 
            print(f"Enregistrement -> Lat: {lat_deg} {lat_ref}, Lon: {lon_deg} {lon_ref}")
 
            # Correction ici : on passe directement le résultat de to_deg
            exif_dict["GPS"] = {
                piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
                piexif.GPSIFD.GPSLatitudeRef: lat_ref,
                piexif.GPSIFD.GPSLatitude: lat_deg,
                piexif.GPSIFD.GPSLongitudeRef: lon_ref,
                piexif.GPSIFD.GPSLongitude: lon_deg,
            }
 
        # 🔧 FIX 4: Utiliser le format réel de l'image, pas l'extension supposée
        try:
            exif_bytes = piexif.dump(exif_dict)
            im = Image.open(filepath)
            
            # Récupérer le format réel de l'image
            actual_format = im.format  # Ex: "JPEG", "PNG"
            print(f"Format réel de l'image : {actual_format}")
            if actual_format:
                # PIL accepte les formats en majuscules ou minuscules
                save_format = actual_format.lower()
            else:
                # Fallback : utiliser l'extension fournie
                save_format = extension.lstrip('.').lower()
                if save_format in ["jpg", "jpeg"]:
                    save_format = "jpeg"
            
            im.save(filepath, save_format, exif=exif_bytes)
 
            if voltage is not None:
                print(f"[INFO] EXIF ajoutés : GPS + BatteryVoltage={voltage:.2f}V")
            else:
                print(f"[INFO] EXIF ajoutés : GPS + BatteryVoltage=unknown")
 
        except Exception as e:
            print(f"[ERROR] Impossible d'ajouter les EXIF : {e}")
 
    except Exception as e:
        print(f"[ERROR] Erreur lors du traitement des EXIF : {e}")
 
    return filepath


def envoyer_http_agrocam(filepath, server_url=AGROCAM_SERVER,metadata_key=AGROCAM_NAME,voltage=None,timeout=10):
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

    # 5. Préparation du fichier pour l'envoi
    upload_filename = f"{metadata_key}_{date_acquisition_iso}_{date_envoi_str}_{voltage}{extension}"
    

    metadata = {
        'key': metadata_key,
        'power_level': voltage,
        'date_acquisition': date_acquisition_iso,
    }

    try:
        with open(filepath, 'rb') as f:
            files = {'photo': (upload_filename, f, f'image/{extension.lstrip(".")}')}
            print(f"Envoi de {filename}")
            
            response = requests.post(
                server_url, 
                files=files, 
                data=metadata, 
                timeout=timeout
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

def envoyer_http_immich(filepath, server_url=IMMICH_SERVER, api_key=API_KEY, album_id=ALBUM_ID,voltage=None,timeout=10):
    """
    Envoie une photo vers un serveur Immich via l'API.
    
    :param file_path: Chemin local de l'image (ex: '/home/pi/photo.png')
    :param server_url: URL de votre instance (ex: 'http://192.168.1.50:2283')
    :param api_key: Votre clé API Immich
    """
    filename = os.path.basename(filepath)
    # Récupération des métadonnées du fichier pour l'ID unique
    stats = os.stat(filepath)
    
    # 1. Séparer le nom de l'extension (ex: .png ou .jpg)
    filename, extension = os.path.splitext(filename)
    # On nettoie l'URL pour s'assurer qu'elle finit par /api
    base_url = f"{server_url}/api/assets"


    
    headers = {
        'Accept': 'application/json',
        'x-api-key': api_key
    }
    
    # Données requises par Immich pour l'upload
    # deviceAssetId doit être unique pour éviter les doublons
    data = {
        'deviceAssetId': f'{filename}-{stats.st_mtime}',
        'deviceId': 'raspberry-pi',
        'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        'isFavorite': 'false'
    }

    print("données envoyées avec la photo : ",data)

    try:
        # --- ÉTAPE 1 : TÉLÉVERSEMENT ---
        with open(filepath, 'rb') as f:
            files = {'assetData': (filepath, f, f"image/{extension.lstrip('.')}")}
            response = requests.post(base_url, headers=headers, data=data, files=files,timeout=timeout)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Erreur Upload {response.status_code} : {response.text}")
            return None

        asset_info = response.json()
        asset_id = asset_info.get('id')
        print(f"✅ Photo envoyée (ID: {asset_id})")
        new_path = filepath.replace(f"_pending{extension}", f"_sent{extension}")
        os.rename(filepath, new_path)

        # --- ÉTAPE 2 : MISE À JOUR DE LA DESCRIPTION (Le voltage) ---
        if asset_id:
            if voltage is not None:
                desc = f"Niveau batterie: {float(voltage):.2f}V"
            else:
                desc = "Niveau batterie: inconnu"
            # L'URL pour modifier un asset est /api/assets/{id}
            update_url = f"{server_url.rstrip('/')}/api/assets/{asset_id}"
            update_payload = {
                'description': desc
            }
            # On utilise PUT pour mettre à jour les informations
            res_upd = requests.put(update_url, headers=headers, json=update_payload,timeout=timeout)
            if res_upd.status_code == 200:
                print(f"📝 Description mise à jour V")
            else:
                print(f"⚠️ Erreur Description : {res_upd.text}")

        # --- ÉTAPE 2 : AJOUT À L'ALBUM ---
        if asset_id and album_id:
            album_url = f"{server_url.rstrip('/')}/api/albums/{album_id}/assets"
            album_data = {
                'ids': [asset_id]
            }
            
            album_res = requests.put(album_url, headers=headers, json=album_data,timeout=timeout)
            
            if album_res.status_code in [200, 201]:
                print(f"📂 Photo ajoutée à l'album {album_id}")
            else:
                print(f"⚠️ Erreur Album {album_res.status_code} : {album_res.text}")
        
        return asset_info

    except Exception as e:
        print(f"⚠️ Erreur : {e}")
        return None

def get_pending_files(folder):
    files = os.listdir(folder)
    return [os.path.join(folder, f) for f in files if "pending" in f]

def resend_pending_photos(voltage,upload_type,dir_path):
    """Renvoie toutes les photos non envoyées (_pending) si le Wi-Fi est disponible"""
    if not is_connected():
        print("Pas de Wi-Fi, impossible de renvoyer les anciennes photos.")
        return
    
    if voltage is not None:
        if voltage > 8 or voltage < 5:
            pending_files=get_pending_files(dir_path)
            if not pending_files:
                print("Aucune photo en attente à renvoyer.")
                return
            
            print(f" {len(pending_files)} photo(s) en attente à renvoyer...")
            for filepath in pending_files:
                filename = os.path.basename(filepath)
                try:
                    if upload_type =="agrocam" :
                        envoyer_http_agrocam(filepath)
                    elif upload_type == "immich" :
                        envoyer_http_immich(filepath,timeout=TIMEOUT)
                    else:
                        print("upload_type inconnu : agrocam ? ou immich ?")
                except Exception as e:
                    print(f"Échec renvoi {filename} : {e}")
        else :
            print("Voltage de : ", voltage, " V insufisant pour envoyer les photos en attentes")
    else:
        print("Erreur : Impossible de lire le voltage, saut de la vérification.")
        return False
    
def set_startup_time(date, hour, minute, second):
    print("Configuration de l'heure de démarrage...")
    command_set_startup = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && set_startup_time {date} {hour} {minute} {second}'"

    subprocess.run(['sudo','bash', '-c', 'source /home/pi/wittypi/utilities.sh && net_to_system'],capture_output=True,text=True)
    subprocess.run(['sudo','bash', '-c', 'source /home/pi/wittypi/utilities.sh && system_to_rtc'],capture_output=True,text=True)
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
    
def is_wittypi_connected():
    """Vérifie si la WittyPi est accessible"""
    try:
        result = subprocess.run(
            ['sudo', 'bash', '-c', 'source /home/pi/wittypi/utilities.sh && get_input_voltage'],
            capture_output=True,
            text=True,
            timeout=1,
            check=True
        )
        # Si on a une tension valide, la WittyPi est connectée
        voltage = float(result.stdout.strip())
        print(f"WittyPi détectée, tension d'entrée : {voltage} V")
        return True
    except:
        print("WittyPi non détectée.")
        return False
    
def setup_wittypi():
    pulsing_interval = credentials["witty"]["pulsing_interval"] #13
    white_led_duration=credentials["witty"]["white_led_duration"] #0
    recovery_voltage=credentials["witty"]["recovery_voltage"] #0 for desactivating the recovery voltage
    threshold_voltage=credentials["witty"]["threshold_voltage"] #70 --> 7 volts

    cmd_pulse = f"""sudo bash -c 'I2C_BUS=1;  source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_PULSE_INTERVAL {pulsing_interval}'"""
    cmd_led = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_BLINK_LED {white_led_duration}'"""
    cmd_recovery_voltage=f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS  $I2C_CONF_RECOVERY_VOLTAGE {recovery_voltage}'"""
    cmd_threshold_voltage = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_LOW_VOLTAGE {threshold_voltage}'"""

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
    """Lance l'ordre de deconnexion puis reconnexion sans poser de questions."""
    # On utilise Popen pour ne pas bloquer le script
    subprocess.run(["sudo","nmcli","con","del",target_ssid],
                   stdout=None,
                   stderr=None) # Pour éviter un bug régulier
    subprocess.run(["sudo", "nmcli" ,"dev" ,"wifi" ,"rescan"])
    subprocess.run(["sudo","nmcli", "device", "wifi", "connect", target_ssid, "password", password],
                   stdout=None,
                   stderr=None)

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


def main():
    wittypi_connected = is_wittypi_connected()
    try:
        if wittypi_connected:
            setup_wittypi()
        initialize_GPIO()
        dir_path=setup_storage_path()
        servo_obturateur = GPIO.PWM(pwm_gpio, 50) # servo obturateur principal
        servo_filtre = GPIO.PWM(filter_pwm_gpio, 50) # servo filtre

        servo_obturateur.start(0)
        servo_filtre.start(0)

        if wittypi_connected :
            voltage = get_voltage()
        else:
            voltage = None
        print("Démarrage du script Agrocam...")

        # Position initiale du servo principal
        move_servo(servo_obturateur, 0)

        #double_capture = bool(credentials.get("photo", {}).get("double_capture", False))
        double_capture = bool(credentials["photo"]["double_capture"])
        filters = credentials["photo"]["filters"]

        # capture unique ou double selon configuration
        if double_capture and len(filters) >= 2:
            for index, step in enumerate(filters, start=1):
                angle = int(step.get("angle", ))
                tag = str(step.get("tag", ""))

                move_servo(servo_filtre, angle)
                filepath = prendre_photo(voltage, extension=credentials["photo"]["format"], tag=tag, dir_path=dir_path)
                print(f"Photo {index} ({tag}) prise : {filepath}")
        
            # repos filtre sur le premier angle
            move_servo(servo_filtre, int(filters[0].get("angle")))
        else:
            filepath = prendre_photo(voltage, extension=credentials["photo"]["format"], tag="notag", dir_path=dir_path)
            print(f"Photo prise : {filepath}")

        move_servo(servo_obturateur, 90)

        servo_obturateur.stop()
        servo_filtre.stop()

        wifi_ok = wait_for_wifi(credentials["wifi"]["timeout"])

        # on n'envoie pas la photo tant que l'agrocam n'a pas de name
        if credentials["upload"]["type"] == "immich":
            if credentials["upload"]["immich"]["album_id"] != "":
                if wifi_ok:
                    print("Envoi de la photo et des métadonnées via HTTP...")
                    envoyer_http_immich(filepath,
                                credentials["upload"]["immich"]["url"],
                                credentials["upload"]["immich"]["api_key"],
                                credentials["upload"]["immich"]["album_id"],
                                voltage,
                                timeout=TIMEOUT)
                    resend_pending_photos(voltage, credentials["upload"]["type"],dir_path=dir_path)
                else:
                    print("Envoi annulé (pas de Wi-Fi)")
            else:
                print("En attente d'un album_id")
        elif credentials["upload"]["type"] == "agrocam":
            if credentials["upload"]["agrocam"]["name"] != "":
                if wifi_ok:
                    print("Envoi de la photo et des métadonnées via HTTP...")
                    envoyer_http_agrocam(filepath,
                                credentials["upload"]["agrocam"]["url"],
                                credentials["upload"]["agrocam"]["name"],
                                voltage,
                                timeout=TIMEOUT)
                    resend_pending_photos(voltage, credentials["upload"]["type"],dir_path=dir_path)
                else:
                    print("Envoi annulé (pas de Wi-Fi)")
            else:
                print("En attente d'un name d'agrocam")

    except KeyboardInterrupt:
        pass

    finally:
        try:
            servo_obturateur.stop()
            servo_filtre.stop()
        except Exception:
            pass

        # Configuration WittyPi
        if wittypi_connected:
            if voltage is not None:
                if voltage >= (credentials["witty"]["threshold_voltage"]/10) + 0.5:
                    print("Tension suffisante, programmation du prochain déclenchement")
                    day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
                    set_startup_time(day, hour, minute, second)
                elif voltage < 5:
                    print("Alimentation par USB, programmation du prochain déclenchement")
                    day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
                    set_startup_time(day, hour, minute, second)
                else:
                    print("Tension insuffisante, pas de reprogrammation")
                    clear_next_startup()
            else :
                print("Impossible de lire la tension, programmation du prochain déclenchement par précaution")
                day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
                set_startup_time(day, hour, minute, second)

        # Mode Maintenance
        if GPIO.input(controlPin) == 1:
            print("Mode maintenance activé. Lancement de l'interface Flask...")
            subprocess.run(['sudo', 'systemctl', 'start', 'agrocam-flask.service'])
            while GPIO.input(controlPin) == 1:
                print("... En attente de la fin de maintenance ...")
                sleep(10)
            print("Mode maintenance terminé.")

        subprocess.run(['sudo', 'systemctl', 'stop', 'agrocam-flask.service'])
        print("Extinction du système...")
        GPIO.cleanup()
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])


if __name__ == "__main__":
    main()
