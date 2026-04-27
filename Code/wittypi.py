import subprocess
from datetime import datetime, timedelta, timezone, time
import json

CREDENTIALS_FILE = "credentials.json"

with open(CREDENTIALS_FILE, "r") as f:
    credentials = json.load(f) 

def set_startup_time(date, hour, minute, second):
    print("Configuration de l'heure de démarrage...")
    command_set_startup = f"sudo bash -c 'source /home/pi/wittypi/utilities.sh && set_startup_time {date} {hour} {minute} {second}'"

    subprocess.run(['sudo', 'bash', '-c', 'source /home/pi/wittypi/utilities.sh && net_to_system'], capture_output=True, text=True)
    subprocess.run(['sudo', 'bash', '-c', 'source /home/pi/wittypi/utilities.sh && system_to_rtc'], capture_output=True, text=True)
    subprocess.run(['bash', '-c', command_set_startup], capture_output=True, text=True)

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

    times = []
    for t in trigger_times:
        if isinstance(t, str):
            h, m, s = map(int, t.split(":"))
            times.append(time(h, m, s))
        else:
            times.append(t)

    trigger_datetimes_today = [datetime.combine(today, t) for t in times]

    upcoming_triggers = [t for t in trigger_datetimes_today if t > now]

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
        voltage = float(result.stdout.strip())
        print(f"WittyPi détectée, tension d'entrée : {voltage} V")
        return True
    except:
        print("WittyPi non détectée.")
        return False

def setup_wittypi():
    pulsing_interval = credentials["witty"]["pulsing_interval"]
    white_led_duration = credentials["witty"]["white_led_duration"]
    recovery_voltage = credentials["witty"]["recovery_voltage"]
    threshold_voltage = credentials["witty"]["threshold_voltage"]

    cmd_pulse = f"""sudo bash -c 'I2C_BUS=1;  source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_PULSE_INTERVAL {pulsing_interval}'"""
    cmd_led = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_BLINK_LED {white_led_duration}'"""
    cmd_recovery_voltage = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS  $I2C_CONF_RECOVERY_VOLTAGE {recovery_voltage}'"""
    cmd_threshold_voltage = f"""sudo bash -c '  I2C_BUS=1; source /home/pi/wittypi/utilities.sh  && i2c_write $I2C_BUS $I2C_MC_ADDRESS $I2C_CONF_LOW_VOLTAGE {threshold_voltage}'"""

    subprocess.run(cmd_led, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_pulse, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_recovery_voltage, shell=True, capture_output=True, text=True)
    subprocess.run(cmd_threshold_voltage, shell=True, capture_output=True, text=True)

def get_voltage():
    """Récupère la tension d'entrée via le script WittyPi"""
    try:
        command = subprocess.run(
            ['sudo', 'bash', '-c', 'source /home/pi/wittypi/utilities.sh && get_input_voltage'],
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