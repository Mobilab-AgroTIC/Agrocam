#!/usr/bin python3
import RPi.GPIO as GPIO
from gpiozero import Servo
from picamera2 import Picamera2, Preview
# from libcamera import Transform
from time import sleep
from ftplib import FTP
import requests
from datetime import datetime, timedelta, timezone
import subprocess
import credentials as credentials
import sys

# Numéro de la broche GPIO à utiliser pour le servo moteur
pwm_gpio = 18

# Numéro de la broche de debogage
controlPin = 24

# Configuration de la caméra
camera = Picamera2()

# Configuration for rotating picture
# Ci-dessous d'anciennes config qui ne minimise la taille des images (<500 ko)
# camera_config = camera.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="main",transform=Transform(180))
camera_config = camera.create_still_configuration(main={"size": (4608, 2592)}, lores={"size": (640, 480)}, display="main")
# La config ci-dessous maximise la taille et donc la qualité de l'image
camera.configure(camera_config)

camera.set_controls({"AfMode": 2}) #Autofocus  
#camera.set_controls({"LensPosition": 2.0})
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
     
    sleep(1)
    camera.capture_file('/home/pi/Agrocam/photo'+date+'.png')
    camera.stop_preview()
    camera.close()

def envoyer_http(date_for_filename_part):
    # URL of the API endpoint
    url = f'https://agrocam.agrotic-dev.org/api/upload'

    now = datetime.now()

    # ISO 8601 format for reliable API date parsing
    now_utc = datetime.now(timezone.utc)
    date_for_api = now_utc.isoformat(timespec='seconds')

    # --- Get Voltage from Wittypi script ---
    voltage = None
    formatted_voltage_for_filename = "unknown_voltage"
    try:
        command = subprocess.run(
            ['bash', '-c', 'source /home/pi/wittypi/utilities.sh && get_input_voltage'],
            capture_output=True,
            text=True,
            check=True
        )
        voltage_str = command.stdout.strip()
        voltage = float(voltage_str)
        # Format voltage for filename (replace '.' with '_')
        formatted_voltage_for_filename = voltage_str.replace('.', '_')
        print(f"Successfully obtained voltage: {voltage} V")

    except FileNotFoundError:
        print(f"Error: 'bash' command not found. {sys.exc_info()[0]}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error running get_input_voltage script: {e}", file=sys.stderr)
        print(f"Stderr:\n{e.stderr}", file=sys.stderr)
    except ValueError:
        print(f"Error converting voltage reading '{voltage_str}' to float. Received unexpected output.", file=sys.stderr)
    except Exception as e:
         print(f"An unexpected error occurred while getting voltage: {e}", file=sys.stderr)
    # ---------------------------------------

    # Construct the full path for the photo file to read
    image_path = f'/home/pi/Agrocam/photo{date_for_filename_part}.png'

    # Define the key used in metadata and filename
    metadata_key = credentials.name # Replace with actual key variable if dynamic

    # Construct the desired filename for the upload, including key, date, and voltage
    upload_filename = f"{metadata_key}_{date_for_filename_part}_{formatted_voltage_for_filename}.png"

    # Populate metadata
    metadata = {
        'key': metadata_key,
        'power_level': voltage, # Use the float voltage (will be None if conversion failed)
        'date_acquisition': date_for_api,
    }

    try:
         # Open the image file and prepare for upload
         with open(image_path, 'rb') as f:
             # 'files' dictionary format: {'field_name': ('filename_for_server', file_object, 'content_type')}
             files = {'photo': (upload_filename, f, 'image/png')}
             data = metadata # Metadata is sent as form fields

             print(f"Sending data via HTTP POST...")

             response = requests.post(url, files=files, data=data)

         if response.status_code == 200:
             print("Photo and metadata sent successfully! Status:", response.status_code)
         else:
             print(f"Error sending data. Status code: {response.status_code}", file=sys.stderr)
             print("Response body:", response.text, file=sys.stderr)

    except FileNotFoundError:
         print(f"Error: Image file not found at {image_path}.", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}", file=sys.stderr)
    except Exception as e:
         print(f"An unexpected error occurred during HTTP request or file handling: {e}", file=sys.stderr)

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


def main():
    setup_wittypi()
    #sleep(30) # waiting for wifi
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
        #envoyer_http(current_date)
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
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])

if __name__ == "__main__":
    main()
