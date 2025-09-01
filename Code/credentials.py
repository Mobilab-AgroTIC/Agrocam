from datetime import time
#url_api = "https://agrocam.agrotic.org/api/upload"
url_api = "https://agrocam.agrotic-dev.org/api/upload"
name= "8_char_id"
# trigger_times=[time(6,30,00),time(8,40,00),time(12,0,0)]
wifi_timeout=30
trigger_times=[time(12,0,0)]
pulsing_interval = 20
white_led_duration=0
recovery_voltage=0
threshold_voltage=70
