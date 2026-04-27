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
from wittypi import set_startup_time,clear_next_startup,calculate_next_startup_time,is_wittypi_connected,setup_wittypi, get_voltage
CREDENTIALS_FILE = "credentials.json"

with open(CREDENTIALS_FILE, "r") as f:
    credentials = json.load(f)


IMMICH_SERVER = credentials["upload"]["immich"]["url"]  # ex: "https://immich.example.com"
API_KEY = credentials["upload"]["immich"]["api_key"]              # Bearer token
ALBUM_ID = credentials["upload"]["immich"]["album_id"]            # Album cible
TIMEOUT = credentials["general"]["sending_timeout"]               # (connexion, lecture)
AGROCAM_SERVER = credentials["upload"]["agrocam"]["url"]
AGROCAM_NAME = credentials["upload"]["agrocam"]["name"]
DEBUG_MODE=credentials["general"]["debug_mode"]

# Numéro de la broche GPIO à utiliser pour le servo moteur principal
pwm_gpio = 18
# Numéro de la broche GPIO à utiliser pour le servo de filtre
filter_pwm_gpio = 19

# Jumper de mode : HIGH (jumper branché sur 3.3V) = config, LOW (absent) = normal
controlPin = 24


def initialize_GPIO():
    print("Initialisation des GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pwm_gpio, GPIO.OUT)
    GPIO.setup(filter_pwm_gpio, GPIO.OUT)
    # PUD_DOWN : sans jumper la broche est fermement à LOW → mode normal garanti
    GPIO.setup(controlPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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

def prendre_photo(voltage, extension="jpg", tag="", dir_path="/home/pi/Agrocam"):
    """
    Prend une photo et enregistre les métadonnées EXIF.

    :param voltage: Tension de la batterie (peut être None)
    :param extension: Extension du fichier avec point (ex: ".jpg" ou ".png")
    """
    if extension and not extension.startswith('.'):
        extension = '.' + extension

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%dT%H-%M-%S")
    timestamp_exif = now.strftime("%Y:%m:%d %H:%M:%S")

    voltage_str = f"{voltage:.2f}" if voltage is not None else "unknown"

    filepath = f'{dir_path}/{timestamp_str}_{voltage_str}_{tag}_pending{extension}'

    cmd = ["sudo", "rpicam-still", "-o", filepath]

    timeout_val = credentials["photo"].get("timeout", 1000)

    if timeout_val == 0:
        cmd.append("--immediate")
        cmd.extend(["-t", "1"])
    else:
        cmd.extend(["-t", str(timeout_val)])

    cmd.extend([
        "--width", str(credentials["photo"]["size"]["width"]),
        "--height", str(credentials["photo"]["size"]["height"]),
        "--awb", "auto"
    ])
    if extension.lower() in [".jpg", ".jpeg"]:
        cmd.extend(["-q", str(credentials["photo"]["quality"])])
    if extension.lower() == ".png":
        cmd.extend(["--encoding", "png"])

    print(cmd)
    subprocess.run(cmd)
    subprocess.run(["sudo", "chmod", "777", filepath], capture_output=True, text=True, timeout=5, check=True)

    try:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}

        exif_dict["0th"][piexif.ImageIFD.DateTime] = timestamp_exif.encode('ascii')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = timestamp_exif.encode('ascii')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = timestamp_exif.encode('ascii')

        if voltage is not None:
            user_comment = f"BatteryVoltage={voltage:.2f}V"
        else:
            user_comment = "BatteryVoltage=unknown"

        exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
            b"ASCII\x00\x00\x00" + user_comment.encode("ascii")
        )

        latitude = float(credentials["photo"]["location"]["latitude"]) if credentials["photo"]["location"]["latitude"] else None
        longitude = float(credentials["photo"]["location"]["longitude"]) if credentials["photo"]["location"]["longitude"] else None

        if latitude is not None and longitude is not None:
            def to_deg(value):
                abs_value = abs(value)
                deg = int(abs_value)
                min_float = (abs_value - deg) * 60
                min_int = int(min_float)
                sec_float = (min_float - min_int) * 60
                return ((deg, 1), (min_int, 1), (int(sec_float * 10000), 10000))

            lat_ref = "N" if latitude >= 0 else "S"
            lon_ref = "E" if longitude >= 0 else "W"

            lat_deg = to_deg(latitude)
            lon_deg = to_deg(longitude)

            print(f"Enregistrement -> Lat: {lat_deg} {lat_ref}, Lon: {lon_deg} {lon_ref}")

            exif_dict["GPS"] = {
                piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
                piexif.GPSIFD.GPSLatitudeRef: lat_ref,
                piexif.GPSIFD.GPSLatitude: lat_deg,
                piexif.GPSIFD.GPSLongitudeRef: lon_ref,
                piexif.GPSIFD.GPSLongitude: lon_deg,
            }

        try:
            exif_bytes = piexif.dump(exif_dict)
            im = Image.open(filepath)

            actual_format = im.format  # Ex: "JPEG", "PNG"
            print(f"Format réel de l'image : {actual_format}")
            if actual_format:
                save_format = actual_format.lower()
            else:
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


def envoyer_http_agrocam(filepath, server_url=AGROCAM_SERVER, metadata_key=AGROCAM_NAME, voltage=None, timeout=10):
    filename = os.path.basename(filepath)

    name_part, extension = os.path.splitext(filename)

    parts = name_part.split('_')

    date_acquisition_raw = parts[0]

    try:
        date_acquisition_dt = datetime.strptime(date_acquisition_raw, "%Y-%m-%dT%H-%M-%S")
        date_acquisition_iso = date_acquisition_dt.isoformat(timespec='seconds')
    except ValueError as e:
        print(f"Erreur format date dans le nom de fichier : {e}")
        return

    date_envoi = datetime.now(timezone.utc)
    date_envoi_str = date_envoi.strftime("%Y-%m-%dT%H:%M:%S")

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

def envoyer_http_immich(filepath, server_url=IMMICH_SERVER, api_key=API_KEY, album_id=ALBUM_ID, voltage=None, timeout=10):
    """
    Envoie une photo vers un serveur Immich via l'API.
    :param file_path: Chemin local de l'image (ex: '/home/pi/photo.png')
    :param server_url: URL de votre instance (ex: 'http://192.168.1.50:2283')
    :param api_key: Votre clé API Immich
    """
    filename = os.path.basename(filepath)
    stats = os.stat(filepath)

    filename, extension = os.path.splitext(filename)
    base_url = f"{server_url}/api/assets"

    headers = {
        'Accept': 'application/json',
        'x-api-key': api_key
    }

    data = {
        'deviceAssetId': f'{filename}-{stats.st_mtime}',
        'deviceId': 'raspberry-pi',
        'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        'isFavorite': 'false'
    }

    print("données envoyées avec la photo : ", data)

    try:
        with open(filepath, 'rb') as f:
            files = {'assetData': (filepath, f, f"image/{extension.lstrip('.')}")}
            response = requests.post(base_url, headers=headers, data=data, files=files, timeout=timeout)

        if response.status_code not in [200, 201]:
            print(f"❌ Erreur Upload {response.status_code} : {response.text}")
            return None

        asset_info = response.json()
        asset_id = asset_info.get('id')
        print(f"✅ Photo envoyée (ID: {asset_id})")
        new_path = filepath.replace(f"_pending{extension}", f"_sent{extension}")
        os.rename(filepath, new_path)

        if asset_id:
            if voltage is not None:
                desc = f"Niveau batterie: {float(voltage):.2f}V"
            else:
                desc = "Niveau batterie: inconnu"
            update_url = f"{server_url.rstrip('/')}/api/assets/{asset_id}"
            update_payload = {'description': desc}
            res_upd = requests.put(update_url, headers=headers, json=update_payload, timeout=timeout)
            if res_upd.status_code == 200:
                print(f"📝 Description mise à jour V")
            else:
                print(f"⚠️ Erreur Description : {res_upd.text}")

        if asset_id and album_id:
            album_url = f"{server_url.rstrip('/')}/api/albums/{album_id}/assets"
            album_data = {'ids': [asset_id]}

            album_res = requests.put(album_url, headers=headers, json=album_data, timeout=timeout)

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

def resend_pending_photos(voltage, upload_type, dir_path):
    """Renvoie toutes les photos non envoyées (_pending) si le Wi-Fi est disponible"""
    if not is_connected():
        print("Pas de Wi-Fi, impossible de renvoyer les anciennes photos.")
        return

    if voltage is not None:
        if voltage > 8 or voltage < 5:
            pending_files = get_pending_files(dir_path)
            if not pending_files:
                print("Aucune photo en attente à renvoyer.")
                return

            print(f" {len(pending_files)} photo(s) en attente à renvoyer...")
            for filepath in pending_files:
                filename = os.path.basename(filepath)
                try:
                    if upload_type == "agrocam":
                        envoyer_http_agrocam(filepath)
                    elif upload_type == "immich":
                        envoyer_http_immich(filepath, timeout=TIMEOUT)
                    else:
                        print("upload_type inconnu : agrocam ? ou immich ?")
                except Exception as e:
                    print(f"Échec renvoi {filename} : {e}")
        else:
            print("Voltage de : ", voltage, " V insufisant pour envoyer les photos en attentes")
    else:
        print("Erreur : Impossible de lire le voltage, saut de la vérification.")
        return False



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
        res = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=2)
        return res.stdout.strip()
    except:
        return None

def connect_wifi(target_ssid, password):
    """Lance l'ordre de deconnexion puis reconnexion sans poser de questions."""
    subprocess.run(["sudo", "nmcli", "con", "del", target_ssid],
                   stdout=None,
                   stderr=None)
    subprocess.run(["sudo", "nmcli", "dev", "wifi", "rescan"])
    subprocess.run(["sudo", "nmcli", "device", "wifi", "connect", target_ssid, "password", password],
                   stdout=None,
                   stderr=None)

def wait_for_wifi(timeout=60):
    target = credentials["wifi"]["ssid"]
    password = credentials["wifi"]["password"]

    print(f"Objectif : Connexion à {target}...")
    start_time = datetime.now()

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
            connect_wifi(target, password)

        sleep(3)

    if is_connected():
        return True
    else:
        print(f"Échec : Cible {target} non rejointe après {timeout}s.")
        return False


# ── Gestion du hotspot pour le mode configuration ────────────────────────────

def get_serial_suffix():
    """Retourne les 4 derniers caractères du numéro de série du Raspberry."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Serial"):
                    return line.split(":")[-1].strip()[-4:].upper()
    except Exception:
        pass
    return "0000"

def start_hotspot():
    """
    Crée un point d'accès WiFi via nmcli.
    NetworkManager gère le DHCP automatiquement (IP du Pi : 10.42.0.1).
    """
    ssid = f"Agrocam-{get_serial_suffix()}"
    password = "agrocam123"
    print(f"[CONFIG] Création du hotspot : SSID={ssid}  Password={password}")
    result = subprocess.run(
        ["sudo", "nmcli", "device", "wifi", "hotspot",
         "ifname", "wlan0", "ssid", ssid, "password", password],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0:
        print(f"[CONFIG] ✅ Hotspot actif")
        print(f"[CONFIG]    → Connectez-vous à '{ssid}'")
        print(f"[CONFIG]    → Ouvrez http://10.42.0.1:5000")
        return True
    else:
        print(f"[CONFIG] ⚠️  Erreur hotspot : {result.stderr.strip()}", file=sys.stderr)
        return False

def stop_hotspot():
    """Arrête le hotspot nmcli."""
    subprocess.run(
        ["sudo", "nmcli", "connection", "down", "Hotspot"],
        capture_output=True, timeout=10
    )
    print("[CONFIG] Hotspot arrêté.")


# ── Point d'entrée principal ──────────────────────────────────────────────────

def main():
    # ── Lecture du jumper AVANT toute initialisation ──────────────────────
    # On configure uniquement controlPin ici ; initialize_GPIO() viendra plus tard
    # si on est en mode normal.
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(controlPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    sleep(0.1)  # Laisser stabiliser le niveau électrique
    config_mode = GPIO.input(controlPin) == GPIO.HIGH
    print(f"Jumper détecté : {config_mode} (HIGH → config, LOW → normal)")
    # ══════════════════════════════════════════════════════════════════════
    # MODE CONFIGURATION  (jumper présent → GPIO HIGH)
    # ══════════════════════════════════════════════════════════════════════
    if config_mode and not DEBUG_MODE :
        print("[CONFIG] Jumper détecté → MODE CONFIGURATION")
        try:
            start_hotspot()
            subprocess.run(
                ["sudo", "systemctl", "start", "agrocam-flask.service"],
                capture_output=True, timeout=5
            )
            print("[CONFIG] Interface web démarrée")
            print("[CONFIG] Retirez le jumper pour terminer et redémarrer...")

            while GPIO.input(controlPin) == GPIO.HIGH:
                sleep(5)

            print("[CONFIG] Jumper retiré → fin du mode configuration")

        finally:
            subprocess.run(
                ["sudo", "systemctl", "stop", "agrocam-flask.service"],
                capture_output=True
            )
            stop_hotspot()
            GPIO.cleanup()
            print("[CONFIG] Redémarrage...")
            subprocess.run(["sudo", "reboot"])

        return  # Sécurité, reboot ci-dessus prend la main

    # ══════════════════════════════════════════════════════════════════════
    # MODE NORMAL  (jumper absent → GPIO LOW)
    # ══════════════════════════════════════════════════════════════════════
    wittypi_connected = is_wittypi_connected()
    voltage = None  # Déclaré ici pour être accessible dans le bloc finally

    try:
        if wittypi_connected:
            setup_wittypi()
        initialize_GPIO()
        dir_path = setup_storage_path()

        servo_obturateur = GPIO.PWM(pwm_gpio, 50)
        servo_filtre = GPIO.PWM(filter_pwm_gpio, 50)

        servo_obturateur.start(0)
        servo_filtre.start(0)

        if wittypi_connected:
            voltage = get_voltage()
        print("Démarrage du script Agrocam...")

        move_servo(servo_obturateur, 0)

        double_capture = bool(credentials["photo"]["double_capture"])
        filters = credentials["photo"]["filters"]

        if double_capture and len(filters) >= 2:
            for index, step in enumerate(filters, start=1):
                angle = int(step.get("angle",))
                tag = str(step.get("tag", ""))

                move_servo(servo_filtre, angle)
                filepath = prendre_photo(voltage, extension=credentials["photo"]["format"], tag=tag, dir_path=dir_path)
                print(f"Photo {index} ({tag}) prise : {filepath}")

            move_servo(servo_filtre, int(filters[0].get("angle")))
        else:
            filepath = prendre_photo(voltage, extension=credentials["photo"]["format"], tag="notag", dir_path=dir_path)
            print(f"Photo prise : {filepath}")

        move_servo(servo_obturateur, 90)

        servo_obturateur.stop()
        servo_filtre.stop()

        wifi_ok = wait_for_wifi(credentials["wifi"]["timeout"])

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
                    resend_pending_photos(voltage, credentials["upload"]["type"], dir_path=dir_path)
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
                    resend_pending_photos(voltage, credentials["upload"]["type"], dir_path=dir_path)
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

        # Configuration WittyPi pour le prochain déclenchement
        if wittypi_connected:
            if voltage is not None:
                if voltage >= (credentials["witty"]["threshold_voltage"] / 10) + 0.5:
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
            else:
                print("Impossible de lire la tension, programmation du prochain déclenchement par précaution")
                day, hour, minute, second = calculate_next_startup_time(credentials["general"]["trigger_times"])
                set_startup_time(day, hour, minute, second)
                
        if not DEBUG_MODE:
            print("Extinction du système...")
            GPIO.cleanup()
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])


if __name__ == "__main__":
    main()